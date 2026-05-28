import logging
from datetime import datetime

def setup_logging(exp_name: str, level=logging.INFO):
    if exp_name:
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_filename = f"./logs/{exp_name}_{date_str}.log"
    else:
        log_filename = datetime.now().strftime("./logs/run_%Y-%m-%d.log")
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )