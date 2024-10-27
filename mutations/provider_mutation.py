from mutations.base_mutation import BaseMutation
import re

class ProviderMutation(BaseMutation):
    def __init__(self, mutation_type=None, patterns=None, original_file_path="provider.tf"):
        super().__init__(mutation_type, patterns, original_file_path=original_file_path)

    def apply_mutation(self):
        """ Apply individual mutation to the file """

        self.set_file_path(project_path=".", file_path=self.file_path)

        self.apply_individual_mutation()

        print("==== DIFF BETWEEN ORIGINAL AND MUTATED FILE ====")
        with open(self.mutated_file_path, 'r') as file:
            mutated_content = file.readlines()
        self.show_diff(mutated_content)