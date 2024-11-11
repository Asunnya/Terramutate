import json
import os
import shutil
import subprocess
from .mutations.base_mutation import BaseMutation


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
        self.copy_path = os.path.join(original_path, "terraform_mutated_copy")
        self.mutation_results = []
        self.mutation_mode = mutation_mode
        
        if os.path.exists(self.copy_path):
            shutil.rmtree(self.copy_path)
    
    
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


    def create_copy(self):
        """
        Create a copy of the original project
        """
        infrastructure_folder = self.config_json['terraform_paths']['infrastructure_folder']
        infrastructure_name = os.path.basename(infrastructure_folder)
        infrastructure_dst = os.path.join(self.copy_path, infrastructure_name)

        if "terraform_mutated_copy" not in self.copy_path:
            raise ValueError("Invalid copy path. Expected 'terraform_mutated_copy' in the path.")

        # Remove existing copy of the project

        if os.path.exists(infrastructure_dst):
            shutil.rmtree(infrastructure_dst)
            print(f"Removed existing copy of the project in {infrastructure_dst}")

        # Infra folder must exist

        if not os.path.exists(self.original_path):
            raise Exception(f"The infrastructure folder {self.original_path} does not exist")

        # Copy the project
        shutil.copytree(self.original_path, infrastructure_dst)
        self.check_copy_folder(self.copy_path)

        print(f"Created copy of the project in {self.copy_path}")
        return infrastructure_dst 

    def revert_mutation(self, mutation):
        """Revert the mutation applied"""
        print(f"Reverting mutation {mutation.__class__.__name__}")
        mutation.revert_mutation()



    def load_mutation(self):
        """Inicialize and returns a list of mutations to be applied"""

        if self.mutation_mode == "individual":
            # Use each mutation as a program, get all mutations from the config yaml file, return a list of id 
            list_mutations = []

            for mutation in self.config_yaml["mutations"]:
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
            # Cria um dicionário para agrupar as mutações por categoria
            categories = {cat: [] for cat in self.config_yaml.get("mutation_categories", [])}

            # Itera sobre as mutações na configuração YAML e agrupa por categoria
            for mutation in self.config_yaml["mutations"]:
                category = mutation.get("category")
                if category in categories:
                    mutation_dict = {
                        "id": mutation.get("id"),
                        "category": mutation.get("category"),
                        "file_type": mutation.get("file_type"),
                        "file_path": mutation.get("file_path"),
                        "mutation_type": mutation.get("mutation_type"),
                        "patterns": mutation.get("patterns")
                    }
                    categories[category].append(mutation_dict)

            # Converte cada categoria e suas mutações em um dicionário separado na lista final
            categorized_mutations = [{cat: mutations} for cat, mutations in categories.items() if mutations]

            return categorized_mutations

        else:
            raise ValueError(f"Modo de mutação desconhecido: '{self.mutation_mode}'")
    def apply_mutation(self, mutation_dict, project_path):
        """
        Call Base Mutation to apply the mutation

        Parameters:
        - mutation_dict: mutation to be applied
        - project_path: path to the project
        """
        
        Mutation = BaseMutation(mutation_dict, project_path)
        Mutation.apply_mutation()

       
    def test_mutation(self, mutation_dict, category ,categorized=False):
        """
        Run the tests for the mutated files.
        Parameters:
        - mutation_dict: mutation to be tested
        - categorized: if the mutation is categorized
        """

        if not categorized:
            if not mutation_dict.id:
                raise ValueError("Mutation ID not found in mutation_dict, Did u send more than one mutate?")

        test_dir = os.path.join(self.copy_path, "iac-tests/infrastructure/test")
        output_file_name = f"{category}_output.txt" if categorized else f"{mutation_dict.id}_output.txt"
        output_file_path = os.path.join(test_dir, output_file_name)

        with open(output_file_path, 'w') as output_file:
            try:
                subprocess.run(["go", "test", "-v"],
                    cwd = test_dir,
                    stdout=output_file,  
                    stderr=output_file, 
                    check=True
                )
                success = True
            except subprocess.CalledProcessError as e:
                success = False
                
        output = f"Test: {success} saved output file: {output_file_path}"

        self.mutation_results.append({
            "mutation_dict": mutation_dict.id if not categorized else category,
            "category": mutation_dict.category if not categorized else category,
            "success": success,
            "output": output
        })



    def run(self):
        """Main method to execute mutations based on the selected mode."""

        project_path = self.create_copy()
        mutations = self.load_mutation()
        if self.mutation_mode == "categorized":
           # The goal here is: Apply more than one mutation of the same category
           # If have 2 POR, apply both, test both, revert both get the results of both
           for category, mutation_dicts in mutations.items():
               print(f"Category: {category}")
               for mutation_dict in mutation_dicts:
                   self.apply_mutation(mutation_dict, project_path)
               self.test_mutation(mutation_dicts, category, True)
               #self.revert_mutations() # Clean all mutations, different from revert_mutation 
        else:  
            # The goal here is: Apply one mutation, test, revert, get the results
            for mutation_dict in mutations:
                self.apply_mutation(mutation_dict, project_path)
                self.test_mutation(mutation_dict, category, False)
                self.revert_mutation(mutation_dict, category)

        self.show_results()

    def show_results(self):
        """Displays the results of all mutations."""

        print("Mutation Results:")
        for result in self.mutation_results:
            status = "Success" if result["success"] else "Failed"
            print(f"Mutation ID: {result['mutation_dict']} - Status: {status}")
            print(f"Output file: {result['output']}")
       
