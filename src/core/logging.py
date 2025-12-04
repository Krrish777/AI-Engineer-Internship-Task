import os
import logging
from datetime import datetime
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
            # Create file handler
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            # Create console handler  
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            # Configure root logger
            root_logger = logging.getLogger()
            root_logger.setLevel(logging.INFO)
            root_logger.addHandler(file_handler)
            root_logger.addHandler(console_handler)
            
            # Configure structlog
            structlog.configure(
                processors=[
                    structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
                    structlog.processors.add_log_level,
                    structlog.processors.EventRenamer("message"),
                    structlog.processors.JSONRenderer()
                ],
                logger_factory=structlog.stdlib.LoggerFactory(),
                cache_logger_on_first_use=True,
            )
            
            self._configured = True
            
        return structlog.get_logger()