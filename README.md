# Terraform Mutation Framework: Terramutate

Este projeto é um framework para gerar e aplicar mutações em arquivos de configuração do Terraform. Ele utiliza **Terratest** para executar testes de integração em um ambiente Terraform e **mutação de código** para verificar a robustez dos testes.

 O framework é capaz de criar cópias de configurações do Terraform, aplicar mutações, utilizando os operadores de mutação definidos através de uma análise qualitativa e quantitativa e registrar os resultados dos testes executados em uma cópia do projeto.

## Funcionalidades

- **Criação de cópias de infraestrutura Terraform**: O framework gera uma cópia completa dos arquivos de configuração do Terraform para aplicar as mutações sem modificar o projeto original.
- **Mutações de configuração**: Atualmente, o framework suporta mutações todas as mutações definidas em `config.yaml`, onde há cada operador de mutação definido e sua categorização.
- **Execução de testes com Terratest**: Usa o `go test` para executar testes de integração no Terraform, salvando a saída dos testes em arquivos.
- **Relatório de mutações**: Após aplicar e reverter mutações, o framework gera um relatório indicando o sucesso ou falha de cada mutação, além de salvar a saída detalhada dos testes em arquivos de texto.

## Estrutura do Projeto

```bash
.
├── app
│   ├── config
│   │   ├── config.json
│   │   ├── config.yaml
│   │   ├── __init__.py
│   │   ├── loader.py
│   ├── framework.py
│   ├── __init__.py
│   ├── main.py
│   ├── mutations
│   │   ├── base_mutation.py
│   │   ├── base_operators.py
│   │   ├── __init__.py
├── README.md
├── setup.py
├── terraform-mutation.code-workspace
└── tests
    ├── test_base_mutation.py
    ├── test_loader.py
    └── test_mutation_framework.py
```

## Requisitos

- Python 3.8+
- Go 1.15+
- Terratest
- AWS CLI
- Local Stack
- Terraform

## Instalação

1. **Clone o repositório**:

   ```bash
   git clone https://github.com/asunnya/terraform-mutation.git
   cd terraform-mutation
   ```

2. **Crie um ambiente virtual e instale as dependências**:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   Alternativamente, você pode usar o `setup.py` para instalar o pacote:
   ```bash
   python setup.py install
   ```

3. **Instale o Go, Terratest, AWS CLI, LocalStack e Configure** 
   
   WIP

4. **Instale o Terraform** (se necessário):

   ```bash
   wget https://releases.hashicorp.com/terraform/1.0.0/terraform_1.0.0_linux_amd64.zip
   unzip terraform_1.0.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

## Configuração

O arquivo `config.json` deve ser configurado para definir os caminhos relativos da infraestrutura e dos arquivos de teste:

```json
{
    "terraform_paths": {
        "root_folder": "app/infrastructure/",
        "infrastructure_folder": "app/infrastructure/",
        "test_folder": "tests/"
    }
}
```

- `root_folder`: O diretório principal onde os arquivos do Terraform estão localizados.
- `infrastructure_folder`: O subdiretório onde os arquivos `.tf` de infraestrutura estão armazenados.
- `test_folder`: O diretório onde os testes do Terraform (Terratest) estão armazenados.

## Como Usar

1. **Execute o framework**:

   Para executar o framework de mutação, use o seguinte comando:

   ```bash
   python app/main.py <caminho_para_projeto> <caminho_para_config.json> [<caminho_para_config.yaml>]
   ```

   - `<caminho_para_projeto>`: Caminho para o diretório do projeto Terraform que você deseja testar.
   - `<caminho_para_config.json>`: Caminho para o arquivo de configuração JSON que define os caminhos relativos da infraestrutura e dos arquivos de teste.
   - `<caminho_para_config.yaml>`: (Opcional) Caminho para o arquivo de configuração YAML que define os operadores de mutação. O padrão é `config/config.yaml`.

   Exemplo de execução:

   ```bash
   python app/main.py ../meu_projeto_terraform app/config/config.json
   ```

   Neste exemplo, o framework irá:

   - Criar uma cópia do projeto de infraestrutura especificado.
   - Aplicar as mutações definidas no arquivo `config.yaml`.
   - Executar os testes de integração usando Terratest.
   - Exibir o resultado de cada mutação e o caminho dos arquivos de saída dos testes no console.
   - Salvar a saída dos testes em arquivos `.txt` na pasta de testes do projeto copiado.

2. **Resultados**:

   - O framework irá criar uma cópia do projeto de infraestrutura e aplicar as mutações.
   - O resultado de cada mutação e o caminho dos arquivos de saída dos testes serão exibidos no console.
   - A saída dos testes será salva em arquivos `.txt` na pasta de testes do projeto copiado.

## Exemplo de Saída

Ao executar o framework, você verá uma saída semelhante a esta:

```bash
Applying mutation InstanceTypeMutation
Mutation InstanceTypeMutation applied to ../terraform_mutated_copy/iac-tests/infrastructure/lambda.tf
Reverting mutation InstanceTypeMutation
Mutação revertida no arquivo: ../terraform_mutated_copy/iac-tests/infrastructure/lambda.tf
Test output saved in ../terraform_mutated_copy/iac-tests/infrastructure/test/InstanceTypeMutation_output.txt

Applying mutation ProviderMutation
Mutation ProviderMutation applied to ../terraform_mutated_copy/iac-tests/infrastructure/providers.tf
Reverting mutation ProviderMutation
Mutação revertida no arquivo: ../terraform_mutated_copy/iac-tests/infrastructure/providers.tf
Test output saved in ../terraform_mutated_copy/iac-tests/infrastructure/test/ProviderMutation_output.txt

All results:
Mutation: InstanceTypeMutation - Status: Failed
Output: Test output saved in ../terraform_mutated_copy/iac-tests/infrastructure/test/InstanceTypeMutation_output.txt
Mutation: ProviderMutation - Status: Failed
Output: Test output saved in ../terraform_mutated_copy/iac-tests/infrastructure/test/ProviderMutation_output.txt
```

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

