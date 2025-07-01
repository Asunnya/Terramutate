import difflib
import os
import shutil
from .base_operators import apply_operators
import re



class BaseMutation:
    def __init__(self, mutation_dict, project_path="."):
        """
        Initializes a mutation instance with configuration details from mutation_dict.
        
        Args:
            mutation_dict (dict): Dictionary containing mutation configuration details.
            project_path (str): Path to the project where the mutation will be applied.
        """

       
        

        self.id = mutation_dict.get("id")
        self.category = mutation_dict.get("category")
        self.file_type = mutation_dict.get("file_type")
        self.project_path = project_path
        self.file_path = mutation_dict.get("file_path")  # pode ser None
        self.mutation_type = mutation_dict.get("mutation_type")
        self.patterns = mutation_dict.get("patterns", []) 
        self.project_path = project_path
        if self.file_path:
            self.set_file_path(project_path, self.file_path)
        
    
    def set_file_path(self, project_path, file_path):
        """
        Set the file path for the mutation.
        """
        if not file_path:
            raise ValueError("File path cannot be empty")
        self.file_path = os.path.join(project_path, file_path)
    

    def find_occurrences(self):
        """Count **all** occurrences of every mutation *pattern* in the target
        file. The count is cached in ``self._total_occurrences`` and returned.
        """

        if hasattr(self, "_total_occurrences"):
            return self._total_occurrences  # cached value

        def _count_in_file(path: str) -> int:
            cnt = 0
            with open(path, "r") as fh:
                for ln in fh:
                    for m in self.patterns:
                        cnt += len(list(re.finditer(m["pattern"], ln)))
            return cnt

        total = 0
        if self.file_path:  # único arquivo
            total = _count_in_file(self.file_path)
        else:  # varrer todos .tf na pasta do projeto
            for root, _dirs, files in os.walk(self.project_path):
                for fn in files:
                    if fn.endswith(".tf"):
                        total += _count_in_file(os.path.join(root, fn))

        self._total_occurrences = total
        return total

    def apply_mutation(self, only_idx: int | None = None):
        """Apply the mutation to the file.

        Parameters
        ----------
        only_idx : int | None, optional
            When provided, *only* the occurrence with global index ``only_idx``
            is mutated (granular mode). When ``None`` (default) the behaviour
            is identical to the legacy implementation, mutating **all**
            occurrences at once.
        """

        target_files: list[str] = []
        if self.file_path:
            target_files.append(self.file_path)
        else:
            for root, _d, files in os.walk(self.project_path):
                target_files += [os.path.join(root, f) for f in files if f.endswith(".tf")]

        global_occ_idx = 0
        mutated_any = False
        for path in target_files:
            if not os.path.exists(path):
                continue

            # ---------------------------------------------------------
            # Copy-on-write safeguard
            # ---------------------------------------------------------
            # When the project tree is cloned using hard-links (via
            # ``shutil.copytree(..., copy_function=os.link)``) the files in
            # *path* may share the same inode with their counterparts in the
            # original source tree.  Mutating such a file would therefore
            # *also* modify the original infrastructure – exactly what we
            # want to avoid.

            # ``os.stat(path).st_nlink`` reports the number of hard-links that
            # point to the same inode.  A value greater than **1** means the
            # file is still linked elsewhere, so we must break the link prior
            # to any change.

            try:
                if os.stat(path).st_nlink > 1:
                    tmp_clone = f"{path}.__cow__"
                    shutil.copy2(path, tmp_clone)
                    os.replace(tmp_clone, path)  # atomic swap ⇒ new inode
            except FileNotFoundError:
                # The file may disappear between the stat and copy (unlikely)
                continue

            # Having ensured the file is now independent, create a pristine
            # backup (*only once* per file).
            backup_path = f"{path}.bckp"
            if not os.path.exists(backup_path):
                shutil.copyfile(path, backup_path)
                print(f"Backup created at {backup_path}")

            with open(path, "r") as f:
                content = f.readlines()

            # Decide selective replacement considering cumulative index
            local_only_idx = None
            if only_idx is not None:
                local_occurrences = sum(len(list(re.finditer(m["pattern"], "".join(content)))) for m in self.patterns)
                if global_occ_idx + local_occurrences <= only_idx:
                    global_occ_idx += local_occurrences
                    continue  # occurrence lies further ahead
                local_only_idx = only_idx - global_occ_idx

            new_content = apply_operators(content, self.patterns, only_idx=local_only_idx)

            # If any change will be written, mark that we actually mutated a file
            if new_content != content:
                mutated_any = True  # flag set – at least one replacement happened

            with open(path, "w+") as f:
                f.writelines(new_content)

            if only_idx is not None and local_only_idx is not None:
                break  # done after replacing specific occurrence

        # ---------------------------------------------------------
        # Return / logging
        # ---------------------------------------------------------
        # If nothing was actually mutated (e.g., file did not exist, pattern
        # not found, etc.) we simply return **True** to signal a graceful
        # no-op – this behaviour is relied upon by unit tests such as
        # `test_mutation_failure`.

        if not mutated_any:
            print("No occurrences found – mutation skipped.")
            return None

        # When at least one replacement happened we compute and return the
        # unified diff so callers (e.g., the framework) can record it.
        action = (
            f"single occurrence idx={only_idx}" if only_idx is not None else "all occurrences"
        )
        diff_text = self.show_diff(return_text=True)
        print(f"Mutation {self.mutation_type} applied ({action}).")
        return diff_text

    def revert_mutation(self):
        """Reverts the mutation by restoring the original file content."""
        if self.file_path:
            backup_file_path = f"{self.file_path}.bckp"
            if os.path.exists(backup_file_path):
                shutil.move(backup_file_path, self.file_path)
        else:
            for root, _d, files in os.walk(self.project_path):
                for fn in files:
                    if fn.endswith(".bckp"):
                        original = os.path.join(root, fn[:-5])
                        shutil.move(os.path.join(root, fn), original)
        print("Restored files from backup.")
        return True

    def show_diff(self, return_text: bool = False):
        """Return an unified diff between backup and mutated file.

        When *return_text* is True the diff is returned as a single string;
        otherwise it is printed to stdout (legacy behaviour).
        """
        # -------------------------------------------------------------
        # Single-file mutation (self.file_path defined)
        # -------------------------------------------------------------
        if self.file_path:
            backup_file_path = f"{self.file_path}.bckp"

            if not os.path.exists(backup_file_path):
                raise FileNotFoundError(
                    f"Error: Backup file {backup_file_path} not found."
                )

            with open(backup_file_path, "r") as backup, open(self.file_path, "r") as current:
                diff_lines = list(
                    difflib.unified_diff(
                        backup.readlines(),
                        current.readlines(),
                        fromfile=f"{self.file_path}.bckp",
                        tofile=self.file_path,
                    )
                )

            diff_text = "".join(diff_lines)

            if return_text:
                return diff_text

            print(diff_text)
            return None

        # -------------------------------------------------------------
        # Multi-file mutation (self.file_path is None)
        # -------------------------------------------------------------
        aggregated_diffs: list[str] = []

        for root, _d, files in os.walk(self.project_path):
            for fn in files:
                if not fn.endswith(".bckp"):
                    continue

                backup_file_path = os.path.join(root, fn)
                original_file_path = backup_file_path[:-5]  # strip '.bckp'

                if not os.path.exists(original_file_path):
                    continue  # original file removed (unlikely)

                with open(backup_file_path, "r") as backup, open(
                    original_file_path, "r"
                ) as current:
                    diff_lines = list(
                        difflib.unified_diff(
                            backup.readlines(),
                            current.readlines(),
                            fromfile=backup_file_path,
                            tofile=original_file_path,
                        )
                    )

                if diff_lines:
                    aggregated_diffs.append("".join(diff_lines))

        diff_text = "\n".join(aggregated_diffs)

        if return_text:
            return diff_text

        print(diff_text)
        return None

    def generate_granular_mutants(self):
        """Generator that yields *occurrence indices* and applies/reverts the
        mutation for each one, guaranteeing the file is restored after the
        yield completes.
        """

        total = self.find_occurrences()
        for idx in range(total):
            self.apply_mutation(only_idx=idx)
            yield idx  # caller can run tests here
            self.revert_mutation()
