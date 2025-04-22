####################################
##### Arquivo: test_mock_data.py
##### Desenvolvedor: AI Assistant
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""Testes unitários para o gerador de dados simulados."""
import unittest
from datetime import datetime

from src.storage.mock_data import (
    generate_mock_readings,
    generate_mock_device_status,
    generate_mock_alarms,
    generate_mock_sensor_reading,
    generate_mock_device_statuses
)
from src.models.device import DeviceType, DeviceState


class TestMockData(unittest.TestCase):
    """Testes para o gerador de dados simulados."""

    def test_generate_mock_readings(self):
        """Testa a geração de leituras simuladas."""
        # Gerar 5 leituras simuladas
        readings = generate_mock_readings(5)
        
        # Verificar se foram geradas 5 leituras
        self.assertEqual(len(readings), 5)
        
        # Verificar se as leituras têm os campos esperados
        for reading in readings:
            self.assertIn('reading_id', reading)
            self.assertIn('timestamp', reading)
            self.assertIn('temperature', reading)
            self.assertIn('humidity', reading)
            self.assertIn('co2_level', reading)
            self.assertIn('ammonia_level', reading)
            self.assertIn('pressure', reading)
            
            # Verificar se os valores estão dentro das faixas esperadas
            self.assertGreaterEqual(reading['temperature'], 20.0)
            self.assertLessEqual(reading['temperature'], 30.0)
            self.assertGreaterEqual(reading['humidity'], 50.0)
            self.assertLessEqual(reading['humidity'], 70.0)
            self.assertGreaterEqual(reading['co2_level'], 500.0)
            self.assertLessEqual(reading['co2_level'], 1500.0)
            self.assertGreaterEqual(reading['ammonia_level'], 5.0)
            self.assertLessEqual(reading['ammonia_level'], 20.0)
            self.assertGreaterEqual(reading['pressure'], 20.0)
            self.assertLessEqual(reading['pressure'], 30.0)
            
            # Verificar se o timestamp é uma data válida
            self.assertIsInstance(reading['timestamp'], datetime)
            
            # Verificar se o ID é negativo (para identificar dados simulados)
            self.assertLessEqual(reading['reading_id'], 0)

    def test_generate_mock_device_status(self):
        """Testa a geração de status de dispositivos simulados."""
        # Gerar 5 status simulados
        status_list = generate_mock_device_status(5)
        
        # Verificar se foram gerados 5 status
        self.assertEqual(len(status_list), 5)
        
        # Verificar se os status têm os campos esperados
        for status in status_list:
            self.assertIn('status_id', status)
            self.assertIn('timestamp', status)
            self.assertIn('device_type', status)
            self.assertIn('device_id', status)
            self.assertIn('status', status)
            self.assertIn('value', status)
            
            # Verificar se o tipo de dispositivo é válido
            self.assertIn(status['device_type'], ["EXHAUST_FAN", "INLET", "HEATER", "NEBULIZER"])
            
            # Verificar se o estado é válido
            self.assertIn(status['status'], ["ON", "OFF", "PARTIAL"])
            
            # Verificar se o timestamp é uma data válida
            self.assertIsInstance(status['timestamp'], datetime)
            
            # Verificar se o ID é negativo (para identificar dados simulados)
            self.assertLessEqual(status['status_id'], 0)

    def test_generate_mock_alarms(self):
        """Testa a geração de alarmes simulados."""
        # Gerar 3 alarmes simulados
        alarms = generate_mock_alarms(3)
        
        # Verificar se foram gerados 3 alarmes
        self.assertEqual(len(alarms), 3)
        
        # Verificar se os alarmes têm os campos esperados
        for alarm in alarms:
            self.assertIn('event_id', alarm)
            self.assertIn('timestamp', alarm)
            self.assertIn('event_type', alarm)
            self.assertIn('severity', alarm)
            self.assertIn('description', alarm)
            
            # Verificar se o tipo de evento é válido
            self.assertIn(alarm['event_type'], ["AMBIENTAL", "ENERGIA", "EQUIPAMENTO"])
            
            # Verificar se a severidade é válida
            self.assertEqual(alarm['severity'], "ERROR")
            
            # Verificar se o timestamp é uma data válida
            self.assertIsInstance(alarm['timestamp'], datetime)
            
            # Verificar se o ID é negativo (para identificar dados simulados)
            self.assertLessEqual(alarm['event_id'], 0)

    def test_generate_mock_sensor_reading(self):
        """Testa a geração de uma leitura de sensor simulada como objeto."""
        # Gerar uma leitura simulada
        reading = generate_mock_sensor_reading()
        
        # Verificar se a leitura tem os atributos esperados
        self.assertTrue(hasattr(reading, 'temperature'))
        self.assertTrue(hasattr(reading, 'external_temp'))
        self.assertTrue(hasattr(reading, 'humidity'))
        self.assertTrue(hasattr(reading, 'co2_level'))
        self.assertTrue(hasattr(reading, 'ammonia_level'))
        self.assertTrue(hasattr(reading, 'pressure'))
        self.assertTrue(hasattr(reading, 'power_ok'))
        self.assertTrue(hasattr(reading, 'sensor_id'))
        
        # Verificar se os valores estão dentro das faixas esperadas
        self.assertGreaterEqual(reading.temperature, 20.0)
        self.assertLessEqual(reading.temperature, 30.0)
        self.assertGreaterEqual(reading.humidity, 50.0)
        self.assertLessEqual(reading.humidity, 70.0)
        self.assertGreaterEqual(reading.co2_level, 500.0)
        self.assertLessEqual(reading.co2_level, 1500.0)
        self.assertGreaterEqual(reading.ammonia_level, 5.0)
        self.assertLessEqual(reading.ammonia_level, 20.0)
        self.assertGreaterEqual(reading.pressure, 20.0)
        self.assertLessEqual(reading.pressure, 30.0)
        
        # Verificar se o sensor_id é o esperado
        self.assertEqual(reading.sensor_id, "MOCK001")

    def test_generate_mock_device_statuses(self):
        """Testa a geração de status de dispositivos simulados como objetos."""
        # Gerar status simulados
        statuses = generate_mock_device_statuses()
        
        # Verificar se foram gerados status para todos os dispositivos esperados
        self.assertGreaterEqual(len(statuses), 6)  # Pelo menos 6 dispositivos
        
        # Verificar se há pelo menos um de cada tipo
        device_types = [status.device_type for status in statuses]
        self.assertIn(DeviceType.EXHAUST_FAN, device_types)
        self.assertIn(DeviceType.INLET, device_types)
        self.assertIn(DeviceType.HEATER, device_types)
        self.assertIn(DeviceType.NEBULIZER, device_types)
        
        # Verificar se os status têm os atributos esperados
        for status in statuses:
            self.assertTrue(hasattr(status, 'device_id'))
            self.assertTrue(hasattr(status, 'device_type'))
            self.assertTrue(hasattr(status, 'state'))
            self.assertTrue(hasattr(status, 'value'))
            self.assertTrue(hasattr(status, 'last_updated'))
            
            # Verificar se o estado é válido
            self.assertIn(status.state, [DeviceState.ON, DeviceState.OFF, DeviceState.PARTIAL])
            
            # Verificar se o valor é consistente com o estado
            if status.state == DeviceState.ON:
                self.assertEqual(status.value, 100.0)
            elif status.state == DeviceState.OFF:
                self.assertEqual(status.value, 0.0)
            elif status.state == DeviceState.PARTIAL:
                self.assertGreaterEqual(status.value, 20.0)
                self.assertLessEqual(status.value, 80.0)


if __name__ == "__main__":
    unittest.main()