

# Terraform Mutation Framework

Este projeto é um framework para gerar e aplicar mutações em arquivos de configuração do Terraform. Ele utiliza **Terratest** para executar testes de integração em um ambiente Terraform e **mutação de código** para verificar a robustez dos testes. O framework é capaz de criar cópias de configurações do Terraform, aplicar mutações em instâncias e provedores, e registrar os resultados dos testes executados em uma cópia do projeto.

## Funcionalidades

- **Criação de cópias de infraestrutura Terraform**: O framework gera uma cópia completa dos arquivos de configuração do Terraform para aplicar as mutações sem modificar o projeto original.
- **Mutações de configuração**: Atualmente, o framework suporta mutações em tipos de instância (`InstanceTypeMutation`) e provedores (`ProviderMutation`).
- **Execução de testes com Terratest**: Usa o `go test` para executar testes de integração no Terraform, salvando a saída dos testes em arquivos.
- **Relatório de mutações**: Após aplicar e reverter mutações, o framework gera um relatório indicando o sucesso ou falha de cada mutação, além de salvar a saída detalhada dos testes em arquivos de texto.

## Estrutura do Projeto

```bash
├── iac-tests                # Diretório com as configurações originais do Terraform
│   ├── infrastructure        # Infraestrutura Terraform (arquivos .tf)
│   └── test                  # Arquivos de teste Terratest
├── terraform-mutation        # Diretório do framework de mutação
│   ├── config.json           # Arquivo de configuração
│   ├── framework.py          # Código principal do framework
│   ├── main.py               # Script principal para executar as mutações
│   └── mutations             # Diretório com classes de mutações
│       ├── base_mutation.py  # Classe base para mutações
│       ├── instance_type_mutation.py  # Mutações de tipo de instância
│       └── provider_mutation.py  # Mutações de provider
└── terraform_mutated_copy    # Diretório gerado automaticamente com a cópia da infraestrutura para aplicar as mutações
```

## Requisitos

- Python 3.8+
- Go 1.15+
- Terratest
- AWS Cli
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
        "root_folder": "iac-tests/",
        "infrastructure_folder": "infrastructure/",
        "test_folder": "test/"
    },
    "file_paths": {
        "instance_file": "lambda.tf",
        "provider_file": "providers.tf"
    }
}
```

- `root_folder`: O diretório principal onde os arquivos do Terraform estão localizados.
- `infrastructure_folder`: O subdiretório onde os arquivos `.tf` de infraestrutura estão armazenados.
- `test_folder`: O diretório onde os testes do Terraform (Terratest) estão armazenados.
- `instance_file`: O arquivo de instância que será alvo de mutação.
- `provider_file`: O arquivo de provider que será alvo de mutação.

## Como Usar

1. **Execute o framework**:

   Para executar o framework de mutação, use o seguinte comando:

   ```bash
   python main.py <caminho_para_o_projeto_terraform> config.json
   ```

   Exemplo:

   ```bash
   python main.py ../ config.json
   ```

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

