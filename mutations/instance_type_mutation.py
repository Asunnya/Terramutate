import os 
import re
from mutations.base_mutation import BaseMutation


class InstanceTypeMutation(BaseMutation):
    def apply_mutation(self):
        mutated_content = []

        with open(self.file_path, 'r') as file:
            self.original_content = file.readlines()
        
        # for line in self.original_content:
        #     mutated_content.append(re.sub(r't2\.micro', 't2.large', line))

        mutated_content = [re.sub(r't2\\.micro', 't2.large', line) for line in self.original_content]


        with open(self.file_path, 'w') as file:
            file.writelines(mutated_content)

        print(f"Mutation {self.__class__.__name__} applied to {self.file_path}")