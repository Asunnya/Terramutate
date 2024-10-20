import difflib
import os



class BaseMutation:
    def __init__(self):
        """
        Base class for mutations.
        """
        self.original_content = []
    
    def set_file_path(self, project_path, file_path):
        """
        Set the file path for the mutation.
        """
        self.file_path = os.path.join(project_path, file_path)
       
    def apply_mutation(self):
        """Abstract method to apply the mutation all subclasses should implement this method"""
        raise NotImplementedError("Subclasses should implement this method")

    def revert_mutation(self):
        """
        Reverte a mutação ao restaurar o conteúdo original do arquivo.
        """
        with open(self.file_path, 'w') as file:
            file.writelines(self.original_content)
        print(f"Mutação revertida no arquivo: {self.file_path}")

    def show_diff(self, new_content):
        """
        show the diff between the file original and the mutate file.
        """
        diff = difflib.unified_diff(
            self.original_content,
            new_content,
            fromfile='Original',
            tofile='Modificado',
            lineterm=''
        )
        for line in diff:
            print(line)