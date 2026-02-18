import logging

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%m-%Y %H:%M:%S'
)

# Scraper configuration
DEFAULT_NUM_ANALYZERS = 1
MAX_URLS_TO_COLLECT = 1000
QUEUE_MAXSIZE = 10000
OUTPUT_JSONL_FILE_NAME = "output.jsonl"