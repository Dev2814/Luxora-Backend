import logging
from logging.handlers import RotatingFileHandler
import os

# --------------------------------------------------
# LOG DIRECTORY
# --------------------------------------------------

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "luxora.log")


# --------------------------------------------------
# SETUP LOGGING
# --------------------------------------------------

def setup_logging():

    logger = logging.getLogger()

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # ------------------------------------------
    # CONSOLE HANDLER
    # ------------------------------------------

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ------------------------------------------
    # FILE HANDLER (ROTATING)
    # ------------------------------------------

    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding="utf-8"
    )

    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # ------------------------------------------
    # ADD HANDLERS
    # ------------------------------------------

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.propagate = False

    logger.info("Logging system initialized")

    return logger