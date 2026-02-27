import logging
import os

os.makedirs('logs', exist_ok=True)

def setup_logger(name, log_file, level=logging.INFO):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        logger.addHandler(handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

download_logger = setup_logger('download', 'logs/downloads.log')
metadata_logger = setup_logger('metadata', 'logs/metadata.log')
connection_logger = setup_logger('connection', 'logs/connections.log')
