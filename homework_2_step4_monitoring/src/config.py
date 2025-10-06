import yaml
from pathlib import Path
from typing import Any, Dict

CONFIG_PATH = Path("config/monitoring_config.yaml")

class Config:
    """Класс для загрузки и хранения конфигурации мониторинга."""

    def __init__(self, config_path: Path = CONFIG_PATH):
        self.config_path = config_path
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self):
        """Загружает конфигурацию из YAML файла."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")

        print(f"Загрузка конфигурации из {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            self._data = yaml.safe_load(f)
        print("Конфигурация загружена успешно.")

    @property
    def service(self) -> dict:
        return self._data.get("service", {})

    @property
    def monitoring(self) -> dict:
        return self._data.get("monitoring", {})

    @property
    def thresholds(self) -> dict:
        return self._data.get("thresholds", {})

    @property
    def alerts(self) -> dict:
        return self._data.get("alerts", {})

    @property
    def logging(self) -> dict:
        return self._data.get("logging", {})

# Экземпляр конфигурации, доступный для импорта
try:
    MONITORING_CONFIG = Config()
except FileNotFoundError as e:
    print(f"Критическая ошибка: {e}")
    MONITORING_CONFIG = None