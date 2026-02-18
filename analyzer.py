import asyncio
import random
import re
import json
import logging
import config
from typing import Dict, Any
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
from user_agents import USER_AGENTS
from exceptions import AvitoFirewallException

class AvitoItemsAnalyzer:
    def __init__(self, analyzer_id: int):
        self.analyzer_id = analyzer_id
        self.is_running = False
        self.browser = None
        self.page = None
        self.stealth = None
        self.processed_count = 0
        self.output_file = config.OUTPUT_JSONL_FILE_NAME
        self.logger = logging.getLogger(f"{__name__}.Analyzer-{analyzer_id}")
    
    def _save_to_jsonl(self, data: dict):
        """Save dictionary as a new line in JSONL file"""
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                json_line = json.dumps(data, ensure_ascii=False)
                f.write(json_line + '\n')
        except Exception as e:
            self.logger.exception(f"Error saving to JSONL: {e}")
    
    async def process_urls(self, queue: asyncio.Queue, stop_event: asyncio.Event):
        """
        Consumer: Continuously get URLs from queue and analyze them
        Each analyzer has its own browser instance
        """
        self.is_running = True
        self.logger.info(f"Analyzer {self.analyzer_id}: Starting")
        
        while not stop_event.is_set():
            try:
                await self._initialize_browser()
                
                while not stop_event.is_set() or not queue.empty():
                    try:
                        # Get URL from queue with timeout
                        url = await asyncio.wait_for(queue.get(), timeout=1.0)
                        
                        self.logger.info(f"Analyzer {self.analyzer_id}: Processing {url}")
                        
                        # Analyze the URL
                        item_data = await self._analyze_item(url)
                        self.processed_count += 1
                        self._save_to_jsonl(item_data)
                        
                        self.logger.info(f"Analyzer {self.analyzer_id}: Processed {item_data['title']} -> Price: {item_data['price']}")
                        
                        queue.task_done()
                        
                    except asyncio.TimeoutError:
                        # No items in queue, continue waiting
                        continue
                    except Exception as e:
                        self.logger.exception(f"Analyzer {self.analyzer_id}: Error processing URL: {e}")
                        queue.task_done()  # Mark as done even on error

            except Exception as e:
                self.logger.exception(f"Analyzer {self.analyzer_id}: Fatal error: {e}... Here's a traceback for you, big boy...")

                try:
                    await self.browser.close()
                except:
                    pass  # If it breaks - it breaks. Who cares?
            finally:
                self.is_running = False
                if self.browser:
                    await self.browser.close()
                self.logger.info(f"Analyzer {self.analyzer_id}: Stopped, processed {self.processed_count} items")
    
    async def _initialize_browser(self):
        """Initialize browser with stealth settings"""
        self.stealth = Stealth()
        playwright_context = await async_playwright().start()
        self.browser = await playwright_context.firefox.launch(
            headless=False,
            args=['--start-minimized', '--window-position=-2000,0']
        )

        user_agent = random.choice(USER_AGENTS)
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=user_agent
        )
        self.stealth.navigator_user_agent_override = user_agent
        self.logger.info(f"Analyzer {self.analyzer_id}: User agent is {user_agent}")
        
        # Apply stealth to the context
        await self.stealth.apply_stealth_async(context)

        self.page = await context.new_page()
        self.logger.info(f"Analyzer {self.analyzer_id}: Browser launched")
    
    async def _analyze_item(self, url: str) -> Dict[str, Any]:
        """Analyze a single Avito item"""
        try:
            await self.page.goto(url, timeout=30000)
            await asyncio.sleep(random.uniform(30.0, 35.0))

            html = await self.page.content()
            if "firewall-container" in html:
                raise AvitoFirewallException("We've been detected by a firewall!")
            
            soup = BeautifulSoup(html, 'html.parser')

            title = "Undefined"
            price = "Undefined"
            seller = "Undefined"
            description = "Undefined"

            title_h1 = soup.find("h1", {"data-marker": re.compile(r"item-view/title-info")})
            if title_h1:
                title = title_h1.text.strip()
            else:
                self.logger.info("Couldn't find h1????")
            
            price_span = soup.find("span", {"data-marker": re.compile(r"item-view/item-price")})
            if price_span:
                price = price_span.text.strip()
            else:
                self.logger.info("Couldn't find span????")
            
            seller_a = soup.find("a", {"data-marker": re.compile(r"seller-link/link")})
            if seller_a:
                seller = seller_a.text.strip()
            else:
                self.logger.info("Couldn't find a tag????")
            
            description_div = soup.find("div", {"data-marker": re.compile(r"item-view/item-description")})
            if description_div:
                description = description_div.text.strip()
            else:
                self.logger.info("Couldn't find div????")

            return {
                'url': url,
                'title': title,
                'price': price,
                'description': description,
                'seller': seller
            }
        except AvitoFirewallException as e:
            raise e
        except Exception as e:
            self.logger.exception(f"Error analyzing {url}: {e} | Trying again!")
            result = await self._analyze_item(url)
            return result