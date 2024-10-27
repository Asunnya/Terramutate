import sys
from framework import MutationFramework
import yaml
# ex: python main.py ../iac-tests/ config.json


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python main.py <caminho_para_o_projeto> <caminho_para_o_config.json> ")
        sys.exit(1)
 
    original_terraform_path = sys.argv[1] # Path project
    config_file_path = sys.argv[2] # Path to the config file config.json
    
    # check if there is another yaml file
    yaml_file = sys.argv[3] if len(sys.argv) > 3 else "config.yaml"


    with open(yaml_file, 'r') as config_file:
        config = yaml.safe_load(config_file)

    mutation_mode = config.get('mutation_mode', 'individual')

    framework = MutationFramework(original_terraform_path, config_file_path, mutation_mode=mutation_mode)

    framework.run()
