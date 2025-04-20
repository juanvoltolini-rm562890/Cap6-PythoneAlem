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
export DB_USERNAME="rm563348"
export DB_PASSWORD="220982"
export DB_DSN="oracle.fiap.com.br/orcl"
```

Opcionalmente, você pode adicionar essas variáveis ao arquivo `~/.zshrc` (se estiver usando o Zsh, que é o padrão no macOS) ou ao `~/.bash_profile`, caso esteja usando o Bash:

```bash
echo 'export DB_USERNAME="rm563348"' >> ~/.zshrc
echo 'export DB_PASSWORD="220982"' >> ~/.zshrc
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

2. Opções do Menu CLI:
- 1: Visualizar leituras atuais
- 2: Configurar limites
- 3: Testar atuadores
- 4: Visualizar logs
- 5: Sair

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