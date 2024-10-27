import re

def apply_operators(content, mutations):
    """
    Applies a series of mutations to the content of a file.

    :param content: List of lines from the file to be mutated.
    :param mutations: List of dictionaries with 'pattern' and 'replacement' keys for each mutation.
    :return: Mutated content.
    """
    mutated_content = []
    for line in content:
        for mutation in mutations:
            pattern = mutation['pattern']
            replacement = mutation['replacement']
            line = re.sub(pattern, replacement, line)
        mutated_content.append(line)
    return mutated_content
