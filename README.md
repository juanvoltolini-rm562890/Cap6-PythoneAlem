# Sistema de Controle de Aviário

Um sistema automatizado de controle ambiental para aviários que mantém condições ideais para o bem-estar das aves através de controle inteligente do clima, gerenciamento da ventilação e monitoramento de segurança.

## Arquitetura do Sistema

```
                     +----------------+
                     |     Main      |
                     | Control Loop  |
                     +----------------+
                           |
           +---------------+---------------+
           |              |               |
    +-------------+ +-----------+ +-------------+
    |   Sensors   | |   Core    | | Actuators  |
    | (T,RH,CO2)  | | Decision  | | (Fans,etc) |
    +-------------+ +-----------+ +-------------+
           |              |               |
    +-------------+ +-----------+ +-------------+
    |  Storage    | | Security  | |    LCD     |
    | (DB/Files)  | | & Alarms  | |  Display   |
    +-------------+ +-----------+ +-------------+
```

## Funcionalidades

- **Controle Climático**: Monitoramento de temperatura, umidade, CO₂, amônia e pressão
- **Regulação Automatizada**: Cortinas, entradas de ar e ventiladores de exaustão
- **Sistemas de Segurança**: Detecção de falha de energia, alertas de temperatura crítica
- **Interface em Tempo Real**: Display LCD e interface de configuração CLI

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/juanvoltolini-rm562890/Cap6-PythoneAlem
cd Cap6-PythoneAlem
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate   # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

### 4. Configure o banco de dados Oracle (Não funciona com o banco de dados da FIAP por falta de permissão aos nossos usuários)

1. **Defina as credenciais do banco de dados como variáveis de ambiente no MACOS:**

No terminal, execute:

```bash
export DB_USERNAME="rmXXXXXX"
export DB_PASSWORD="XXXXXX"
export DB_DSN="oracle.fiap.com.br/orcl"
```

Opcionalmente, você pode adicionar essas variáveis ao arquivo `~/.zshrc` (se estiver usando o Zsh, que é o padrão no macOS) ou ao `~/.bash_profile`, caso esteja usando o Bash:

```bash
echo 'export DB_USERNAME="rmXXXXXX"' >> ~/.zshrc
echo 'export DB_PASSWORD="XXXXXX"' >> ~/.zshrc
echo 'export DB_DSN="oracle.fiap.com.br/orcl"' >> ~/.zshrc
source ~/.zshrc
```

2. **Execute o script:**

No terminal, rode o script no diretório principal do projeto:

```bash
python db/setup_db.py
```

Se o banco de dados estiver configurado corretamente, o script será executado e o schema definido.

---

## Uso

1. Inicie o sistema de controle:
```bash
python main.py
```

2. Opções de linha de comando:
```
--config PATH           Caminho para o arquivo de configuração
--oracle-user USER      Nome de usuário do banco de dados Oracle
--oracle-password PASS  Senha do banco de dados Oracle
--oracle-host HOST      Host do banco de dados Oracle
--no-menu               Executar sem interface interativa
--no-oracle             Desabilitar conexão com banco de dados Oracle
--use-mock-data         Forçar o uso de dados simulados mesmo com Oracle disponível
```

3. Opções do Menu CLI:
- 1: Visualizar leituras atuais
- 2: Configurar limites
- 3: Testar atuadores
- 4: Visualizar logs
- 5: Sair

### Exemplos de uso

Para executar com dados simulados (sem tentar conectar ao Oracle):
```bash
python main.py --use-mock-data
```

Para executar sem interface interativa e sem Oracle:
```bash
python main.py --no-menu --no-oracle
```

Para executar com credenciais Oracle específicas:
```bash
python main.py --oracle-user "username" --oracle-password "password" --oracle-host "host"
```

## Estrutura do Projeto

```
aviary-control/
├─ data/sample/        # Arquivos de dados de exemplo
├─ db/schema.sql       # Schema do banco de dados Oracle
├─ docs/              
│  ├─ architecture.md  # Design detalhado do sistema
│  └─ user_guide.md    # Documentação do usuário
├─ src/
│  ├─ core/           # Lógica de controle
│  ├─ models/         # Modelos de dados
│  ├─ sensors/        # Interfaces dos sensores
│  ├─ actuators/      # Controle de dispositivos
│  └─ storage/        # Persistência de dados
├─ main.py           
└─ README.md
```

## Desenvolvimento

- Python 3.12+
- Compatível com PEP 8 (88 colunas)
- Docstrings no estilo Google

## Atualizações Recentes

### Suporte a Dados Simulados

1. Foi adicionada a opção `--use-mock-data` para forçar o uso de dados simulados mesmo quando o Oracle está disponível.

2. O sistema agora detecta automaticamente falhas na conexão Oracle e usa dados simulados como fallback.

3. Foram adicionados testes unitários para verificar o funcionamento correto do modo de dados simulados.

### Integração do Teste de Conexão Oracle

1. Foi adicionado um método estático `test_connection_fix()` à classe `OracleStorage`

2. Foi adicionado um bloco `if __name__ == "__main__"` ao arquivo `oracle_db.py` que permite executar o teste diretamente:
   ```bash
   python -m src.storage.oracle_db
   ```

3. Os testes unitários foram atualizados para incluir o teste da nova funcionalidade.

Essas alterações mantêm toda a funcionalidade original enquanto simplificam a estrutura do projeto, eliminando a necessidade de um arquivo de teste separado.