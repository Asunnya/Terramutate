import sys
import os
import yaml
from config.loader import load_config_json, load_config_yaml
from app.framework import MutationFramework
# ex: python main.py ../iac-tests/ config.json


def validate_path(path, path_type="file"):
    """
    Validate if the path exists and is of the correct type.
    
    Args:
        path (str): path to be validated.
        path_type (str): type of the path to be validated. Can be "file" or "directory".
    
    Returns:
        bool: true if the path is valid, exception otherwise.
    """
    if path_type == "file" and not os.path.isfile(path):
        raise FileNotFoundError(f"Erro: O arquivo '{path}' não foi encontrado.")
    elif path_type == "directory" and not os.path.isdir(path):
        raise NotADirectoryError(f"Erro: O diretório '{path}' não existe.")
    return True 

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <path_to_project> <path_to_config.json> [<path_to_config.yaml>]")
        sys.exit(1)
    
    original_terraform_path = sys.argv[1]
    config_file_path_json = sys.argv[2]
    config_file_path_yaml = sys.argv[3] if len(sys.argv) > 3 else "config/config.yaml"

    try:
        validate_path(original_terraform_path, path_type="directory")
        validate_path(config_file_path_json, path_type="file")
        validate_path(config_file_path_yaml, path_type="file")
    except (FileNotFoundError, NotADirectoryError) as e:
        print(e)
        sys.exit(1)

    config_json = load_config_json(config_file_path_json)
    config_yaml = load_config_yaml(config_file_path_yaml)

    mutation_mode = config_yaml.get('mutation_mode', 'individual')

    framework = MutationFramework(original_terraform_path, config_json, config_yaml, mutation_mode=mutation_mode)
    framework.run()

if __name__ == "__main__":
    main()
