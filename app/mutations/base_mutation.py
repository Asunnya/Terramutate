import difflib
import os
import shutil
from .base_operators import apply_operators



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
        self.file_path = mutation_dict.get("file_path") or "default_path.tf"  

        if not self.file_path:
            raise ValueError("File path cannot be empty")
        if not self.project_path:
            raise ValueError("Project path cannot be empty")

        self.mutation_type = mutation_dict.get("mutation_type")
        self.patterns = mutation_dict.get("patterns", []) 
        self.project_path = project_path
        self.set_file_path(project_path, self.file_path)
        
    
    def set_file_path(self, project_path, file_path):
        """
        Set the file path for the mutation.
        """
        if not file_path:
            raise ValueError("File path cannot be empty")
        self.file_path = os.path.join(project_path, file_path)
    

    def apply_mutation(self):
        """
        Apply the mutation to the file.
        """
        
        if not self.file_path:
            raise ValueError("Error: File path not set.")
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"Error: File {self.file_path} not found.")

        backup_file_path = f"{self.file_path}.bckp"
        
        
        shutil.copyfile(self.file_path, backup_file_path)
        print(f"Backup created at {backup_file_path}")

        with open(self.file_path, 'r') as file:
            original_content = file.readlines()


        mutated_content = apply_operators(original_content, self.patterns)

        with open(self.file_path, 'w') as file:
                file.writelines(mutated_content)        
        print(f"File {self.file_path} has been modified successfully.")
        return True


    def revert_mutation(self):
        """Reverts the mutation by restoring the original file content."""
        backup_file_path = f"{self.file_path}.bckp"
        if not os.path.exists(backup_file_path):
            raise FileNotFoundError(f"Error: Backup file {backup_file_path} not found.")

        shutil.move(backup_file_path, self.file_path)
        print(f"File {self.file_path} has been restored from backup.")
        return True



    def show_diff(self):
        """Shows the diff between the original and the mutated file."""
        backup_file_path = f"{self.file_path}.bckp"

        if not os.path.exists(backup_file_path):
            raise FileNotFoundError(f"Error: Backup file {backup_file_path} not found.")

        with open(backup_file_path, 'r') as backup, open(self.file_path, 'r') as current:
            diff = difflib.unified_diff(
                backup.readlines(),
                current.readlines(),
                fromfile=f"{self.file_path}.bckp",
                tofile=self.file_path
            )
            print("\n".join(diff))
