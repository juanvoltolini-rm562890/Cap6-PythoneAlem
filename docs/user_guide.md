# Guia do Usuário - Sistema de Controle de Aviário

## Sumário
1. [Introdução](#introdução)
2. [Instalação](#instalação)
3. [Configuração](#configuração)
4. [Uso do Sistema](#uso-do-sistema)
5. [Monitoramento](#monitoramento)
6. [Resolução de Problemas](#resolução-de-problemas)
7. [Exemplos](#exemplos)

## Introdução

O Sistema de Controle de Aviário é uma solução automatizada para manter condições ambientais ideais em aviários. O sistema monitora e controla:

- Temperatura
- Umidade
- Níveis de CO₂
- Níveis de amônia
- Pressão do ar
- Ventilação
- Aquecimento
- Nebulização

## Instalação

1. Requisitos do Sistema:
   - Python 3.12 ou superior
   - Oracle Database 19c ou superior
   - Sistema operacional: Linux, Windows ou macOS

2. Instalação do Software:
   ```bash
   # Clone o repositório
   git clone https://github.com/yourusername/aviary-control.git
   cd aviary-control

   # Crie e ative o ambiente virtual
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\\Scripts\\activate   # Windows

   # Instale as dependências
   pip install -r requirements.txt
   ```

3. Configuração do Banco de Dados:
   ```bash
   # Configure o banco de dados Oracle
   cd db
   sqlplus usuario/senha@host @schema.sql
   ```

## Configuração

### Configuração Básica

1. Arquivo de Configuração:
   ```json
   {
     "environmental_limits": {
       "temp_min": 18.0,
       "temp_max": 32.0,
       "humidity_min": 50.0,
       "humidity_max": 70.0,
       "co2_max": 2000.0,
       "ammonia_max": 25.0,
       "pressure_target": 25.0
     },
     "reading_interval": 30,
     "log_level": "INFO",
     "alarm_enabled": true,
     "backup_power_threshold": 20.0
   }
   ```

2. Variáveis de Ambiente:
   ```bash
   export ORACLE_USER=seu_usuario
   export ORACLE_PASSWORD=sua_senha
   export ORACLE_HOST=localhost
   ```

### Configuração Avançada

1. Ajuste de Limites:
   - Temperatura: 18-32°C
   - Umidade: 50-70%
   - CO₂: até 2000 ppm
   - Amônia: até 25 ppm
   - Pressão: 20-30 Pa

2. Intervalos de Leitura:
   - Mínimo: 5 segundos
   - Recomendado: 30 segundos
   - Máximo: 60 segundos

## Uso do Sistema

### Interface de Linha de Comando

1. Iniciar o Sistema:
   ```bash
   python main.py
   ```

2. Opções do Menu Principal:
   - 1: Visualizar leituras atuais
   - 2: Configurar limites
   - 3: Testar atuadores
   - 4: Visualizar logs
   - 5: Configuração do sistema
   - 6: Ajuda
   - 0: Sair

### Modo Não-Interativo

Para execução em segundo plano:
```bash
python main.py --no-menu
```

## Monitoramento

### Visualização de Dados

1. Leituras Atuais:
   ```
   +---------------------+-------------+----------+-------+--------+---------+
   | Timestamp          | Temperatura | Umidade  | CO₂   | Amônia | Pressão |
   +---------------------+-------------+----------+-------+--------+---------+
   | 2024-01-20 10:30:00| 25.5°C     | 65.0%    | 800   | 15.0   | 25.0    |
   +---------------------+-------------+----------+-------+--------+---------+
   ```

2. Histórico de Alarmes:
   ```
   +---------------------+--------+--------------------------------+
   | Timestamp          | Nível  | Mensagem                       |
   +---------------------+--------+--------------------------------+
   | 2024-01-20 10:35:00| ERROR  | Temperatura acima do limite!   |
   +---------------------+--------+--------------------------------+
   ```

### Logs do Sistema

1. Arquivos de Log:
   - `data/logs/readings_YYYYMMDD.txt`: Leituras dos sensores
   - `data/logs/devices_YYYYMMDD.txt`: Status dos dispositivos
   - `data/logs/alarms.txt`: Registro de alarmes

2. Níveis de Log:
   - DEBUG: Informações detalhadas para diagnóstico
   - INFO: Operações normais do sistema
   - WARNING: Situações inesperadas mas não críticas
   - ERROR: Erros que precisam de atenção

## Resolução de Problemas

### Problemas Comuns

1. Erro de Conexão com Banco de Dados
   - Verifique as credenciais
   - Confirme se o serviço Oracle está rodando
   - Teste a conectividade de rede

2. Leituras Incorretas
   - Verifique a calibração dos sensores
   - Confirme as conexões físicas
   - Verifique interferências ambientais

3. Atuadores Não Respondem
   - Verifique a alimentação
   - Teste as conexões físicas
   - Confirme as permissões do sistema

### Manutenção Preventiva

1. Diária:
   - Verificar leituras dos sensores
   - Monitorar logs de alarmes
   - Confirmar operação dos atuadores

2. Semanal:
   - Backup do banco de dados
   - Limpeza de logs antigos
   - Verificação de calibração

3. Mensal:
   - Manutenção física dos sensores
   - Atualização do software
   - Revisão das configurações

## Exemplos

### Configuração Típica para Verão

```json
{
  "environmental_limits": {
    "temp_min": 20.0,
    "temp_max": 28.0,
    "humidity_min": 55.0,
    "humidity_max": 65.0,
    "co2_max": 1800.0,
    "ammonia_max": 20.0,
    "pressure_target": 23.0
  },
  "reading_interval": 20,
  "alarm_enabled": true
}
```

### Configuração Típica para Inverno

```json
{
  "environmental_limits": {
    "temp_min": 22.0,
    "temp_max": 30.0,
    "humidity_min": 50.0,
    "humidity_max": 70.0,
    "co2_max": 2000.0,
    "ammonia_max": 25.0,
    "pressure_target": 25.0
  },
  "reading_interval": 30,
  "alarm_enabled": true
}
```

### Comandos Úteis

1. Iniciar com Configuração Personalizada:
   ```bash
   python main.py --config config/custom.json
   ```

2. Conexão com Banco de Dados Remoto:
   ```bash
   python main.py --oracle-host remote.db.com --oracle-user admin
   ```

3. Execução em Modo Silencioso:
   ```bash
   python main.py --no-menu > /dev/null 2>&1 &
   ```