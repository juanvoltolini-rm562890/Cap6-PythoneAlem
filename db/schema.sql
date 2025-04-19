####################################
##### Arquivo: schema.sql
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção, 
####################################

-- Esquema do Banco de Dados do Sistema de Controle de Aviário

-- Tabela de Leituras dos Sensores
CREATE TABLE sensor_readings (
    reading_id NUMBER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature NUMBER(5,2),
    humidity NUMBER(5,2),
    co2_level NUMBER(6,2),
    ammonia_level NUMBER(5,2),
    pressure NUMBER(5,2)
);

-- Tabela de Configuração do Sistema
CREATE TABLE system_config (
    config_id NUMBER PRIMARY KEY,
    param_name VARCHAR2(50) UNIQUE,
    param_value VARCHAR2(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Status dos Atuadores
CREATE TABLE actuator_status (
    status_id NUMBER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    device_type VARCHAR2(20),
    device_id VARCHAR2(20),
    status VARCHAR2(20),
    value NUMBER(5,2)
);

-- Tabela de Eventos de Alarme
CREATE TABLE alarm_events (
    event_id NUMBER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR2(50),
    severity VARCHAR2(20),
    description VARCHAR2(200)
);

-- Sequências
CREATE SEQUENCE reading_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE config_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE status_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE event_seq START WITH 1 INCREMENT BY 1;

-- Valores Padrão de Configuração
INSERT INTO system_config (config_id, param_name, param_value) VALUES
(config_seq.NEXTVAL, 'temp_max', '32.0'),
(config_seq.NEXTVAL, 'temp_min', '18.0'),
(config_seq.NEXTVAL, 'humidity_max', '70.0'),
(config_seq.NEXTVAL, 'humidity_min', '50.0'),
(config_seq.NEXTVAL, 'co2_max', '2000.0'),
(config_seq.NEXTVAL, 'ammonia_max', '25.0'),
(config_seq.NEXTVAL, 'pressure_target', '25.0');

-- Índices
CREATE INDEX idx_readings_timestamp ON sensor_readings(timestamp);
CREATE INDEX idx_alarms_timestamp ON alarm_events(timestamp);
CREATE INDEX idx_actuator_status ON actuator_status(device_type, device_id);
