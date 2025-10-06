import logging
import json
import sys
from datetime import datetime
from pathlib import Path

# LOGGER_INITIALIZED = False

# ANSI Color Codes
COLORS = {
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "RED": "\033[91m",
    "BLUE": "\033[94m",
    "CYAN": "\033[96m",
    "MAGENTA": "\033[95m",
    "ENDC": "\033[0m",
}

class JsonFormatter(logging.Formatter):
    """Форматтер для логирования в JSON."""
    def format(self, record):
        log_record = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        
        # Добавляем любые дополнительные атрибуты, если они есть
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                           'filename', 'module', 'exc_info', 'exc_text', 'stack_info', 
                           'lineno', 'funcName', 'created', 'msecs', 'relativeCreated', 
                           'thread', 'threadName', 'process', 'message'] and not key.startswith('_'):
                log_record[key] = value

        return json.dumps(log_record, ensure_ascii=False)


def setup_logger(log_file: str, console_colors: bool):
    """Настройка основного логгера."""
    Path("logs").mkdir(exist_ok=True) # Убедимся, что папка logs существует

    logger = logging.getLogger("Monitor")
    logger.setLevel(logging.INFO)

    # 1. Файловый хэндлер (JSON)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    # 2. Консольный хэндлер (Цветной)
    console_handler = logging.StreamHandler(sys.stdout)
    
    if console_colors:
        class ColorFormatter(logging.Formatter):
            """Цветной форматтер для консоли."""
            FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
            
            LEVEL_COLORS = {
                logging.INFO: COLORS["GREEN"],
                logging.WARNING: COLORS["YELLOW"],
                logging.ERROR: COLORS["RED"],
                logging.CRITICAL: COLORS["RED"] + COLORS["MAGENTA"],
            }
            
            def format(self, record):
                log_fmt = self.FORMAT
                color = self.LEVEL_COLORS.get(record.levelno, COLORS["ENDC"])
                
                # Добавляем цвет в начало и сбрасываем в конце
                formatter = logging.Formatter(color + log_fmt + COLORS["ENDC"], "%Y-%m-%d %H:%M:%S")
                return formatter.format(record)

        console_handler.setFormatter(ColorFormatter())
    else:
        console_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"))

    logger.addHandler(console_handler)

    return logger

# Заглушка, если конфигурация не загрузилась, чтобы не падать
try:
    from .config import MONITORING_CONFIG
    LOG_FILE = MONITORING_CONFIG.logging["log_file"]
    CONSOLE_COLORS = MONITORING_CONFIG.logging["console_colors"]
    
    # Инициализация логгера
    LOGGER = setup_logger(LOG_FILE, CONSOLE_COLORS)
    
    # Настройка специального хэндлера для метрик (JSONL)
    METRICS_FILE = MONITORING_CONFIG.logging["metrics_file"]
    metrics_handler = logging.FileHandler(METRICS_FILE, encoding='utf-8')
    metrics_handler.setFormatter(JsonFormatter())
    
    METRICS_LOGGER = logging.getLogger("Metrics")
    METRICS_LOGGER.setLevel(logging.INFO)
    METRICS_LOGGER.addHandler(metrics_handler)
    METRICS_LOGGER.propagate = False # Отключаем вывод метрик в основной лог и консоль

except Exception as e:
    # Запасной вариант
    print(f"Ошибка инициализации логгера: {e}. Используется стандартный логгер.")
    LOGGER = logging.getLogger("Monitor")
    LOGGER.setLevel(logging.INFO)
    LOGGER.addHandler(logging.StreamHandler(sys.stdout))
    METRICS_LOGGER = LOGGER # Заглушка для метрик

# def flush_metrics_logger():
#     """Принудительно сбрасывает буфер файловых хэндлеров метрик, чтобы обеспечить запись на диск."""
#     if LOGGER_INITIALIZED:
#         for handler in METRICS_LOGGER.handlers:
#             if isinstance(handler, logging.FileHandler):
#                 handler.flush()