import json
import os
import shutil
import subprocess
from mutations.instance_type_mutation import InstanceTypeMutation
from mutations.provider_mutation import ProviderMutation

class Config:
    def __init__(self, config_file_path):
        with open(config_file_path, 'r') as config_file:
            self.config = json.load(config_file)

        self.root_folder = self.config['terraform_paths']['root_folder']
        self.infrastructure_folder = os.path.join(self.root_folder, self.config['terraform_paths']['infrastructure_folder'])
        self.test_folder = os.path.join(self.root_folder, self.config['terraform_paths']['test_folder'])

        self.instance_file = self.config['file_paths']['instance_file']
        self.provider_file = self.config['file_paths']['provider_file']


    def get_infrastucture_path(self):
        """Returns the path to the infrastructure folder"""
        return self.infrastructure_folder
    

    def get_test_folder_path(self, project_path):
        """
        Returns the path to the test folder
        Parameters:
        - project_path: path to the project
        """
        return os.path.join(project_path, self.test_folder)

    
    def get_instance_file_path(self):
        """Returns the path to the instance file"""
        return os.path.join(self.infrastructure_folder, self.instance_file)

    def get_provider_file_path(self):
        """Returns the path to the provider file"""
        return os.path.join(self.infrastructure_folder, self.provider_file)

class MutationFramework:
    def __init__(self, original_terraform_path, config_file_path):
        
        """
        Init framework
        Parameters:
        - original_terraform_path: path to the original terraform project
        - config_file_path: path to the config file
        """
        
        self.config = Config(config_file_path)
        self.original_terraform_path = original_terraform_path
        self.copy_path = os.path.join(original_terraform_path, "terraform_mutated_copy")
        self.results = []

        if os.path.exists(self.copy_path):
            shutil.rmtree(self.copy_path)
    
    
    # I DONT KNOW WHY BUT SOMETHINGS COPY EVERYTHING FROM terraform_tests
    def check_copy_folder(self, copy_path):
        #verify if this files are in the copy path

        if os.path.exists(copy_path):
            #verify if the folder terraform-mutation is in the copy path
            if os.path.exists("terraform-mutation/"):
                print("BUG: The folder terraform-mutation is in the copy path")
                shutil.rmtree("terraform-mutation/")

                #verify if the folder .vscode is in the copy path
            if os.path.exists(".vscode/"):
                print("BUG: The folder .vscode is in the copy path")
                shutil.rmtree(".vscode/")
            
            #verify if the file terraform_tests.code-workspace is in the copy path
            if os.path.exists("terraform_tests.code-workspace"):
                print("BUG: The file terraform_tests.code-workspace is in the copy path")
                os.remove("terraform_tests.code-workspace")
           


    def create_copy(self):
        infrastructure_name = os.path.basename(self.config.infrastructure_folder)
        infrastructure_dst = os.path.join(self.copy_path, infrastructure_name)

        if "terraform_mutated_copy" in infrastructure_dst:
            print("The copy path is valid")
        else:
            raise Exception("The copy path is invalid")

        if os.path.exists(infrastructure_dst):
            shutil.rmtree(infrastructure_dst)

        if not os.path.exists(self.original_terraform_path):
            raise Exception(f"The infrastructure folder {self.original_terraform_path} does not exist")

        shutil.copytree(self.original_terraform_path, infrastructure_dst)
        self.check_copy_folder(self.copy_path)


        print(f"Created copy of the project in {self.copy_path}")
        return infrastructure_dst 

    def revert_mutations(self, mutation):
        """Revert the mutation applied"""
        print(f"Reverting mutation {mutation.__class__.__name__}")
        mutation.revert_mutation()

    def get_mutations(self, project_path):
        """Inicialize and returns a list of mutations to be applied"""
       
        instance_mutation = InstanceTypeMutation()
        provider_mutation = ProviderMutation()

        instance_mutation.set_file_path(project_path, self.config.get_instance_file_path())
        provider_mutation.set_file_path(project_path, self.config.get_provider_file_path())

        return [instance_mutation, provider_mutation]

    def apply_and_test_mutation(self, mutation):
        """
        Apply the mutation and run the tests    
        Parameters:
        - mutation: mutation to be applied
        """
        print(f"Applying mutation {mutation.__class__.__name__}")
        mutation.apply_mutation()

        test_dir = os.path.join(self.copy_path, "iac-tests/infrastructure/test") # todo make this dinamic because when i tried is giving me a lot erros idk why
        
        output_file_path = os.path.join(test_dir, f"{mutation.__class__.__name__}_output.txt")
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

        self.results.append({
            "mutation": mutation.__class__.__name__,
            "success": success,
            "output": output
        })

        self.revert_mutations(mutation)

        return success
    
    def run(self):
        project_path = self.create_copy()
        mutations = self.get_mutations(project_path)

        for mutation in mutations:
             self.apply_and_test_mutation(mutation)

        self.show_results()

    def show_results(self):
        print(f"All results")
        for result in self.results:
            status = "Success" if result["success"] else "Failed"
            print(f"Mutation: {result['mutation']} - Status: {status}")
            print(f"Output: {result['output']}")
       
