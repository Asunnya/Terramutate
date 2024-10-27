import difflib
import os
from base_operators import apply_operators



class BaseMutation:
    def __init__(self, mutation_type=None, patterns=None, original_file_path=""):
        """
        Base class for mutations.
        """
        self.mutation_type = mutation_type
        self.patterns = patterns or []
        self.original_file_path = original_file_path
        self.mutated_file_path = None
        self.mutated_content = None
    
    def set_file_path(self, project_path, file_path):
        """
        Set the file path for the mutation.
        """
        self.file_path = os.path.join(project_path, file_path)
    
    def apply_individual_mutation(self):
        """
        Apply the mutation to the file.
        """
        with open(self.original_file_path, 'r') as file:
            self.original_content = file.readlines()
        
        self.mutated_content = apply_operators(self.original_content, self.patterns)

        self.mutated_file_path = F"{self.mutation_type}_mutated.tf"
        with open(self.mutated_file_path, 'w') as file:
            file.writelines(self.mutated_content)
        
        print(f"Mutation {self.mutation_type} applied to {self.original_file_path}")

    def apply_categorized_mutation(self, mutation_list):
        """
        Apply all mutations in the same category (e.g., all provider mutations) in a unique program.
        """
        with open(self.original_file_path, 'r') as file:
            self.original_content = file.readlines()

        all_patterns = [pattern for mutation in mutation_list for pattern in mutation.patterns]
        mutated_content = apply_operators(self.original_content, all_patterns)

        categorized_mutated_file_path = F"{self.mutation_type}_mutated.tf"
        with open(categorized_mutated_file_path, 'w') as file:
            file.writelines(mutated_content)
        
        print(f"Categorized mutation {self.mutation_type} applied to {self.original_file_path}")


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