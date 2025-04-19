# Sistema de Controle de Aviário - Documentação da Arquitetura

## Visão Geral do Sistema

O Sistema de Controle de Aviário é projetado para manter condições ambientais ideais em aviários através do monitoramento e controle automatizado de vários parâmetros. O sistema segue uma arquitetura modular com clara separação de responsabilidades.

## Componentes Principais

### 1. Camada de Modelos (`src/models/`)
- Estruturas de dados representando entidades do sistema
- Validação de entrada e verificação de tipos de dados
- Regras de negócio e restrições

### 2. Camada de Sensores (`src/sensors/`)
- Implementações simuladas de sensores físicos
- Coleta periódica de leituras
- Validação e normalização de dados
- Sensores suportados:
  - Temperatura
  - Umidade
  - CO₂
  - Amônia
  - Pressão

### 3. Camada de Atuadores (`src/actuators/`)
- Interfaces de controle para dispositivos físicos
- Gerenciamento de estado e verificações de segurança
- Atuadores suportados:
  - Ventiladores de exaustão
  - Cortinas
  - Entradas de ar
  - Aquecedores
  - Nebulizadores
  - Sistemas de alarme

### 4. Lógica Principal (`src/core/`)
- Motor de decisão para controle ambiental
- Processamento de regras e determinação de ações
- Monitoramento de segurança e respostas de emergência
- Coordenação do loop principal de controle

### 5. Camada de Armazenamento (`src/storage/`)
- Persistência de dados (Banco de dados Oracle)
- Gerenciamento de configuração
- Sistema de logging
- Operações de arquivo (JSON/TXT)

## Fluxo de Controle

1. **Coleta de Dados**
   ```
   Sensores → Validação → Armazenamento → Motor de Decisão
   ```

2. **Tomada de Decisão**
   ```
   Estado Atual + Regras → Ações → Atuadores
   ```

3. **Loop de Monitoramento**
   ```
   Ler Sensores → Processar Dados → Atualizar Display → Executar Ações
   ```

## Recursos de Segurança

1. **Proteção contra Falha de Energia**
   - Detecção de UPS
   - Mudança automática de modo
   - Priorização de sistemas críticos

2. **Alertas Ambientais**
   - Sistema de aviso multinível
   - Ações corretivas automáticas
   - Registro de eventos

3. **Monitoramento da Saúde do Sistema**
   - Validação de sensores
   - Feedback dos atuadores
   - Verificações de comunicação

## Fluxo de Dados

```
[Sensores] → [Validação de Dados] → [Armazenamento]
     ↓            ↓                    ↑
[Motor de Decisão] → [Atuadores] → [Logging]
     ↓
[Interface do Usuário]
```

## Gerenciamento de Configuração

- Arquivos de configuração baseados em JSON
- Atualizações de parâmetros em tempo de execução
- Armazenamento persistente no banco de dados Oracle
- Aplicação de regras de validação

## Design da Interface

1. **Display LCD**
   - Leituras atuais
   - Status do sistema
   - Alarmes ativos

2. **Interface CLI**
   - Gerenciamento de configuração
   - Controles manuais
   - Diagnóstico do sistema

## Tratamento de Erros

1. **Falhas de Sensores**
   - Verificações de redundância
   - Valores seguros padrão
   - Notificações ao operador

2. **Falhas de Atuadores**
   - Monitoramento de feedback
   - Posições à prova de falhas
   - Caminhos alternativos de ação