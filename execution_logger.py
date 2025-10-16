import logging
import sys
from pathlib import Path
from datetime import datetime
from config import Config

def setup_logging():
    log_dir = Path(Config.LOGS_DIR)
    log_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"automation_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
