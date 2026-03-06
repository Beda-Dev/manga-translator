"""
Configuration du système de logs.
Logs structurés avec émojis pour faciliter le débogage.
"""

import logging
import sys
from typing import Any


class ColorFormatter(logging.Formatter):
    """Formatter avec couleurs et émojis pour la console."""

    FORMATS = {
        logging.DEBUG:    "🔍 %(asctime)s [DEBUG]   %(name)s: %(message)s",
        logging.INFO:     "ℹ️  %(asctime)s [INFO]    %(name)s: %(message)s",
        logging.WARNING:  "⚠️  %(asctime)s [WARNING] %(name)s: %(message)s",
        logging.ERROR:    "❌ %(asctime)s [ERROR]   %(name)s: %(message)s",
        logging.CRITICAL: "🔥 %(asctime)s [CRITICAL] %(name)s: %(message)s",
    }

    def format(self, record: Any) -> str:
        fmt = self.FORMATS.get(record.levelno, self.FORMATS[logging.INFO])
        formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
        return formatter.format(record)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure le système de logs global."""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Handler console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter())
    root_logger.addHandler(console_handler)

    # Réduire le bruit des libs externes
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)