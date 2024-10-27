import os 
import re
from mutations.base_mutation import BaseMutation


class InstanceTypeMutation(BaseMutation):
    def __init__(self, mutation_type=None, patterns=None, original_file_path="instance.tf"):
        super().__init__(mutation_type, patterns, original_file_path=original_file_path)
   
    def apply_mutation_old(self):
        mutated_content = []

        with open(self.file_path, 'r') as file:
            self.original_content = file.readlines()

        for line in self.original_content:
            # Mutação de tipo de instância
            line = re.sub(r't2\.micro', 't2.large', line)
            # Mutação de memória
            line = re.sub(r'memory_size = \d+', 'memory_size = 1024', line)
            # Mutação de timeout
            line = re.sub(r'timeout = \d+', 'timeout = 60', line)
            # Mutação do runtime
            line = re.sub(r'runtime = "nodejs12\.x"', 'runtime = "python3.8"', line)
            mutated_content.append(line)


        with open(self.file_path, 'w') as file:
            file.writelines(mutated_content)

        print(f"Mutation {self.__class__.__name__} applied to {self.file_path}")

        print("=== Diff file mutated ===")
        self.show_diff(mutated_content)

    def apply_mutation(self):
        """ Apply individual mutation to the file """

        self.set_file_path(project_path=".", file_path=self.file_path)

        self.apply_individual_mutation()

        print("==== DIFF BETWEEN ORIGINAL AND MUTATED FILE ====")
        with open(self.mutated_file_path, 'r') as file:
            mutated_content = file.readlines()
        self.show_diff(mutated_content)