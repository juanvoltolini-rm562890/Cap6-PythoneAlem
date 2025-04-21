####################################
##### Arquivo: test_oracle_storage.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""Testes unitários para funcionalidades de armazenamento Oracle."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.storage.oracle_db import OracleStorage
from src.models.sensor_data import SensorReading
from src.models.device import DeviceStatus, DeviceType, DeviceState


class TestOracleStorage:
    """Casos de teste para a classe OracleStorage."""

    @pytest.fixture
    def oracle_storage(self):
        """Cria uma instância de OracleStorage para testes."""
        with patch('oracledb.connect') as mock_connect:
            # Configura o mock para retornar um objeto de conexão simulado
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            
            # Configura o mock do cursor para retornar informações de versão
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchone.return_value = ["Oracle Database 19c Enterprise Edition"]
            
            # Cria a instância de OracleStorage
            storage = OracleStorage(
                username="test_user",
                password="test_password",
                dsn="test_dsn"
            )
            
            # Configura o mock da conexão
            storage._connection = mock_connection
            
            # Configura atributos adicionais para o mock da conexão
            mock_connection.autocommit = False
            # Nota: encoding não é mais necessário pois o código agora verifica se o atributo existe
            
            yield storage

    def test_connect(self):
        """Testa o método connect."""
        with patch('oracledb.connect') as mock_connect:
            # Configura o mock
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            
            # Configura o mock do cursor para retornar informações de versão
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchone.return_value = ["Oracle Database 19c Enterprise Edition"]
            
            # Configura atributos adicionais para o mock da conexão
            mock_connection.autocommit = False
            # Nota: encoding não é mais necessário pois o código agora verifica se o atributo existe
            
            # Cria a instância e chama connect
            storage = OracleStorage("test_user", "test_password", "test_dsn")
            storage.connect()
            
            # Verifica se connect foi chamado com os parâmetros corretos
            mock_connect.assert_called_once_with(
                user="test_user",
                password="test_password",
                dsn="test_dsn"
            )
            
            # Verifica se a conexão foi armazenada
            assert storage._connection == mock_connection

    def test_disconnect(self, oracle_storage):
        """Testa o método disconnect."""
        # Chama disconnect
        oracle_storage.disconnect()
        
        # Verifica se close foi chamado na conexão
        oracle_storage._connection.close.assert_called_once()

    def test_test_connection_success(self, oracle_storage):
        """Testa o método test_connection quando a conexão é bem-sucedida."""
        # Configura o mock do cursor
        mock_cursor = MagicMock()
        oracle_storage._connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]  # Simula resultado bem-sucedido
        
        # Chama test_connection
        result = oracle_storage.test_connection()
        
        # Verifica se a consulta foi executada
        mock_cursor.execute.assert_called_with("SELECT 1 FROM DUAL")
        
        # Verifica se o resultado é True
        assert result is True

    def test_test_connection_failure(self, oracle_storage):
        """Testa o método test_connection quando a conexão falha."""
        # Configura o mock do cursor para retornar None
        mock_cursor = MagicMock()
        oracle_storage._connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None  # Simula falha na consulta
        
        # Chama test_connection
        result = oracle_storage.test_connection()
        
        # Verifica se a consulta foi executada
        mock_cursor.execute.assert_called_with("SELECT 1 FROM DUAL")
        
        # Verifica se o resultado é False
        assert result is False

    def test_test_connection_exception(self):
        """Testa o método test_connection quando ocorre uma exceção."""
        with patch('oracledb.connect') as mock_connect:
            # Configura o mock para lançar uma exceção
            mock_connect.side_effect = Exception("Erro de conexão")
            
            # Cria a instância
            storage = OracleStorage("test_user", "test_password", "test_dsn")
            
            # Verifica se test_connection lança a exceção
            with pytest.raises(Exception, match="Erro de conexão"):
                storage.test_connection()

    def test_store_reading(self, oracle_storage):
        """Testa o método store_reading."""
        # Cria uma leitura de teste
        reading = SensorReading(
            timestamp=datetime(2025, 4, 19, 10, 0, 0),
            temperature=25.8,
            external_temp=24.5,
            humidity=59.5,
            co2_level=786,
            ammonia_level=10.3,
            pressure=24.5,
            power_ok=True,
            sensor_id="ARRAY001"
        )
        
        # Chama store_reading
        oracle_storage.store_reading(reading)
        
        # Verifica se execute foi chamado no cursor
        cursor = oracle_storage._connection.cursor.return_value.__enter__.return_value
        assert cursor.execute.called
        
        # Verifica se commit foi chamado na conexão
        oracle_storage._connection.commit.assert_called_once()

    def test_store_device_status(self, oracle_storage):
        """Testa o método store_device_status."""
        # Cria um status de dispositivo de teste
        status = DeviceStatus(
            device_type=DeviceType.EXHAUST_FAN,
            device_id="FAN001",
            state=DeviceState.ON,
            value=100.0,
            last_updated=datetime(2025, 4, 19, 10, 0, 0)
        )
        
        # Chama store_device_status
        oracle_storage.store_device_status(status)
        
        # Verifica se execute foi chamado no cursor
        cursor = oracle_storage._connection.cursor.return_value.__enter__.return_value
        assert cursor.execute.called
        
        # Verifica se commit foi chamado na conexão
        oracle_storage._connection.commit.assert_called_once()

    def test_store_alarm(self, oracle_storage):
        """Testa o método store_alarm."""
        # Chama store_alarm
        timestamp = datetime(2025, 4, 19, 10, 0, 0)
        event_type = "AMBIENTAL"
        description = "Temperatura acima do limite"
        
        oracle_storage.store_alarm(timestamp, event_type, description)
        
        # Verifica se execute foi chamado no cursor
        cursor = oracle_storage._connection.cursor.return_value.__enter__.return_value
        assert cursor.execute.called
        
        # Verifica se commit foi chamado na conexão
        oracle_storage._connection.commit.assert_called_once()
        
    def test_ensure_connection_reconnect(self, oracle_storage):
        """Testa o método _ensure_connection quando a conexão precisa ser reestabelecida."""
        # Configura o mock do cursor para simular uma conexão inativa
        mock_cursor = MagicMock()
        oracle_storage._connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Conexão perdida")
        
        # Chama _ensure_connection
        oracle_storage._ensure_connection()
        
        # Verifica se disconnect e connect foram chamados
        oracle_storage._connection.close.assert_called_once()
        assert oracle_storage._connection is not None
    def test_check_schema_exists(self, oracle_storage):
        """Testa o método check_schema_exists."""
        # Configura o mock do cursor para simular tabelas existentes
        mock_cursor = MagicMock()
        oracle_storage._connection.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Configura o comportamento para a verificação de tabelas
        mock_cursor.fetchone.side_effect = [
            [1],  # sensor_readings existe
            [0],  # actuator_status não existe
            [1],  # alarm_events existe
            [1],  # sensor_readings_seq existe
            [0],  # actuator_status_seq não existe
            [1],  # alarm_events_seq existe
        ]
        
        # Configura o comportamento para a verificação de colunas
        mock_cursor.fetchall.side_effect = [
            [("READING_ID",), ("TIMESTAMP",), ("TEMPERATURE",)],  # Colunas de sensor_readings
            [("EVENT_ID",), ("TIMESTAMP",), ("EVENT_TYPE",)]      # Colunas de alarm_events
        ]
        
        # Chama check_schema_exists
        result = oracle_storage.check_schema_exists()
        
        # Verifica se as consultas foram executadas
        assert mock_cursor.execute.call_count >= 6
        
        # Verifica o resultado
        assert result["sensor_readings"] is True
        assert result["actuator_status"] is False
        assert result["alarm_events"] is True
        assert result["sensor_readings_seq"] is True
        assert result["actuator_status_seq"] is False
        assert result["alarm_events_seq"] is True
        
    def test_oracle_identification(self, oracle_storage):
        """Testa se o Oracle Storage é identificável."""
        # Verifica se a instância existe
        assert oracle_storage is not None
        
        # Verifica se os atributos de conexão estão definidos
        assert hasattr(oracle_storage, 'username')
        assert hasattr(oracle_storage, 'password')
        assert hasattr(oracle_storage, 'dsn')
        
        # Verifica se o método de teste de conexão está disponível
        assert hasattr(oracle_storage, 'test_connection')
        
        # Verifica se o método de verificação de esquema está disponível
        assert hasattr(oracle_storage, 'check_schema_exists')
        
        # Configura o mock para simular uma conexão bem-sucedida
        mock_cursor = MagicMock()
        oracle_storage._connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]  # Simula resultado bem-sucedido
        
        # Verifica se o teste de conexão retorna True
        assert oracle_storage.test_connection() is True
        
    def test_connection_fix(self):
        """Testa o método test_connection_fix."""
        # Executa o teste de correção de conexão
        with patch('oracledb.connect') as mock_connect:
            # Configura o mock
            mock_connection = MagicMock()
            mock_connect.return_value = mock_connection
            
            # Configura o mock do cursor
            mock_cursor = MagicMock()
            mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
            mock_cursor.fetchone.return_value = ["Oracle Database 19c Enterprise Edition"]
            
            # Configura atributos da conexão
            mock_connection.autocommit = False
            
            # Executa o teste de correção
            result = OracleStorage.test_connection_fix()
            
            # Verifica se o resultado é True (teste passou)
            assert result is True
            
            # Verifica se connect foi chamado com os parâmetros corretos
            mock_connect.assert_called_once()




