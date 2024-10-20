import sys
from framework import MutationFramework

# ex: python main.py ../iac-tests/ config.json


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python main.py <caminho_para_o_projeto> <caminho_para_o_config.json>")
        sys.exit(1)
 
    original_terraform_path = sys.argv[1] # Path project
    config_file_path = sys.argv[2] # Path to the config file config.json

    framework = MutationFramework(original_terraform_path, config_file_path)

    framework.run()
