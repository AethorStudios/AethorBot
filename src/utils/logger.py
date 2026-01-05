import logging
import os
from logging.handlers import RotatingFileHandler

from src.config import ConfigModel


def setup_logging(config: ConfigModel, level: int = logging.INFO) -> None:
    logging.basicConfig(level=level, format="[%(asctime)s] %(levelname)s:%(name)s: %(message)s")

    if config.file_logs.enabled:
        try:
            os.makedirs(os.path.dirname(config.file_logs.path), exist_ok=True)
            file_handler = RotatingFileHandler(
                config.file_logs.path, maxBytes=config.file_logs.max_bytes, backupCount=config.file_logs.backup_count
            )
            file_handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s:%(name)s: %(message)s"))
            root_logger = logging.getLogger()
            # Avoid adding multiple duplicate handlers if called twice
            if not any(
                isinstance(h, RotatingFileHandler) and h.baseFilename == file_handler.baseFilename
                for h in root_logger.handlers
            ):
                root_logger.addHandler(file_handler)
        except Exception as e:  # pragma: no cover
            logging.getLogger("Aethor").warning(f"Failed to enable file logging: {e}")
