import asyncio
import time
import logging

from scraper import AvitoScraper
import config

async def main():
    logger = logging.getLogger(__name__)
    start_time = time.time()

    scraper = AvitoScraper(num_analyzers=config.DEFAULT_NUM_ANALYZERS) 
    await scraper.run()

    end_time = time.time()
    execution_time = end_time - start_time

    hours = int(execution_time // 3600)
    minutes = int((execution_time % 3600) // 60)
    seconds = execution_time % 60
    logger.info(f"Program executed in {hours}h {minutes}m {seconds:.2f}s")

if __name__ == "__main__":
    asyncio.run(main())