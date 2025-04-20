--####################################
--##### Arquivo: schema.sql
--##### Desenvolvedor: Juan F. Voltolini
--##### Instituição: FIAP
--##### Trabalho: Cap 6 - Python e Além
--##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção,
--####################################

-- Esquema do Banco de Dados para Controle de Aviário
-- Tabela de Leituras dos Sensores
CREATE TABLE :SCHEMA.sensor_readings (
    reading_id NUMBER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature NUMBER(5,2),
    humidity NUMBER(5,2),
    co2_level NUMBER(6,2),
    ammonia_level NUMBER(5,2),
    pressure NUMBER(5,2)
);

-- Tabela de Configuração do Sistema
CREATE TABLE :SCHEMA.system_config (
    config_id NUMBER PRIMARY KEY,
    param_name VARCHAR2(50) UNIQUE,
    param_value VARCHAR2(100),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de Status dos Atuadores
CREATE TABLE :SCHEMA.actuator_status (
    status_id NUMBER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    device_type VARCHAR2(20),
    device_id VARCHAR2(20),
    status VARCHAR2(20),
    value NUMBER(5,2)
);

-- Tabela de Eventos de Alarme
CREATE TABLE :SCHEMA.alarm_events (
    event_id NUMBER PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type VARCHAR2(50),
    severity VARCHAR2(20),
    description VARCHAR2(200)
);

-- Sequências
CREATE SEQUENCE :SCHEMA.reading_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE :SCHEMA.config_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE :SCHEMA.status_seq START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE :SCHEMA.event_seq START WITH 1 INCREMENT BY 1;

-- Inserção de Valores Padrão de Configuração
INSERT INTO :SCHEMA.system_config (config_id, param_name, param_value)
VALUES (:SCHEMA.config_seq.NEXTVAL, 'temp_max', '32.0');
INSERT INTO :SCHEMA.system_config (config_id, param_name, param_value)
VALUES (:SCHEMA.config_seq.NEXTVAL, 'temp_min', '18.0');
INSERT INTO :SCHEMA.system_config (config_id, param_name, param_value)
VALUES (:SCHEMA.config_seq.NEXTVAL, 'humidity_max', '70.0');
INSERT INTO :SCHEMA.system_config (config_id, param_name, param_value)
VALUES (:SCHEMA.config_seq.NEXTVAL, 'humidity_min', '50.0');
INSERT INTO :SCHEMA.system_config (config_id, param_name, param_value)
VALUES (:SCHEMA.config_seq.NEXTVAL, 'co2_max', '2000.0');
INSERT INTO :SCHEMA.system_config (config_id, param_name, param_value)
VALUES (:SCHEMA.config_seq.NEXTVAL, 'ammonia_max', '25.0');
INSERT INTO :SCHEMA.system_config (config_id, param_name, param_value)
VALUES (:SCHEMA.config_seq.NEXTVAL, 'pressure_target', '25.0');

-- Índices
CREATE INDEX :SCHEMA.idx_readings_timestamp
    ON :SCHEMA.sensor_readings(timestamp);
CREATE INDEX :SCHEMA.idx_alarms_timestamp
    ON :SCHEMA.alarm_events(timestamp);
CREATE INDEX :SCHEMA.idx_actuator_status
    ON :SCHEMA.actuator_status(device_type, device_id);