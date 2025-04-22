####################################
##### Arquivo: mock_data.py
##### Desenvolvedor: AI Assistant
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""
Gerador de dados simulados para quando o banco de dados Oracle não está disponível.

Este módulo fornece funções para gerar dados simulados para sensores, dispositivos e alarmes
quando o banco de dados Oracle não está disponível ou não contém dados.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..models.device import DeviceStatus, DeviceType, DeviceState
from ..models.sensor_data import SensorReading

logger = logging.getLogger(__name__)

def generate_mock_readings(count: int = 10) -> List[Dict[str, Any]]:
    """
    Gera leituras simuladas de sensores.
    
    Args:
        count: Número de leituras a gerar
        
    Returns:
        List[Dict[str, Any]]: Lista de leituras simuladas
    """
    logger.info(f"Gerando {count} leituras simuladas de sensores")
    readings = []
    
    # Hora atual
    now = datetime.now()
    
    for i in range(count):
        # Gerar timestamp decrescente (mais recente primeiro)
        timestamp = now - timedelta(minutes=i*5)
        
        # Gerar valores aleatórios dentro de faixas realistas
        temperature = round(random.uniform(20.0, 30.0), 1)
        humidity = round(random.uniform(50.0, 70.0), 1)
        co2_level = round(random.uniform(500.0, 1500.0), 0)
        ammonia_level = round(random.uniform(5.0, 20.0), 1)
        pressure = round(random.uniform(20.0, 30.0), 1)
        
        # Criar leitura
        reading = {
            "reading_id": count - i,  # IDs decrescentes
            "timestamp": timestamp,
            "temperature": temperature,
            "humidity": humidity,
            "co2_level": co2_level,
            "ammonia_level": ammonia_level,
            "pressure": pressure
        }
        
        readings.append(reading)
    
    logger.info(f"Geradas {len(readings)} leituras simuladas")
    return readings

def generate_mock_device_status(count: int = 10) -> List[Dict[str, Any]]:
    """
    Gera status simulados de dispositivos.
    
    Args:
        count: Número de status a gerar
        
    Returns:
        List[Dict[str, Any]]: Lista de status simulados
    """
    logger.info(f"Gerando {count} status simulados de dispositivos")
    status_list = []
    
    # Hora atual
    now = datetime.now()
    
    # Tipos de dispositivos disponíveis
    device_types = ["EXHAUST_FAN", "INLET", "HEATER", "NEBULIZER"]
    
    # Estados possíveis
    states = ["ON", "OFF", "PARTIAL"]
    
    for i in range(count):
        # Gerar timestamp decrescente (mais recente primeiro)
        timestamp = now - timedelta(minutes=i*10)
        
        # Selecionar tipo de dispositivo aleatório
        device_type = random.choice(device_types)
        
        # Gerar ID de dispositivo baseado no tipo
        device_id = f"{device_type[:3]}{random.randint(1, 5):03d}"
        
        # Selecionar estado aleatório
        state = random.choice(states)
        
        # Gerar valor (relevante principalmente para PARTIAL)
        value = None
        if state == "PARTIAL":
            value = round(random.uniform(10.0, 90.0), 0)
        elif state == "ON":
            value = 100.0
        else:
            value = 0.0
        
        # Criar status
        status = {
            "status_id": count - i,  # IDs decrescentes
            "timestamp": timestamp,
            "device_type": device_type,
            "device_id": device_id,
            "status": state,
            "value": value
        }
        
        status_list.append(status)
    
    logger.info(f"Gerados {len(status_list)} status simulados")
    return status_list

def generate_mock_alarms(count: int = 5) -> List[Dict[str, Any]]:
    """
    Gera alarmes simulados.
    
    Args:
        count: Número de alarmes a gerar
        
    Returns:
        List[Dict[str, Any]]: Lista de alarmes simulados
    """
    logger.info(f"Gerando {count} alarmes simulados")
    alarms = []
    
    # Hora atual
    now = datetime.now()
    
    # Tipos de eventos possíveis
    event_types = ["AMBIENTAL", "ENERGIA", "EQUIPAMENTO"]
    
    # Descrições possíveis por tipo
    descriptions = {
        "AMBIENTAL": [
            "Temperatura acima do limite",
            "Umidade abaixo do limite",
            "Nível de CO2 elevado",
            "Nível de amônia crítico"
        ],
        "ENERGIA": [
            "Falha de energia detectada",
            "Operando com energia de backup",
            "Baixa tensão na rede elétrica"
        ],
        "EQUIPAMENTO": [
            "Falha no exaustor principal",
            "Entrada de ar bloqueada",
            "Aquecedor com funcionamento irregular",
            "Nebulizador sem água"
        ]
    }
    
    for i in range(count):
        # Gerar timestamp decrescente (mais recente primeiro)
        timestamp = now - timedelta(hours=i*2)
        
        # Selecionar tipo de evento aleatório
        event_type = random.choice(event_types)
        
        # Selecionar descrição aleatória baseada no tipo
        description = random.choice(descriptions[event_type])
        
        # Criar alarme
        alarm = {
            "event_id": count - i,  # IDs decrescentes
            "timestamp": timestamp,
            "event_type": event_type,
            "severity": "ERROR",
            "description": description
        }
        
        alarms.append(alarm)
    
    logger.info(f"Gerados {len(alarms)} alarmes simulados")
    return alarms

def generate_mock_sensor_reading() -> SensorReading:
    """
    Gera uma leitura de sensor simulada como objeto SensorReading.
    
    Returns:
        SensorReading: Objeto de leitura de sensor simulado
    """
    # Gerar valores aleatórios dentro de faixas realistas
    temperature = round(random.uniform(20.0, 30.0), 1)
    external_temp = round(temperature + random.uniform(-5.0, 5.0), 1)
    humidity = round(random.uniform(50.0, 70.0), 1)
    co2_level = round(random.uniform(500.0, 1500.0), 0)
    ammonia_level = round(random.uniform(5.0, 20.0), 1)
    pressure = round(random.uniform(20.0, 30.0), 1)
    power_ok = random.random() > 0.1  # 90% de chance de energia OK
    
    # Criar leitura
    reading = SensorReading(
        timestamp=datetime.now(),
        temperature=temperature,
        external_temp=external_temp,
        humidity=humidity,
        co2_level=co2_level,
        ammonia_level=ammonia_level,
        pressure=pressure,
        power_ok=power_ok,
        sensor_id="MOCK001"
    )
    
    return reading

def generate_mock_device_statuses() -> List[DeviceStatus]:
    """
    Gera uma lista de status de dispositivos simulados como objetos DeviceStatus.
    
    Returns:
        List[DeviceStatus]: Lista de objetos de status de dispositivo simulados
    """
    statuses = []
    
    # Definir dispositivos comuns em um aviário
    devices = [
        ("FAN001", DeviceType.EXHAUST_FAN),
        ("FAN002", DeviceType.EXHAUST_FAN),
        ("INL001", DeviceType.INLET),
        ("INL002", DeviceType.INLET),
        ("HTR001", DeviceType.HEATER),
        ("NEB001", DeviceType.NEBULIZER)
    ]
    
    for device_id, device_type in devices:
        # Determinar estado com base em probabilidades
        if device_type == DeviceType.EXHAUST_FAN:
            state = DeviceState.ON if random.random() > 0.3 else DeviceState.OFF
            value = 100.0 if state == DeviceState.ON else 0.0
        elif device_type == DeviceType.INLET:
            r = random.random()
            if r > 0.6:
                state = DeviceState.PARTIAL
                value = round(random.uniform(20.0, 80.0), 0)
            else:
                state = DeviceState.ON if r > 0.3 else DeviceState.OFF
                value = 100.0 if state == DeviceState.ON else 0.0
        elif device_type == DeviceType.HEATER:
            state = DeviceState.ON if random.random() > 0.7 else DeviceState.OFF
            value = 100.0 if state == DeviceState.ON else 0.0
        else:  # NEBULIZER
            state = DeviceState.ON if random.random() > 0.6 else DeviceState.OFF
            value = 100.0 if state == DeviceState.ON else 0.0
        
        # Criar status
        status = DeviceStatus(
            device_id=device_id,
            device_type=device_type,
            state=state,
            value=value,
            last_updated=datetime.now() - timedelta(minutes=random.randint(0, 30)),
            error_message=None
        )
        
        statuses.append(status)
    
    return statuses