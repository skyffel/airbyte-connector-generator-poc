from datetime import datetime
from rich.table import Table
from rich.console import Console
import dotenv
import logging
import os

dotenv.load_dotenv()

logger = logging.getLogger('skyffel')

ch = logging.StreamHandler()

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()

logger.setLevel(LOG_LEVEL)
ch.setLevel(LOG_LEVEL)
logger.addHandler(ch)
