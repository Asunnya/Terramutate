import json
import os
import shutil
import subprocess
from .mutations.base_mutation import BaseMutation
from typing import List, Optional, Set, Dict


class MutationFramework:
    def __init__(self, original_path, config_json, config_yaml, mutation_mode="individual"):
        
        """
        Init framework
        Parameters:
        - original_path: path to the original terraform project
        - config_json: path to the config file
        - mutation_mode: mutation mode to be applied (individual or combined)
            if individual, each mutation = program
            if combined, all mutations from a category = program
        """  
        self.original_path = original_path
        self.config_json = config_json
        self.config_yaml = config_yaml
        # Place the sandbox copy alongside the application code (project root)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.copy_path = os.path.join(project_root, "terraform_mutated_copy")
        self.mutation_results = []
        # Determine mutation mode: argument has precedence, else config file
        if mutation_mode != "individual" or "mutation_mode" not in config_yaml:
            self.mutation_mode = mutation_mode
        else:
            self.mutation_mode = config_yaml.get("mutation_mode", "individual")
        
        if os.path.exists(self.copy_path):
            shutil.rmtree(self.copy_path)
        
        # -------------------------------------------------------------
        # Optional filtering of categories / mutation types.
        # Priority: explicit keys in YAML config, else hard-coded defaults
        # in app.config.selection module. If both unavailable, include all.
        # -------------------------------------------------------------
        try:
            from app.config import selection as _sel
        except ImportError:  # fallback when module absent (e.g., legacy tests)
            class _SelFallback:
                INCLUDE_CATEGORIES = None
                INCLUDE_MUTATION_TYPES = None
            _sel = _SelFallback()

        self.include_categories: Optional[List[str]] = (
            config_yaml.get("include_categories") if isinstance(config_yaml, dict) else None
        ) or getattr(_sel, "INCLUDE_CATEGORIES", None)

        self.include_mut_types: Optional[List[str]] = (
            config_yaml.get("include_mutation_types") if isinstance(config_yaml, dict) else None
        ) or getattr(_sel, "INCLUDE_MUTATION_TYPES", None)
    
    
    # I DONT KNOW WHY BUT SOMETHINGS COPY EVERYTHING FROM terraform_tests
    def check_copy_folder(self, copy_path):
        """
        Ensures that the copy folder only contains required files and subdirectories.
        Removes any extraneous files or folders.

        Parameters:
        - copy_path: path to the copy folder
        """
        unwanted_items = ["terraform-mutation", ".vscode", "terraform_tests.code-workspace"]
        
        for item in unwanted_items:
            item_path = os.path.join(copy_path, item)
            if os.path.exists(item_path):
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                    print(f"Removed unwanted folder: {item_path}")
                else:
                    os.remove(item_path)
                    print(f"Removed unwanted file: {item_path}")


    def create_copy(self, mutations: list | dict | None = None):
        """Create a *copy-on-write* workspace of the original infrastructure.

        When *mutations* is provided (list in "individual" mode, or dict
        category→list in "categorized" mode) the method performs a space-
        efficient clone:

        1. Duplicates every file in *original_path* using **hard-links**
           via ``shutil.copytree(..., copy_function=os.link)`` – cheap in time
           and disk.
        2. For every *file_path* that will be mutated, it **replaces the
           hard-link by a real copy** of the file, ensuring changes don't leak
           back to the original source tree.

        If *mutations* is *None* the previous behaviour (full physical copy)
        is preserved for backwards-compatibility (e.g., unit tests that call
        ``create_copy()`` directly).
        """

        infrastructure_folder = self.config_json["terraform_paths"]["infrastructure_folder"].rstrip("/\\")
        infrastructure_name = os.path.basename(infrastructure_folder)
        infrastructure_dst = os.path.join(self.copy_path, infrastructure_name)

        if "terraform_mutated_copy" not in self.copy_path:
            raise ValueError("Invalid copy path. Expected 'terraform_mutated_copy' in the path.")

        # Remove any previous copy to guarantee a clean workspace
        if os.path.exists(infrastructure_dst):
            shutil.rmtree(infrastructure_dst)

        if not os.path.exists(self.original_path):
            raise FileNotFoundError(f"The infrastructure folder {self.original_path} does not exist")

        # Decide strategy based on whether we know which files will be mutated.
        if mutations is None:
            # Legacy – physical copy of every file
            shutil.copytree(self.original_path, infrastructure_dst)
        else:
            # 1) Attempt a cheap clone using hard-links. When the source and
            # destination reside on different devices (common when tmpfs ←→
            # regular FS) the operation fails with *Invalid cross-device link*
            # (errno 18). In such case we transparently fall back to a regular
            # byte-for-byte copy (``shutil.copy2``), which is slower but
            # portable.

            try:
                shutil.copytree(
                    self.original_path,
                    infrastructure_dst,
                    copy_function=os.link,
                    ignore=shutil.ignore_patterns('terraform_mutated_copy'),
                )
            except shutil.Error as err:
                # Detect cross-device link errors inside aggregated tuples.
                if any(
                    "Invalid cross-device link" in tup[2]
                    for tup in err.args[0]
                ):
                    # Clean up partial dst and retry with standard copy.
                    if os.path.exists(infrastructure_dst):
                        shutil.rmtree(infrastructure_dst)
                    shutil.copytree(
                        self.original_path,
                        infrastructure_dst,
                        copy_function=shutil.copy2,
                        ignore=shutil.ignore_patterns('terraform_mutated_copy'),
                    )
                else:
                    raise

            # 2) Build a *set* with relative paths to files that will be mutated
            mutated_rel_paths: Set[str] = set()

            if isinstance(mutations, dict):  # categorized ➜ {category: [dict,…]}
                mutation_iterable = (m for lst in mutations.values() for m in lst)
            else:  # individual ➜ list[dict]
                mutation_iterable = mutations

            for m in mutation_iterable:
                rel_path = m.get("file_path")
                if rel_path:
                    mutated_rel_paths.add(rel_path.lstrip("/\\"))

            # 3) Break the hard-links for those files, replacing by real copies
            for rel_path in mutated_rel_paths:
                src_file = os.path.join(self.original_path, rel_path)
                # Attempt also infra subfolder if path missing
                if not os.path.exists(src_file):
                    src_file = os.path.join(self.original_path, infrastructure_folder, rel_path)
                if not os.path.exists(src_file):
                    continue  # skip missing files
                dst_file = os.path.join(infrastructure_dst, rel_path)

                # Ensure parent directory exists in destination tree
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)

                # Remove the hard-link (or symlink) first to avoid copying over itself
                if os.path.exists(dst_file):
                    os.remove(dst_file)

                shutil.copy2(src_file, dst_file)

        # ------------------------------------------------------------------
        # When the *original_path* already contains a top-level directory with
        # the same name of ``infrastructure_folder`` (the typical case) we
        # end up with a nested structure like:
        #     terraform_mutated_copy/infrastructure/infrastructure/…
        # Move the inner contents one level up and discard the redundant
        # directory so callers can reference files using
        # <copy_path>/infrastructure/<file.tf> as expected by the unit tests.
        # ------------------------------------------------------------------

        nested_path = os.path.join(infrastructure_dst, infrastructure_name)
        if os.path.isdir(nested_path):
            for entry in os.listdir(nested_path):
                src_entry = os.path.join(nested_path, entry)
                dst_entry = os.path.join(infrastructure_dst, entry)
                if os.path.exists(dst_entry):
                    # Prefer the already-present file (may have been copied
                    # with broken hard-link above). Remove duplicate.
                    if os.path.isdir(src_entry):
                        shutil.rmtree(src_entry)
                    else:
                        os.remove(src_entry)
                    continue
                shutil.move(src_entry, dst_entry)
            try:
                os.rmdir(nested_path)
            except OSError:
                pass  # ignore if not empty for any reason

        # Final tidy-up: ensure no unwanted artefacts were copied
        self.check_copy_folder(self.copy_path)

        print(f"Created copy-on-write project in {self.copy_path}")
        return infrastructure_dst 

    def revert_mutation(self, mutation):
        """Revert the mutation applied"""
        print(f"Reverting mutation {mutation.__class__.__name__}")
        mutation.revert_mutation()



    def load_mutation(self):
        """Initialize and return a list of mutations to be applied"""
        if self.mutation_mode == "individual":
            list_mutations: List[dict] = []
            for mutation in self.config_yaml["mutations"]:
                # Apply selection filters, if any --------------------------------
                if self.include_categories and mutation.get("category") not in self.include_categories:
                    continue
                if self.include_mut_types and mutation.get("mutation_type") not in self.include_mut_types:
                    continue
                mutation_dict = {
                    "id": mutation.get("id"),
                    "category": mutation.get("category"),
                    "file_type": mutation.get("file_type"),
                    "file_path": mutation.get("file_path"),
                    "mutation_type": mutation.get("mutation_type"),
                    "patterns": mutation.get("patterns")
                }
                list_mutations.append(mutation_dict)
            return list_mutations
        elif self.mutation_mode == "categorized":
            categories: Dict[str, List[dict]] = {}
            for mutation in self.config_yaml["mutations"]:
                # Selection filters ------------------------------------------------
                if self.include_categories and mutation.get("category") not in self.include_categories:
                    continue
                if self.include_mut_types and mutation.get("mutation_type") not in self.include_mut_types:
                    continue
                category = mutation.get("category")
                if category not in categories:
                    categories[category] = []
                mutation_dict = {
                    "id": mutation.get("id"),
                    "category": category,
                    "file_type": mutation.get("file_type"),
                    "file_path": mutation.get("file_path"),
                    "mutation_type": mutation.get("mutation_type"),
                    "patterns": mutation.get("patterns")
                }
                categories[category].append(mutation_dict)
            # Remove empty categories after filtering
            categories = {k: v for k, v in categories.items() if v}
            return [categories] if categories else []
        else:
            raise ValueError(f"Modo de mutação desconhecido: '{self.mutation_mode}'")
    def apply_mutation(self, mutation_dict, project_path, only_idx=None):
        """Instantiate ``BaseMutation`` and apply it.

        Parameters
        ----------
        mutation_dict : dict
            Metadata for the mutation (copied from YAML config).
        project_path : str
            Root path of the terraform project copy where the mutation will be
            applied.
        only_idx : int | None, optional
            When provided, only the *idx*-th occurrence will be mutated.
        """

        mutation_instance = BaseMutation(mutation_dict, project_path)
        mutation_instance.apply_mutation(only_idx=only_idx)
        return mutation_instance
    def test_mutation(self, mutation_dict, category ,categorized=False):
        """
        Run the tests for the mutated files.
        Parameters:
        - mutation_dict: mutation to be tested
        - categorized: if the mutation is categorized
        """

        if not categorized:


            if not mutation_dict['id']:

                print(
                    mutation_dict['id']
                )
                raise ValueError("Mutation ID not found in mutation_dict, Did u send more than one mutate?")


        # Build the path to the Go tests directory inside the *copied* project.
        # The structure of the workspace after `create_copy` is:
        #   <copy_path>/infrastructure/          ← full clone of the original project (iac-tests)
        #     └── infrastructure/               ← original infrastructure folder
        #         └── test/                     ← Go tests live here

        infra_folder_cfg = self.config_json["terraform_paths"].get("infrastructure_folder", "infrastructure/").rstrip("/\\")
        test_folder_cfg = self.config_json["terraform_paths"].get("test_folder", "test/").rstrip("/\\")

        # After `create_copy` we intentionally flatten the directory so that
        # all Terraform files (and the Go `test/` folder) live directly under
        # `<copy_path>/infrastructure/`. Therefore there is **no** nested
        # `<copy_path>/infrastructure/infrastructure/…` anymore.  Build the
        # test directory path accordingly.

        test_dir = os.path.join(self.copy_path, "infrastructure", test_folder_cfg)

        # -------------------------------------------------------------
        # Verbose information about where the Go tests will run so users
        # can confirm execution happens inside the *copy* workspace.
        # E.g.: "rodando tests at program 0  mutant folder <path> after applied idx0 ..."
        # -------------------------------------------------------------
        program_number = len(self.mutation_results) + 1  # next program index (1-based)
        mutant_label = (
            f"{mutation_dict.get('id', 'N/A')}" if not categorized else f"category_{category}"
        )
        print(
            f"\n[Terramutate] running tests at program {program_number}  "
            f"mutant folder {test_dir}  after applied {mutant_label} ...\n"
        )

        os.makedirs(test_dir, exist_ok=True)
        output_file_name = (
            f"{category}_output.txt" if categorized else f"{mutation_dict['id']}_output.txt"
        )
        output_file_path = os.path.join(test_dir, output_file_name)


        with open(output_file_path, 'w') as output_file:
            # If diff information is present, write it first
            if not categorized and mutation_dict.get("_diff"):
                output_file.write("===== DIFF =====\n")
                output_file.write(mutation_dict["_diff"] + "\n")
                output_file.write("===== END DIFF =====\n\n")
            try:
                subprocess.run(["go", "test", "-v"],
                    cwd = test_dir,
                    stdout=output_file,  
                    stderr=output_file, 
                    check=True
                )
                success = True
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                success = False
                
        output = f"Test: {success} saved output file: {output_file_path}"

        # Store mutation result details, including diff when available
        self.mutation_results.append({
            "mutation_dict": mutation_dict["id"] if not categorized else category,
            "category": mutation_dict["category"] if not categorized else category,
            "success": success,
            "output": output,
            # Diff is only present for non-categorized mutations
            "diff": mutation_dict.get("_diff") if not categorized else None,
        })



    def run(self):
        """Main method to execute mutations based on the selected mode."""

        mutations = self.load_mutation()
        # For categorized mode we need the inner dict to properly list
        # individual mutation dicts when copying files.
        mutations_for_copy = mutations[0] if self.mutation_mode == "categorized" else mutations
        project_path = self.create_copy(mutations_for_copy)
        if self.mutation_mode == "categorized":
           # The goal here is: Apply more than one mutation of the same category
           # If have 2 POR, apply both, test both, revert both get the results of both
           categories = mutations_for_copy
           for category, mutation_dicts in categories.items():
               print(f"Category: {category}")
               for mutation_dict in mutation_dicts:
                   self.apply_mutation(mutation_dict, project_path)
               self.test_mutation(mutation_dicts, category, True)
        else:  
            # The goal here is: Apply one mutation, test, revert, get the results
            print(mutations)
            for mutation_dict in mutations:
                print(f"Mutation: {mutation_dict['category']}")
                category = mutation_dict["category"]

                # Prepare mutation instance and count occurrences
                mutation_instance = BaseMutation(mutation_dict, project_path)
                total_occ = mutation_instance.find_occurrences()

                if total_occ == 0:
                    print(
                        f"[WARN] Mutation {mutation_dict['id']} has no occurrences – skipping."
                    )
                    continue

                for idx in range(total_occ):
                    # Apply single-occurrence mutation
                    diff_text = mutation_instance.apply_mutation(only_idx=idx)

                    # Clone original dict to avoid side-effects across loop
                    idx_mut_dict = mutation_dict.copy()
                    idx_mut_dict["id"] = f"{mutation_dict['id']}__idx{idx}"
                    if isinstance(diff_text, str):
                        idx_mut_dict["_diff"] = diff_text

                    self.test_mutation(idx_mut_dict, category, False)

                    # Restore original file(s) so next mutant starts from pristine code
                    mutation_instance.revert_mutation()

        self.show_results()

    def show_results(self):
        """Displays the results of all mutations."""

        report_lines = []
        report_lines.append("==================== Mutation Results ====================\n")
        for i, result in enumerate(self.mutation_results, start=1):
            # Mark failed mutants as "Failed (killed)" to align with mutation testing jargon
            status = "Success (alive)" if result["success"] else "Failed (killed)"

            line_id = f"[{i}] Mutant Program: {result['mutation_dict']} - Status: {status}"
            line_output = f"    Output: {result['output']}"
            report_lines.extend([line_id, line_output])

            # Append diff information when available
            if result.get("diff"):
                report_lines.append("    ----- DIFF START -----")
                # Ensure diff lines are indented for readability
                for diff_line in result["diff"].splitlines():
                    report_lines.append(f"    {diff_line}")
                report_lines.append("    ----- DIFF END -----")
        report_lines.append("---------------------------------------------------------")
        report_lines.append(f"Total mutant programs generated & tested: {len(self.mutation_results)}")
        report_lines.append("Each program contains exactly 1 mutation, forming N mutant programs.")
        report_lines.append("=========================================================\n")

        # Print to console
        for ln in report_lines:
            print(ln)

        # Also write to summary file at the project root (alongside `app/`)
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        summary_path = os.path.join(project_root, "mutation_results_summary.txt")
        try:
            with open(summary_path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(report_lines))
            print(f"[INFO] Summary saved to {summary_path}")
        except IOError as e:
            print(f"[WARN] Could not write summary file: {e}")
       
