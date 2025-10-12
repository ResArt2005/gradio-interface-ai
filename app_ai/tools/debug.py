import logging
import sys
import os
import json
from datetime import datetime
from typing import Optional, Literal, Dict, Any
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Кастомный форматтер для JSON логов"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирование записи лога в JSON"""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Добавляем дополнительные поля если есть
        if hasattr(record, 'extra_data'):
            log_entry["extra_data"] = record.extra_data
            
        # Добавляем информацию об исключении если есть
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_entry, ensure_ascii=False)

class SimpleLogger:
    """
    Универсальная мини-библиотека для логирования событий
    с поддержкой вывода в консоль или файл (JSON формат)
    """
    
    def __init__(
        self, 
        name: str = "AppLogger", 
        debug_mode: bool = False,
        output: Literal["console", "file"] = "console",
        log_file: Optional[str] = None,
        logs_dir: str = "logs",
        json_format: bool = False
    ):
        self.debug_mode = debug_mode
        self.name = name
        self.output = output
        self.logs_dir = Path(logs_dir)
        self.json_format = json_format
        
        # Создаем папку logs если она не существует и нужен вывод в файл
        if output == "file":
            self.logs_dir.mkdir(exist_ok=True)
            
            # Если имя файла не указано, генерируем автоматически
            if not log_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                extension = "json" if json_format else "log"
                log_file = f"{name}_{timestamp}.{extension}"
            else:
                # Если указано имя файла без расширения, добавляем правильное расширение
                if not Path(log_file).suffix:
                    extension = "json" if json_format else "log"
                    log_file = f"{log_file}.{extension}"
            
            self.log_file_path = self.logs_dir / log_file
        
        # Настройка форматтеров
        if json_format:
            self.formatter = JSONFormatter()
            self.console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            self.formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            self.console_formatter = self.formatter
        
        # Создаем логгер
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
        
        # Очищаем существующие обработчики
        self.logger.handlers.clear()
        
        # Настройка обработчиков в зависимости от выбранного вывода
        if output == "console":
            self._setup_console_handler()
        elif output == "file":
            self._setup_file_handler()
    
    def _setup_console_handler(self) -> None:
        """Настройка обработчика для вывода в консоль"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
        console_handler.setFormatter(self.console_formatter)
        self.logger.addHandler(console_handler)
        
        # Логируем информацию о запуске
        if self.json_format:
            self.logger.info(f"Логирование запущено (режим: {'DEBUG' if self.debug_mode else 'INFO'}, вывод: консоль, формат: JSON)")
        else:
            self.logger.info(f"Логирование запущено (режим: {'DEBUG' if self.debug_mode else 'INFO'}, вывод: консоль)")
    
    def _setup_file_handler(self) -> None:
        """Настройка обработчика для вывода в файл"""
        try:
            if self.json_format:
                # Для JSON используем обычный FileHandler, но с JSON форматтером
                file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
            else:
                file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
                
            file_handler.setLevel(logging.DEBUG if self.debug_mode else logging.INFO)
            file_handler.setFormatter(self.formatter)
            self.logger.addHandler(file_handler)
            
            # Логируем информацию о запуске
            format_info = "JSON" if self.json_format else "текст"
            self.logger.info(f"Логирование запущено (режим: {'DEBUG' if self.debug_mode else 'INFO'}, файл: {self.log_file_path}, формат: {format_info})")
            
        except Exception as e:
            # Если не удалось создать файловый обработчик, fallback на консоль
            print(f"Ошибка создания файлового логгера: {e}. Использую консольный вывод.")
            self._setup_console_handler()
    
    def switch_output(self, new_output: Literal["console", "file"], log_file: Optional[str] = None, json_format: Optional[bool] = None) -> None:
        """Переключение между выводом в консоль и файл"""
        if json_format is not None:
            self.json_format = json_format
            
        if new_output == self.output and not log_file:
            return
            
        self.output = new_output
        
        # Очищаем текущие обработчики
        self.logger.handlers.clear()
        
        # Обновляем путь к файлу если указан
        if log_file:
            if not Path(log_file).suffix:
                extension = "json" if self.json_format else "log"
                log_file = f"{log_file}.{extension}"
            self.log_file_path = self.logs_dir / log_file
        
        # Устанавливаем новые обработчики
        if new_output == "console":
            self._setup_console_handler()
        elif new_output == "file":
            self._setup_file_handler()
    
    def switch_json_format(self, json_format: bool) -> None:
        """Переключение между JSON и текстовым форматом"""
        if json_format == self.json_format:
            return
            
        self.json_format = json_format
        
        # Обновляем обработчики
        if self.output == "file":
            self.logger.handlers.clear()
            self._setup_file_handler()
    
    def log_with_extra(self, level: str, message: str, extra_data: Dict[str, Any] = None) -> None:
        """Логирование с дополнительными данными"""
        if extra_data is None:
            extra_data = {}
            
        # Создаем кастомную запись с дополнительными данными
        extra = {'extra_data': extra_data}
        
        if level == 'info':
            self.logger.info(message, extra=extra)
        elif level == 'error':
            self.logger.error(message, extra=extra)
        elif level == 'warning':
            self.logger.warning(message, extra=extra)
        elif level == 'debug':
            if self.debug_mode:  # Добавляем проверку для debug
                self.logger.debug(message, extra=extra)
        elif level == 'critical':
            self.logger.critical(message, extra=extra)
    
    def read_json_logs(self, limit: int = None) -> list[Dict[str, Any]]:
        """Чтение JSON логов из файла (только для JSON формата)"""
        if not self.json_format or self.output != "file":
            return []
            
        try:
            logs = []
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line.strip()))
            
            if limit:
                return logs[-limit:]
            return logs
            
        except Exception as e:
            self.logger.error(f"Ошибка чтения JSON логов: {e}")
            return []
    
    def get_log_file_path(self) -> Optional[Path]:
        """Получить путь к текущему файлу логов (если используется файловый вывод)"""
        return self.log_file_path if self.output == "file" else None
    
    def get_logs_directory(self) -> Path:
        """Получить путь к папке с логами"""
        return self.logs_dir
    
    def list_log_files(self) -> list[str]:
        """Получить список всех файлов логов в папке"""
        if not self.logs_dir.exists():
            return []
        return [f.name for f in self.logs_dir.glob("*.*") if f.is_file() and f.suffix in ['.log', '.json']]
    
    def cleanup_old_logs(self, days: int = 30) -> None:
        """Очистка старых логов (старше указанного количества дней)"""
        if not self.logs_dir.exists():
            return
            
        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for log_file in self.logs_dir.glob("*.*"):
            if log_file.suffix in ['.log', '.json'] and log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.warning(f"Не удалось удалить старый лог-файл {log_file}: {e}")
        
        if deleted_count > 0:
            self.info(f"Удалено старых лог-файлов: {deleted_count}")
    
    def info(self, message: str, *args, **kwargs) -> None:
        """Логирование информационного сообщения"""
        self.logger.info(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs) -> None:
        """Логирование ошибки"""
        self.logger.error(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs) -> None:
        """Логирование предупреждения"""
        self.logger.warning(message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs) -> None:
        """Логирование отладочной информации (только в debug режиме)"""
        if self.debug_mode:  # Полностью игнорируем вызов если не в debug режиме
            self.logger.debug(message, *args, **kwargs)
        # Если debug_mode = False, функция ничего не делает
    
    def critical(self, message: str, *args, **kwargs) -> None:
        """Логирование критической ошибки"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs) -> None:
        """Логирование исключения с трассировкой"""
        self.logger.exception(message, *args, **kwargs)
    
    def success(self, message: str, *args, **kwargs) -> None:
        """Логирование успешного события (кастомный уровень)"""
        if self.json_format:
            self.log_with_extra('info', message, {'type': 'success'})
        else:
            self.logger.info(f"✅ SUCCESS: {message}", *args, **kwargs)
    
    def start_timer(self) -> datetime:
        """Начать отсчет времени для измерения производительности"""
        return datetime.now()
    
    def end_timer(self, start_time: datetime, operation_name: str = "Operation") -> None:
        """Закончить отсчет времени и залогировать продолжительность"""
        if not self.debug_mode:  # Игнорируем таймеры если не в debug режиме
            return
            
        duration = (datetime.now() - start_time).total_seconds()
        if self.json_format:
            self.log_with_extra('debug', f"{operation_name} completed", {'duration': duration, 'operation': operation_name})
        else:
            self.debug(f"{operation_name} completed in {duration:.3f} seconds")

# Глобальные настройки
DEBUG = True
LOG_OUTPUT = "console"  # console/file
JSON_FORMAT = False     # True для JSON формата

# Создание глобального экземпляра логгера
logger = SimpleLogger(
    name="App", 
    debug_mode=DEBUG,
    output=LOG_OUTPUT,
    json_format=JSON_FORMAT,
    logs_dir="logs"
)

# Функции для обратной совместимости с вашим текущим кодом
def send_info(message: str, *args, **kwargs):
    """Аналог info для обратной совместимости"""
    logger.info(message, *args, **kwargs)

def send_error(message: str, *args, **kwargs):
    """Аналог error для обратной совместимости"""
    logger.error(message, *args, **kwargs)

def send_warning(message: str, *args, **kwargs):
    """Аналог warning для обратной совместимости"""
    logger.warning(message, *args, **kwargs)

def send_debug(message: str, *args, **kwargs):
    """Аналог debug для обратной совместимости"""
    logger.debug(message, *args, **kwargs)  # Будет игнорироваться если DEBUG = False