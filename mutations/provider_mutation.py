import os
from mutations.base_mutation import BaseMutation
import re

class ProviderMutation(BaseMutation):
    def apply_mutation(self):
      
        mutated_content = []

        with open(self.file_path, 'r') as file:
            self.original_content = file.readlines()
        
        # for line in self.original_content:
        #     mutated_content.append(re.sub(r'aws', 'google', line))

        mutated_content = [re.sub(r'provider "aws"', 'provider "google"', line) for line in self.original_content]



        with open(self.file_path, 'w') as file:
            file.writelines(mutated_content)

        print(f"Mutation {self.__class__.__name__} applied to {self.file_path}")

        print("=== Diff file mutated ===")
        self.show_diff(mutated_content)