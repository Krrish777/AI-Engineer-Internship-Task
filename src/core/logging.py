import logging
from pathlib import Path
import structlog

class CustomLogger:
    def __init__(self, name: str, log_file: str | Path | None = None, log_file_name: str = "app.log"):
        default_root = Path(__file__).resolve().parents[2]
        self.logs_dir = Path(log_file) if log_file else default_root / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.log_file_path = self.logs_dir / log_file_name
        self._configured = False
        
    def get_logger(self):
        if not self._configured:
            # Clear any existing handlers to avoid duplicates
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)
            
            # Create file handler for JSON logs
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.INFO)
            
            # Create console handler for simple logs
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            # Configure structlog for JSON file output only
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
                    structlog.processors.add_log_level,
                    structlog.processors.EventRenamer("message"),
                    structlog.processors.JSONRenderer()
                ],
                logger_factory=structlog.stdlib.LoggerFactory(),
                wrapper_class=structlog.stdlib.BoundLogger,
                cache_logger_on_first_use=True,
            )
            
            # Add only file handler to structlog's logger
            structlog_logger = logging.getLogger()
            structlog_logger.setLevel(logging.INFO)
            structlog_logger.addHandler(file_handler)
            
            # Add only console handler to a separate logger for console output
            console_logger = logging.getLogger('console')
            console_logger.setLevel(logging.INFO) 
            console_logger.addHandler(console_handler)
            
            self._configured = True
            
        # Return a custom logger that writes to both console and file differently
        return ConsoleFileLogger()
    
class ConsoleFileLogger:
    def __init__(self):
        self.struct_logger = structlog.get_logger()
        self.console_logger = logging.getLogger('console')
    
    def info(self, message, **kwargs):
        self.console_logger.info(message)
        self.struct_logger.info(message, **kwargs)
    
    def warning(self, message, **kwargs):
        self.console_logger.warning(message)
        self.struct_logger.warning(message, **kwargs)
        
    def error(self, message, **kwargs):
        self.console_logger.error(message)
        self.struct_logger.error(message, **kwargs)
    
    def debug(self, message, **kwargs):
        self.console_logger.debug(message)
        self.struct_logger.debug(message, **kwargs)