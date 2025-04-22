####################################
##### Arquivo: file_storage.py
##### Desenvolvedor: Juan F. Voltolini
##### Instituição: FIAP
##### Trabalho: Cap 6 - Python e Além
##### Grupo: Alexander Dorneles de Oliveira, Felipe Sabino da Silva, Juan Felipe Voltolini, Luiz Henrique Ribeiro de Oliveira e Marco Aurélio Eberhardt Assumpção
####################################

"""Implementação de armazenamento baseado em arquivos.

Este módulo manipula a leitura e escrita de dados em arquivos JSON e texto
para configuração e propósitos de log.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.config import AlertConfig, AlertSeverity, AlertType, EnvironmentalLimits, SystemConfig
from ..models.device import DeviceStatus, DeviceType, DeviceState
from ..models.sensor_data import SensorReading


logger = logging.getLogger(__name__)


def parse_sensor_reading(line: str) -> Optional[SensorReading]:
    """Analisa uma leitura de sensor a partir de uma linha de log.

    Args:
        line: Linha de log para analisar

    Returns:
        Optional[SensorReading]: Leitura analisada ou None se a análise falhar
    """
    try:
        parts = line.strip().split(",")
        # Pular linha de cabeçalho
        if parts[0].startswith("Timestamp"):
            return None

        # Lidar com formatos antigo (7 campos) e novo (9 campos)
        if len(parts) not in [7, 9]:
            logger.warning(f"Número inválido de campos na entrada de log: {line.strip()}")
            return None

        timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
        
        # Analisar campos numéricos primeiro para validá-los
        try:
            temp = float(parts[1])
            if len(parts) == 7:
                humidity = float(parts[2])
                co2 = float(parts[3])
                ammonia = float(parts[4])
                pressure = float(parts[5])
                ext_temp = temp  # Usar temperatura como temperatura externa
                sensor_id = parts[6].strip()
                power_ok = True  # Assumir energia OK para formato antigo
            else:  # Novo formato com 9 campos
                ext_temp = float(parts[2])
                humidity = float(parts[3])
                co2 = float(parts[4])
                ammonia = float(parts[5])
                pressure = float(parts[6])
                power_ok = parts[7].lower() == "true"
                sensor_id = parts[8].strip()
        except ValueError as ve:
            logger.warning(f"Valor numérico inválido na leitura do sensor: {ve}")
            return None

        # Criar objeto de leitura com valores validados
        return SensorReading(
            timestamp=timestamp,
            temperature=temp,
            external_temp=ext_temp,
            humidity=humidity,
            co2_level=co2,
            ammonia_level=ammonia,
            pressure=pressure,
            power_ok=power_ok,
            sensor_id=sensor_id
        )
    except Exception as e:
        logger.warning(f"Erro ao processar entrada de log: {e}")
        return None


class FileStorage:
    """Manipula operações de armazenamento de dados baseadas em arquivo."""

    def __init__(self, base_path: str = "data"):
        """Inicializa o armazenamento de arquivos.

        Args:
            base_path: Diretório base para arquivos de dados
        """
        self.base_path = Path(base_path)
        self.config_path = self.base_path / "config"
        self.logs_path = self.base_path / "logs"
        self._ensure_directories()

    def _ensure_directories(self):
        """Cria os diretórios necessários se não existirem."""
        self.base_path.mkdir(exist_ok=True)
        self.config_path.mkdir(exist_ok=True)
        self.logs_path.mkdir(exist_ok=True)

    def save_config(self, config: SystemConfig):
        """Salva a configuração do sistema em arquivo JSON.

        Args:
            config: Configuração do sistema para salvar
        """
        config_file = self.config_path / "system_config.json"
        
        # Usar o método to_dict da classe SystemConfig para obter todos os dados
        config_data = config.to_dict()
        
        try:
            with open(config_file, "w") as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Configuração salva em {config_file}")
        except Exception as e:
            logger.error(f"Falha ao salvar configuração: {e}")
            raise

    def load_config(self) -> Optional[SystemConfig]:
        """Carrega a configuração do sistema a partir de arquivo JSON.

        Returns:
            Optional[SystemConfig]: Configuração carregada ou None se arquivo não encontrado
        """
        config_file = self.config_path / "system_config.json"
        if not config_file.exists():
            return None

        try:
            with open(config_file) as f:
                config_data = json.load(f)

            # Usar o método from_dict da classe SystemConfig para criar a instância
            return SystemConfig.from_dict(config_data)
        except Exception as e:
            logger.error(f"Falha ao carregar configuração: {e}")
            return None

    def log_sensor_reading(self, reading: SensorReading):
        """Registra leitura de sensor em arquivo de log diário.

        Args:
            reading: Leitura de sensor para registrar
        """
        log_file = self.logs_path / f"readings_{datetime.now():%Y%m%d}.txt"
        log_entry = (
            f"{reading.timestamp:%Y-%m-%d %H:%M:%S},"
            f"{reading.temperature:.1f},"
            f"{reading.external_temp:.1f},"
            f"{reading.humidity:.1f},"
            f"{reading.co2_level:.0f},"
            f"{reading.ammonia_level:.1f},"
            f"{reading.pressure:.1f},"
            f"{str(reading.power_ok).lower()},"
            f"{reading.sensor_id}\n"
        )

        try:
            # Criar arquivo com cabeçalho se não existir
            if not log_file.exists():
                with open(log_file, "w") as f:
                    f.write("Timestamp,Temperature,External_Temp,Humidity,CO2,Ammonia,Pressure,Power_OK,Sensor_ID\n")

            # Adicionar leitura
            with open(log_file, "a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Falha ao registrar leitura do sensor: {e}")

    def log_device_status(self, status: DeviceStatus):
        """Registra mudança de status de dispositivo em arquivo de log diário.

        Args:
            status: Status do dispositivo para registrar
        """
        log_file = self.logs_path / f"devices_{datetime.now():%Y%m%d}.txt"
        log_entry = (
            f"{status.last_updated:%Y-%m-%d %H:%M:%S},"
            f"{status.device_id},"
            f"{status.device_type.name},"
            f"{status.state.name},"
            f"{status.value if status.value is not None else 'N/A'},"
            f"{status.error_message if status.error_message else 'OK'}\n"
        )

        try:
            with open(log_file, "a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Falha ao registrar status do dispositivo: {e}")

    def log_alarm(self, message: str, level: str = "ERROR"):
        """Registra evento de alarme em arquivo de log de alarmes.

        Args:
            message: Mensagem de alarme
            level: Nível de severidade do alarme
        """
        log_file = self.logs_path / "alarms.txt"
        log_entry = f"{datetime.now():%Y-%m-%d %H:%M:%S} [{level}] {message}\n"

        try:
            with open(log_file, "a") as f:
                f.write(log_entry)
        except Exception as e:
            logger.error(f"Falha ao registrar alarme: {e}")

    def get_recent_readings(self, hours: int = 24) -> List[SensorReading]:
        """Obtém leituras de sensor das últimas N horas.

        Args:
            hours: Número de horas para retroceder

        Returns:
            List[SensorReading]: Lista de objetos de leitura de sensor
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)
        readings = []

        # Obter todos os arquivos de leitura das últimas N horas
        log_files = sorted(
            self.logs_path.glob("readings_*.txt"),
            key=lambda x: x.stat().st_mtime,
            reverse=True,
        )

        for log_file in log_files:
            try:
                with open(log_file) as f:
                    # Pular linha de cabeçalho se presente
                    first_line = f.readline().strip()
                    if not first_line.startswith("20"):  # Se linha não começa com ano, é cabeçalho
                        pass  # Pular cabeçalho
                    else:
                        # Se primeira linha é dado, voltar ao início
                        f.seek(0)

                    for line in f:
                        # Pular linha de cabeçalho se encontrada
                        if line.strip().startswith("Timestamp"):
                            continue

                        parts = line.strip().split(",")
                        try:
                            # Lidar com formatos antigo (7 campos) e novo (9 campos)
                            if len(parts) not in [7, 9]:
                                logger.warning(f"Número inválido de campos na entrada de log: {line.strip()}")
                                continue

                            timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                            file_timestamp = timestamp.timestamp()
                            if file_timestamp < cutoff:
                                continue

                            # Analisar campos numéricos primeiro para validá-los
                            try:
                                temp = float(parts[1])
                                if len(parts) == 7:
                                    humidity = float(parts[2])
                                    co2 = float(parts[3])
                                    ammonia = float(parts[4])
                                    pressure = float(parts[5])
                                    ext_temp = temp  # Usar temperatura como temperatura externa
                                    sensor_id = parts[6].strip()
                                    power_ok = True  # Assumir energia OK para formato antigo
                                else:  # Novo formato com 9 campos
                                    ext_temp = float(parts[2])
                                    humidity = float(parts[3])
                                    co2 = float(parts[4])
                                    ammonia = float(parts[5])
                                    pressure = float(parts[6])
                                    power_ok = parts[7].lower() == "true"
                                    sensor_id = parts[8].strip()
                            except ValueError as ve:
                                logger.warning(f"Valor numérico inválido na leitura do sensor: {ve}")
                                continue

                            # Criar objeto de leitura com valores validados
                            reading = SensorReading(
                                timestamp=timestamp,
                                temperature=temp,
                                external_temp=ext_temp,
                                humidity=humidity,
                                co2_level=co2,
                                ammonia_level=ammonia,
                                pressure=pressure,
                                power_ok=power_ok,
                                sensor_id=sensor_id
                            )
                            readings.append(reading)
                        except Exception as e:
                            logger.warning(f"Erro ao processar entrada de log: {e}")
                            continue

            except Exception as e:
                logger.error(f"Erro ao ler arquivo de log {log_file}: {e}")

        return readings

    def edit_sensor_reading(self, timestamp: datetime, sensor_id: str, new_reading: SensorReading) -> bool:
        """Edita uma leitura de sensor existente.

        Args:
            timestamp: Timestamp da leitura a ser editada
            sensor_id: ID do sensor
            new_reading: Nova leitura para substituir a existente

        Returns:
            bool: True se a edição foi bem sucedida, False caso contrário
        """
        log_file = self.logs_path / f"readings_{timestamp:%Y%m%d}.txt"
        if not log_file.exists():
            return False

        try:
            # Ler arquivo existente
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Procurar e substituir a leitura
            found = False
            for i, line in enumerate(lines):
                parts = line.strip().split(',')
                line_timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                line_sensor_id = parts[8]

                if line_timestamp == timestamp and line_sensor_id == sensor_id:
                    # Substituir linha
                    lines[i] = (
                        f"{new_reading.timestamp:%Y-%m-%d %H:%M:%S},"
                        f"{new_reading.temperature:.1f},"
                        f"{new_reading.external_temp:.1f},"
                        f"{new_reading.humidity:.1f},"
                        f"{new_reading.co2_level:.0f},"
                        f"{new_reading.ammonia_level:.1f},"
                        f"{new_reading.pressure:.1f},"
                        f"{str(new_reading.power_ok).lower()},"
                        f"{new_reading.sensor_id}\n"
                    )
                    found = True
                    break

            if not found:
                return False

            # Reescrever arquivo
            with open(log_file, 'w') as f:
                f.writelines(lines)

            return True

        except Exception as e:
            logger.error(f"Erro ao editar leitura do sensor: {e}")
            return False

    def delete_sensor_reading(self, timestamp: datetime, sensor_id: str) -> bool:
        """Exclui uma leitura de sensor.

        Args:
            timestamp: Timestamp da leitura a ser excluída
            sensor_id: ID do sensor

        Returns:
            bool: True se a exclusão foi bem sucedida, False caso contrário
        """
        log_file = self.logs_path / f"readings_{timestamp:%Y%m%d}.txt"
        if not log_file.exists():
            return False

        try:
            # Ler arquivo existente
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Procurar e remover a leitura
            found = False
            new_lines = []
            for line in lines:
                parts = line.strip().split(',')
                line_timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                line_sensor_id = parts[8]

                if line_timestamp == timestamp and line_sensor_id == sensor_id:
                    found = True
                else:
                    new_lines.append(line)

            if not found:
                return False

            # Reescrever arquivo
            with open(log_file, 'w') as f:
                f.writelines(new_lines)

            return True

        except Exception as e:
            logger.error(f"Erro ao excluir leitura do sensor: {e}")
            return False

    def edit_device_status(self, timestamp: datetime, device_id: str, new_status: DeviceStatus) -> bool:
        """Edita um status de dispositivo existente.

        Args:
            timestamp: Timestamp do status a ser editado
            device_id: ID do dispositivo
            new_status: Novo status para substituir o existente

        Returns:
            bool: True se a edição foi bem sucedida, False caso contrário
        """
        log_file = self.logs_path / f"devices_{timestamp:%Y%m%d}.txt"
        if not log_file.exists():
            return False

        try:
            # Ler arquivo existente
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Procurar e substituir o status
            found = False
            for i, line in enumerate(lines):
                parts = line.strip().split(',')
                line_timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                line_device_id = parts[1]

                if line_timestamp == timestamp and line_device_id == device_id:
                    # Substituir linha
                    lines[i] = (
                        f"{new_status.last_updated:%Y-%m-%d %H:%M:%S},"
                        f"{new_status.device_id},"
                        f"{new_status.device_type.name},"
                        f"{new_status.state.name},"
                        f"{new_status.value if new_status.value is not None else 'N/A'},"
                        f"{new_status.error_message if new_status.error_message else 'OK'}\n"
                    )
                    found = True
                    break

            if not found:
                return False

            # Reescrever arquivo
            with open(log_file, 'w') as f:
                f.writelines(lines)

            return True

        except Exception as e:
            logger.error(f"Erro ao editar status do dispositivo: {e}")
            return False

    def delete_device_status(self, timestamp: datetime, device_id: str) -> bool:
        """Exclui um status de dispositivo.

        Args:
            timestamp: Timestamp do status a ser excluído
            device_id: ID do dispositivo

        Returns:
            bool: True se a exclusão foi bem sucedida, False caso contrário
        """
        log_file = self.logs_path / f"devices_{timestamp:%Y%m%d}.txt"
        if not log_file.exists():
            return False

        try:
            # Ler arquivo existente
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Procurar e remover o status
            found = False
            new_lines = []
            for line in lines:
                parts = line.strip().split(',')
                line_timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                line_device_id = parts[1]

                if line_timestamp == timestamp and line_device_id == device_id:
                    found = True
                else:
                    new_lines.append(line)

            if not found:
                return False

            # Reescrever arquivo
            with open(log_file, 'w') as f:
                f.writelines(new_lines)

            return True

        except Exception as e:
            logger.error(f"Erro ao excluir status do dispositivo: {e}")
            return False

    def edit_alarm(self, timestamp: datetime, old_message: str, new_message: str, new_level: str) -> bool:
        """Edita um alarme existente.

        Args:
            timestamp: Timestamp do alarme a ser editado
            old_message: Mensagem original do alarme
            new_message: Nova mensagem do alarme
            new_level: Novo nível do alarme

        Returns:
            bool: True se a edição foi bem sucedida, False caso contrário
        """
        log_file = self.logs_path / "alarms.txt"
        if not log_file.exists():
            return False

        try:
            # Ler arquivo existente
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Procurar e substituir o alarme
            found = False
            for i, line in enumerate(lines):
                parts = line.strip().split(" ", 3)
                line_timestamp = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y-%m-%d %H:%M:%S")
                line_message = parts[3]

                if line_timestamp == timestamp and line_message == old_message:
                    # Substituir linha
                    lines[i] = f"{timestamp:%Y-%m-%d %H:%M:%S} [{new_level}] {new_message}\n"
                    found = True
                    break

            if not found:
                return False

            # Reescrever arquivo
            with open(log_file, 'w') as f:
                f.writelines(lines)

            return True

        except Exception as e:
            logger.error(f"Erro ao editar alarme: {e}")
            return False

    def delete_alarm(self, timestamp: datetime, message: str) -> bool:
        """Exclui um alarme.

        Args:
            timestamp: Timestamp do alarme a ser excluído
            message: Mensagem do alarme

        Returns:
            bool: True se a exclusão foi bem sucedida, False caso contrário
        """
        log_file = self.logs_path / "alarms.txt"
        if not log_file.exists():
            return False

        try:
            # Ler arquivo existente
            with open(log_file, 'r') as f:
                lines = f.readlines()

            # Procurar e remover o alarme
            found = False
            new_lines = []
            for line in lines:
                parts = line.strip().split(" ", 3)
                line_timestamp = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y-%m-%d %H:%M:%S")
                line_message = parts[3]

                if line_timestamp == timestamp and line_message == message:
                    found = True
                else:
                    new_lines.append(line)

            if not found:
                return False

            # Reescrever arquivo
            with open(log_file, 'w') as f:
                f.writelines(new_lines)

            return True

        except Exception as e:
            logger.error(f"Erro ao excluir alarme: {e}")
            return False

    def get_recent_alarms(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtém alarmes das últimas N horas.

        Args:
            hours: Número de horas para retroceder

        Returns:
            List[Dict[str, Any]]: Lista de dicionários de alarme contendo timestamp, nível e mensagem
        """
        cutoff = datetime.now().timestamp() - (hours * 3600)
        alarms = []
        log_file = self.logs_path / "alarms.txt"

        if not log_file.exists():
            return []

        try:
            with open(log_file) as f:
                for line in f:
                    try:
                        # Analisar formato da linha de alarme: "YYYY-MM-DD HH:MM:SS [LEVEL] Message"
                        parts = line.strip().split(" ", 3)
                        timestamp = datetime.strptime(f"{parts[0]} {parts[1]}", "%Y-%m-%d %H:%M:%S")
                        
                        if timestamp.timestamp() < cutoff:
                            continue

                        level = parts[2].strip("[]")
                        message = parts[3]

                        alarm = {
                            "timestamp": timestamp,
                            "level": level,
                            "message": message
                        }
                        alarms.append(alarm)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Formato de alarme inválido na linha: {line.strip()}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Erro ao ler arquivo de log de alarmes: {e}")

        return sorted(alarms, key=lambda x: x["timestamp"], reverse=True)

    def get_available_days(self) -> List[datetime]:
        """Obtém a lista de dias com leituras disponíveis.

        Returns:
            List[datetime]: Lista de datas com leituras
        """
        days = []
        for log_file in self.logs_path.glob("readings_*.txt"):
            try:
                date_str = log_file.stem.split("_")[1]
                day = datetime.strptime(date_str, "%Y%m%d")
                days.append(day)
            except (ValueError, IndexError) as e:
                logger.warning(f"Formato inválido de nome de arquivo de log: {log_file.name}: {e}")
                continue

        return sorted(days, reverse=True)

    def get_readings_for_day(self, day: datetime) -> List[SensorReading]:
        """Obtém todas as leituras para um dia específico.

        Args:
            day: Data para buscar leituras

        Returns:
            List[SensorReading]: Lista de leituras do dia
        """
        log_file = self.logs_path / f"readings_{day:%Y%m%d}.txt"
        readings = []

        if not log_file.exists():
            return readings

        try:
            with open(log_file) as f:
                # Pular linha de cabeçalho se presente
                first_line = f.readline().strip()
                if not first_line.startswith("20"):  # Se linha não começa com ano, é cabeçalho
                    pass  # Pular cabeçalho
                else:
                    # Se primeira linha é dado, voltar ao início
                    f.seek(0)

                for line in f:
                    reading = parse_sensor_reading(line)
                    if reading is not None:
                        readings.append(reading)

        except Exception as e:
            logger.error(f"Erro ao ler arquivo de log {log_file}: {e}")

        return sorted(readings, key=lambda x: x.timestamp)

    def clear_history(self) -> bool:
        """Apaga todo o histórico de leituras.

        Returns:
            bool: True se a operação foi bem sucedida, False caso contrário
        """
        try:
            # Remover arquivos de leituras
            for log_file in self.logs_path.glob("readings_*.txt"):
                log_file.unlink()

            # Remover arquivos de dispositivos
            for log_file in self.logs_path.glob("devices_*.txt"):
                log_file.unlink()

            # Remover arquivo de alarmes
            alarm_file = self.logs_path / "alarms.txt"
            if alarm_file.exists():
                alarm_file.unlink()

            return True

        except Exception as e:
            logger.error(f"Erro ao apagar histórico: {e}")
            return False

    def get_latest_reading(self) -> Optional[SensorReading]:
        """Obtém a leitura mais recente do sensor.

        Returns:
            Optional[SensorReading]: Leitura mais recente do sensor ou None se não existirem leituras
        """
        # Obter o arquivo de leitura mais recente
        reading_files = sorted(
            self.logs_path.glob("readings_*.txt"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not reading_files:
            logger.warning("Nenhum log de leitura de sensor encontrado")
            return None

        latest_file = reading_files[0]
        latest_reading = None

        try:
            with open(latest_file) as f:
                # Ler todas as linhas e obter a última válida
                lines = f.readlines()
                for line in reversed(lines):  # Começar da última linha
                    reading = parse_sensor_reading(line)
                    if reading is not None:
                        latest_reading = reading
                        break

        except Exception as e:
            logger.error(f"Erro ao ler arquivo de leitura de sensor {latest_file}: {e}")
            return None

        return latest_reading

    def export_readings(self, day: datetime) -> bool:
        """Exporta as leituras de um dia específico para um arquivo CSV.

        Args:
            day: Data das leituras a serem exportadas

        Returns:
            bool: True se a exportação foi bem sucedida, False caso contrário
        """
        try:
            readings = self.get_readings_for_day(day)
            if not readings:
                logger.warning(f"Nenhuma leitura encontrada para {day:%Y-%m-%d}")
                return False

            export_dir = self.base_path / "exports"
            export_dir.mkdir(exist_ok=True)
            export_file = export_dir / f"readings_{day:%Y%m%d}_export.csv"

            with open(export_file, 'w') as f:
                # Escrever cabeçalho
                f.write("Timestamp,Temperature,External_Temp,Humidity,CO2,Ammonia,Pressure,Power_OK,Sensor_ID\n")
                
                # Escrever dados
                for reading in readings:
                    f.write(
                        f"{reading.timestamp:%Y-%m-%d %H:%M:%S},"
                        f"{reading.temperature:.1f},"
                        f"{reading.external_temp:.1f},"
                        f"{reading.humidity:.1f},"
                        f"{reading.co2_level:.0f},"
                        f"{reading.ammonia_level:.1f},"
                        f"{reading.pressure:.1f},"
                        f"{str(reading.power_ok).lower()},"
                        f"{reading.sensor_id}\n"
                    )

            logger.info(f"Leituras exportadas com sucesso para {export_file}")
            return True

        except Exception as e:
            logger.error(f"Erro ao exportar leituras: {e}")
            return False

    def export_all_readings(self) -> bool:
        """Exporta todas as leituras disponíveis.

        Returns:
            bool: True se a exportação foi bem sucedida, False caso contrário
        """
        try:
            days = self.get_available_days()
            if not days:
                logger.warning("Nenhuma leitura disponível para exportação")
                return False

            success = True
            for day in days:
                if not self.export_readings(day):
                    success = False
                    logger.error(f"Falha ao exportar leituras para {day:%Y-%m-%d}")

            return success

        except Exception as e:
            logger.error(f"Erro ao exportar todas as leituras: {e}")
            return False

    def import_readings(self, filepath: str) -> bool:
        """Importa leituras de um arquivo CSV.

        Args:
            filepath: Caminho do arquivo CSV a ser importado

        Returns:
            bool: True se a importação foi bem sucedida, False caso contrário
        """
        try:
            if not os.path.exists(filepath):
                logger.error(f"Arquivo de importação não encontrado: {filepath}")
                return False

            with open(filepath, 'r') as f:
                # Ler primeira linha para verificar se é cabeçalho
                first_line = f.readline().strip()
                if first_line.startswith("Timestamp"):
                    pass  # Pular cabeçalho
                else:
                    # Se primeira linha é dado, voltar ao início
                    f.seek(0)
                
                # Processar linhas de dados
                for line in f:
                    reading = parse_sensor_reading(line)
                    if reading is not None:
                        # Registrar a leitura importada
                        self.log_sensor_reading(reading)

            logger.info(f"Leituras importadas com sucesso de {filepath}")
            return True

        except Exception as e:
            logger.error(f"Erro ao importar leituras: {e}")
            return False

    def import_config(self, filepath: str) -> bool:
        """Importa configurações de um arquivo JSON.

        Args:
            filepath: Caminho do arquivo JSON a ser importado

        Returns:
            bool: True se a importação foi bem sucedida, False caso contrário
        """
        try:
            if not os.path.exists(filepath):
                logger.error(f"Arquivo de importação não encontrado: {filepath}")
                return False

            with open(filepath, 'r') as f:
                config_data = json.load(f)

            # Validar dados de configuração
            required_fields = [
                "environmental_limits",
                "reading_interval",
                "log_level",
                "alarm_enabled",
                "backup_power_threshold"
            ]
            
            for field in required_fields:
                if field not in config_data:
                    logger.error(f"Campo obrigatório faltando no arquivo de configuração: {field}")
                    return False

            # Criar objeto de configuração
            limits = EnvironmentalLimits(**config_data["environmental_limits"])
            config = SystemConfig(
                environmental_limits=limits,
                reading_interval=config_data["reading_interval"],
                log_level=config_data["log_level"],
                alarm_enabled=config_data["alarm_enabled"],
                backup_power_threshold=config_data["backup_power_threshold"]
            )

            # Salvar a configuração importada
            self.save_config(config)
            
            logger.info(f"Configuração importada com sucesso de {filepath}")
            return True

        except Exception as e:
            logger.error(f"Erro ao importar configuração: {e}")
            return False

    def create_backup(self, include_data: bool = True, include_config: bool = True) -> Optional[str]:
        """Cria um backup do sistema.

        Args:
            include_data: Se True, inclui dados históricos no backup
            include_config: Se True, inclui configurações no backup

        Returns:
            Optional[str]: Caminho do arquivo de backup criado, ou None se falhou
        """
        try:
            import shutil
            from datetime import datetime

            # Criar diretório de backup
            backup_dir = self.base_path / "backups"
            backup_dir.mkdir(exist_ok=True)

            # Criar diretório de backup com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"backup_{timestamp}"
            backup_path.mkdir()

            # Fazer backup da configuração se solicitado
            if include_config:
                config_backup = backup_path / "config"
                shutil.copytree(self.config_path, config_backup)

            # Fazer backup dos dados se solicitado
            if include_data:
                logs_backup = backup_path / "logs"
                shutil.copytree(self.logs_path, logs_backup)

            # Criar arquivo zip
            zip_path = str(backup_path) + ".zip"
            shutil.make_archive(str(backup_path), 'zip', str(backup_path))
            
            # Limpar diretório temporário
            shutil.rmtree(backup_path)

            logger.info(f"Backup criado com sucesso: {zip_path}")
            return zip_path

        except Exception as e:
            logger.error(f"Erro ao criar backup: {e}")
            return None

    def save_alert(self, alert: AlertConfig) -> bool:
        """Salva um alerta personalizado.

        Args:
            alert: Configuração do alerta para salvar

        Returns:
            bool: True se o alerta foi salvo com sucesso, False caso contrário
        """
        try:
            # Carregar configuração atual
            config = self.load_config()
            if not config:
                # Se não houver configuração, criar uma nova
                limits = EnvironmentalLimits(
                    temp_min=18.0,
                    temp_max=32.0,
                    humidity_min=50.0,
                    humidity_max=70.0,
                    co2_max=2000.0,
                    ammonia_max=25.0,
                    pressure_target=25.0
                )
                config = SystemConfig(environmental_limits=limits)
            
            # Adicionar ou atualizar o alerta
            existing_alert = config.get_alert(alert.alert_id)
            if existing_alert:
                config.update_alert(alert.alert_id, alert)
            else:
                config.add_alert(alert)
            
            # Salvar configuração atualizada
            self.save_config(config)
            logger.info(f"Alerta {alert.alert_id} salvo com sucesso")
            return True
        except Exception as e:
            logger.error(f"Falha ao salvar alerta: {e}")
            return False
    
    def delete_alert(self, alert_id: str) -> bool:
        """Remove um alerta personalizado.

        Args:
            alert_id: ID do alerta a ser removido

        Returns:
            bool: True se o alerta foi removido com sucesso, False caso contrário
        """
        try:
            # Carregar configuração atual
            config = self.load_config()
            if not config:
                return False
            
            # Remover o alerta
            if config.remove_alert(alert_id):
                # Salvar configuração atualizada
                self.save_config(config)
                logger.info(f"Alerta {alert_id} removido com sucesso")
                return True
            else:
                logger.warning(f"Alerta {alert_id} não encontrado")
                return False
        except Exception as e:
            logger.error(f"Falha ao remover alerta: {e}")
            return False
    
    def get_alerts(self) -> List[AlertConfig]:
        """Obtém todos os alertas personalizados.

        Returns:
            List[AlertConfig]: Lista de alertas personalizados
        """
        try:
            # Carregar configuração atual
            config = self.load_config()
            if not config:
                return []
            
            return config.custom_alerts
        except Exception as e:
            logger.error(f"Falha ao obter alertas: {e}")
            return []
    
    def get_alert(self, alert_id: str) -> Optional[AlertConfig]:
        """Obtém um alerta personalizado pelo ID.

        Args:
            alert_id: ID do alerta a ser obtido

        Returns:
            Optional[AlertConfig]: Configuração do alerta ou None se não encontrado
        """
        try:
            # Carregar configuração atual
            config = self.load_config()
            if not config:
                return None
            
            return config.get_alert(alert_id)
        except Exception as e:
            logger.error(f"Falha ao obter alerta: {e}")
            return None
    
    def set_persistence_mode(self, mode: str) -> bool:
        """Define o modo de persistência dos dados.

        Args:
            mode: Modo de persistência ("local", "oracle", "auto")

        Returns:
            bool: True se o modo foi definido com sucesso, False caso contrário
        """
        try:
            # Validar o modo
            if mode.lower() not in {"local", "oracle", "auto"}:
                logger.error(f"Modo de persistência inválido: {mode}")
                return False
            
            # Carregar configuração atual
            config = self.load_config()
            if not config:
                # Se não houver configuração, criar uma nova
                limits = EnvironmentalLimits(
                    temp_min=18.0,
                    temp_max=32.0,
                    humidity_min=50.0,
                    humidity_max=70.0,
                    co2_max=2000.0,
                    ammonia_max=25.0,
                    pressure_target=25.0
                )
                config = SystemConfig(environmental_limits=limits)
            
            # Definir o modo de persistência
            config.persistence_mode = mode.lower()
            
            # Salvar configuração atualizada
            self.save_config(config)
            logger.info(f"Modo de persistência definido para {mode}")
            return True
        except Exception as e:
            logger.error(f"Falha ao definir modo de persistência: {e}")
            return False
    
    def get_persistence_mode(self) -> str:
        """Obtém o modo de persistência dos dados.

        Returns:
            str: Modo de persistência atual ("local", "oracle", "auto")
        """
        try:
            # Carregar configuração atual
            config = self.load_config()
            if not config:
                return "auto"  # Valor padrão
            
            return config.persistence_mode
        except Exception as e:
            logger.error(f"Falha ao obter modo de persistência: {e}")
            return "auto"  # Valor padrão em caso de erro
    
    def restore_default_config(self) -> bool:
        """Restaura as configurações padrão do sistema.

        Returns:
            bool: True se a restauração foi bem sucedida, False caso contrário
        """
        try:
            # Criar configuração padrão
            limits = EnvironmentalLimits(
                temp_min=18.0,
                temp_max=32.0,
                humidity_min=50.0,
                humidity_max=70.0,
                co2_max=2000.0,
                ammonia_max=25.0,
                pressure_target=25.0
            )
            
            config = SystemConfig(
                environmental_limits=limits,
                reading_interval=300,  # 5 minutos
                log_level="INFO",
                alarm_enabled=True,
                backup_power_threshold=0.2  # 20%
            )

            # Salvar configuração padrão
            self.save_config(config)
            
            logger.info("Configuração padrão restaurada com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao restaurar configuração padrão: {e}")
            return False

    def clear_all_data(self) -> bool:
        """Apaga todos os dados do sistema, incluindo configurações.

        Returns:
            bool: True se a operação foi bem sucedida, False caso contrário
        """
        try:
            # Limpar histórico primeiro
            if not self.clear_history():
                return False

            # Remover arquivos de configuração
            for config_file in self.config_path.glob("*"):
                config_file.unlink()

            logger.info("Todos os dados do sistema foram apagados com sucesso")
            return True

        except Exception as e:
            logger.error(f"Erro ao limpar dados do sistema: {e}")
            return False

    def get_device_status(self) -> List[DeviceStatus]:
        """Obtém o status atual de todos os dispositivos das entradas de log mais recentes.

        Returns:
            List[DeviceStatus]: Lista de objetos de status de dispositivo atuais
        """
        # Obter o arquivo de log de dispositivos mais recente
        device_files = sorted(
            self.logs_path.glob("devices_*.txt"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if not device_files:
            logger.warning("Nenhum log de status de dispositivo encontrado")
            return []

        latest_file = device_files[0]
        latest_statuses = {}  # Dicionário para manter apenas o status mais recente por dispositivo

        try:
            with open(latest_file) as f:
                for line in f:
                    try:
                        parts = line.strip().split(",")
                        timestamp = datetime.strptime(parts[0], "%Y-%m-%d %H:%M:%S")
                        device_id = parts[1]
                        device_type = DeviceType[parts[2]]
                        state = DeviceState[parts[3]]
                        value = None if parts[4] == "N/A" else float(parts[4])
                        error_message = None if parts[5] == "OK" else parts[5]

                        status = DeviceStatus(
                            device_id=device_id,
                            device_type=device_type,
                            state=state,
                            value=value,
                            last_updated=timestamp,
                            error_message=error_message
                        )

                        # Manter apenas o status mais recente para cada dispositivo
                        if device_id not in latest_statuses or \
                           timestamp > latest_statuses[device_id].last_updated:
                            latest_statuses[device_id] = status

                    except (ValueError, IndexError, KeyError) as e:
                        logger.warning(f"Formato de status de dispositivo inválido na linha: {line.strip()}: {e}")
                        continue

        except Exception as e:
            logger.error(f"Erro ao ler arquivo de status de dispositivo {latest_file}: {e}")
            return []

        return list(latest_statuses.values())



