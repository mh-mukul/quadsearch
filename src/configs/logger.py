import os
import logging
from dotenv import load_dotenv
from logging.handlers import TimedRotatingFileHandler

load_dotenv()
LOG_DIR = os.environ.get("LOG_DIR", "./logs")
if not os.path.exists(LOG_DIR):
    os.mkdir(LOG_DIR)

log_file = f"{LOG_DIR}/app.log"

# Configure the root logger first
logging.basicConfig(level=logging.INFO)

# Create our app logger instance
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)

# Remove any existing handlers to prevent duplication
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Add file handler
file_handler = TimedRotatingFileHandler(
    log_file, when="midnight", interval=1, backupCount=7)

formatter = logging.Formatter(
    "%(asctime)s - %(funcName)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
# Prevent logs from being propagated to the root logger (console)
logger.propagate = False

# Also ensure root logger doesn't output to console
root_logger = logging.getLogger()
root_logger.handlers = []
root_logger.addHandler(file_handler)
