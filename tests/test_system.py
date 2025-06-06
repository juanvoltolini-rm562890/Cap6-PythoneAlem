####################################
##### Arquivo: test_system.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""Testes unitários para o sistema de controle de aviário."""
import pytest
from unittest.mock import MagicMock, patch

from main import AviaryControlSystem
from src.storage.oracle_db import OracleStorage


class TestAviaryControlSystem:
    """Casos de teste para a classe AviaryControlSystem."""

    @pytest.fixture
    def mock_oracle_storage(self):
        """Cria um mock para OracleStorage."""
        with patch('src.storage.oracle_db.OracleStorage') as mock_class:
            # Configura o mock para retornar uma instância simulada
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            # Configura o comportamento dos métodos
            mock_instance.connect.return_value = None
            mock_instance.test_connection.return_value = True
            mock_instance.check_schema_exists.return_value = {
                "sensor_readings": True,
                "actuator_status": True,
                "alarm_events": True,
                "sensor_readings_seq": True,
                "actuator_status_seq": True,
                "alarm_events_seq": True
            }
            
            yield mock_class

    @pytest.fixture
    def mock_file_storage(self):
        """Cria um mock para FileStorage."""
        with patch('src.storage.file_storage.FileStorage') as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            yield mock_class

    def test_init_with_oracle_enabled(self, mock_oracle_storage, mock_file_storage):
        """Testa a inicialização do sistema com Oracle habilitado."""
        # Configura o mock do OracleStorage
        mock_oracle_instance = mock_oracle_storage.return_value
        
        # Inicializa o sistema com Oracle habilitado
        system = AviaryControlSystem(use_oracle=True)
        
        # Verifica se o OracleStorage foi inicializado
        mock_oracle_storage.assert_called_once()
        
        # Verifica se os métodos do OracleStorage foram chamados
        mock_oracle_instance.connect.assert_called_once()
        mock_oracle_instance.test_connection.assert_called_once()
        mock_oracle_instance.check_schema_exists.assert_called_once()
        
        # Verifica se o oracle_storage foi configurado corretamente
        assert system.oracle_storage is not None
        assert system.oracle_storage == mock_oracle_instance

    def test_init_with_oracle_disabled(self, mock_oracle_storage, mock_file_storage):
        """Testa a inicialização do sistema com Oracle desabilitado."""
        # Inicializa o sistema com Oracle desabilitado
        system = AviaryControlSystem(use_oracle=False)
        
        # Verifica se o OracleStorage não foi inicializado
        mock_oracle_storage.assert_not_called()
        
        # Verifica se o oracle_storage é None
        assert system.oracle_storage is None

    def test_init_with_oracle_connection_failure(self, mock_oracle_storage, mock_file_storage):
        """Testa a inicialização do sistema quando a conexão Oracle falha."""
        # Configura o mock do OracleStorage para simular falha na conexão
        mock_oracle_instance = mock_oracle_storage.return_value
        mock_oracle_instance.test_connection.return_value = False
        
        # Inicializa o sistema com Oracle habilitado
        system = AviaryControlSystem(use_oracle=True)
        
        # Verifica se o OracleStorage foi inicializado
        mock_oracle_storage.assert_called_once()
        
        # Verifica se os métodos do OracleStorage foram chamados
        mock_oracle_instance.connect.assert_called_once()
        mock_oracle_instance.test_connection.assert_called_once()
        
        # Verifica se o oracle_storage é None devido à falha na conexão
        assert system.oracle_storage is None

    def test_init_with_oracle_exception(self, mock_oracle_storage, mock_file_storage):
        """Testa a inicialização do sistema quando ocorre uma exceção ao conectar ao Oracle."""
        # Configura o mock do OracleStorage para lançar uma exceção
        mock_oracle_instance = mock_oracle_storage.return_value
        mock_oracle_instance.connect.side_effect = Exception("Erro de conexão")
        
        # Inicializa o sistema com Oracle habilitado
        system = AviaryControlSystem(use_oracle=True)
        
        # Verifica se o OracleStorage foi inicializado
        mock_oracle_storage.assert_called_once()
        
        # Verifica se o método connect foi chamado
        mock_oracle_instance.connect.assert_called_once()
        
        # Verifica se o oracle_storage é None devido à exceção
        assert system.oracle_storage is None
        
    def test_configure_oracle_success(self, mock_oracle_storage, mock_file_storage):
        """Testa o método configure_oracle quando a conexão é bem-sucedida."""
        # Configura o mock do OracleStorage
        mock_oracle_instance = mock_oracle_storage.return_value
        mock_oracle_instance.test_connection.return_value = True
        mock_oracle_instance.check_schema_exists.return_value = {
            "sensor_readings": True,
            "actuator_status": True,
            "alarm_events": True,
            "reading_seq": True,
            "status_seq": True,
            "event_seq": True
        }
        
        # Inicializa o sistema com Oracle desabilitado
        system = AviaryControlSystem(use_oracle=False)
        
        # Configura Oracle
        result = system.configure_oracle("test_user", "test_password", "test_dsn")
        
        # Verifica se o OracleStorage foi inicializado com os parâmetros corretos
        mock_oracle_storage.assert_called_once_with("test_user", "test_password", "test_dsn")
        
        # Verifica se os métodos do OracleStorage foram chamados
        mock_oracle_instance.connect.assert_called_once()
        mock_oracle_instance.test_connection.assert_called_once()
        mock_oracle_instance.check_schema_exists.assert_called_once()
        
        # Verifica se o resultado é True
        assert result is True
        
        # Verifica se o oracle_storage foi configurado corretamente
        assert system.oracle_storage is not None
        assert system.oracle_storage == mock_oracle_instance
        
        # Verifica se using_mock_data é False
        assert system.using_mock_data is False
        
    def test_configure_oracle_connection_failure(self, mock_oracle_storage, mock_file_storage):
        """Testa o método configure_oracle quando a conexão falha."""
        # Configura o mock do OracleStorage para simular falha na conexão
        mock_oracle_instance = mock_oracle_storage.return_value
        mock_oracle_instance.test_connection.return_value = False
        
        # Inicializa o sistema com Oracle desabilitado
        system = AviaryControlSystem(use_oracle=False)
        
        # Configura Oracle
        result = system.configure_oracle("test_user", "test_password", "test_dsn")
        
        # Verifica se o OracleStorage foi inicializado com os parâmetros corretos
        mock_oracle_storage.assert_called_once_with("test_user", "test_password", "test_dsn")
        
        # Verifica se os métodos do OracleStorage foram chamados
        mock_oracle_instance.connect.assert_called_once()
        mock_oracle_instance.test_connection.assert_called_once()
        
        # Verifica se o resultado é False
        assert result is False
        
        # Verifica se using_mock_data é True
        assert system.using_mock_data is True
        
    def test_configure_oracle_schema_incomplete(self, mock_oracle_storage, mock_file_storage):
        """Testa o método configure_oracle quando o esquema está incompleto."""
        # Configura o mock do OracleStorage
        mock_oracle_instance = mock_oracle_storage.return_value
        mock_oracle_instance.test_connection.return_value = True
        mock_oracle_instance.check_schema_exists.return_value = {
            "sensor_readings": True,
            "actuator_status": False,  # Tabela ausente
            "alarm_events": True,
            "reading_seq": True,
            "status_seq": True,
            "event_seq": True
        }
        
        # Configura o mock para initialize_schema
        with patch('db.setup_db.initialize_schema') as mock_initialize:
            # Configura o mock para retornar True (sucesso)
            mock_initialize.return_value = True
            
            # Inicializa o sistema com Oracle desabilitado
            system = AviaryControlSystem(use_oracle=False)
            
            # Configura Oracle
            result = system.configure_oracle("test_user", "test_password", "test_dsn")
            
            # Verifica se initialize_schema foi chamado
            mock_initialize.assert_called_once_with("test_user", "test_password", "test_dsn")
            
            # Verifica se o resultado é True
            assert result is True
            
            # Verifica se using_mock_data é False
            assert system.using_mock_data is False
