import asyncio
import logging

import config
from grabber import AvitoItemsURLGrabber
from analyzer import AvitoItemsAnalyzer

class AvitoScraper:
    def __init__(self, num_analyzers: int = config.DEFAULT_NUM_ANALYZERS):
        self.grabber = AvitoItemsURLGrabber()
        self.analyzers = []
        self.url_queue = asyncio.Queue(maxsize=config.QUEUE_MAXSIZE)
        self.stop_event = asyncio.Event()
        self.num_analyzers = num_analyzers
        self.logger = logging.getLogger(__name__)

        # Create analyzer instances with unique IDs
        for i in range(num_analyzers):
            self.analyzers.append(AvitoItemsAnalyzer(analyzer_id=i + 1))
    
    async def run(self):
        """
        Run grabber and multiple analyzers concurrently
        """
        self.logger.info(f"Starting Avito Scraper with {self.num_analyzers} analyzers...")
        
        # Create list to hold all tasks
        tasks = []
        
        # Add grabber task
        tasks.append(asyncio.create_task(
            self.grabber.fetch_urls(self.url_queue, self.stop_event),
            name="Grabber"
        ))
        
        # Add analyzer tasks
        for analyzer in self.analyzers:
            task = asyncio.create_task(
                analyzer.process_urls(self.url_queue, self.stop_event),
                name=f"Analyzer-{analyzer.analyzer_id}"
            )
            tasks.append(task)
        
        # Run until we hit the URLs limit
        try:
            # Monitor progress
            while self.grabber.url_counter < config.MAX_URLS_TO_COLLECT:
                await asyncio.sleep(1)
                
                queue_size = self.url_queue.qsize()
                self.logger.info(f"Progress: {self.grabber.url_counter} URLs found, Queue: {queue_size}")
            
            self.logger.info("\nTarget reached, shutting down...")
            self.stop_event.set()
            
            # Wait for queue to be processed
            self.logger.info("Waiting for queue to empty...")
            await self.url_queue.join()
            
            # Wait for all tasks to finish with timeout
            self.logger.info("Waiting for tasks to finish...")
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0
            )
            
        except asyncio.TimeoutError:
            self.logger.info("Some tasks didn't finish within timeout")
        except KeyboardInterrupt:
            self.logger.info("\nReceived interrupt signal")
            self.stop_event.set()
            # Cancel all tasks gracefully
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            # Print final statistics
            self._print_statistics()
    
    def _print_statistics(self):
        """Print final statistics"""
        self.logger.info("\n" + "="*50)
        self.logger.info("FINAL STATISTICS:")
        self.logger.info(f"Total URLs found: {self.grabber.url_counter}")
        self.logger.info(f"Final queue size: {self.url_queue.qsize()}")
        for analyzer in self.analyzers:
            self.logger.info(f"Analyzer {analyzer.analyzer_id} processed: {analyzer.processed_count} items")
        self.logger.info("="*50)