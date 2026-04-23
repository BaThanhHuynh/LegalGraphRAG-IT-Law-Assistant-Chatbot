import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_logger(name="it_law_chatbot"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Tránh lặp log nếu logger đã được setup
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 2. File Handler (Tự động xoay file khi đạt 5MB)
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

# Singleton logger instance
logger = setup_logger()
