import asyncio
import random
import re
import logging
from typing import List

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup

from user_agents import USER_AGENTS
from exceptions import AvitoFirewallException
import config

class AvitoItemsURLGrabber:
    def __init__(self):
        self.is_running = False
        self.url_mask = {}
        self.browser = None
        self.page = None
        self.stealth = None
        self.url_counter = 0
        self.logger = logging.getLogger(f"{__name__}.Grabber")
    
    async def fetch_urls(self, queue: asyncio.Queue, stop_event: asyncio.Event):
        """
        Producer: Continuously fetch URLs and put them into the queue
        """
        self.logger.info("Grabber: Start")
        self.is_running = True
        
        while not stop_event.is_set():
            try:
                await self._initialize_browser()
                
                while not stop_event.is_set() and self.url_counter < config.MAX_URLS_TO_COLLECT:
                    urls = await self._get_avito_urls()
                    
                    for url in urls:
                        await queue.put(url)
                        self.logger.info(f"Grabber: Added URL {url} to queue")
                    
                    # Wait before next batch
                    await asyncio.sleep(2)
                    
            except Exception as ex:
                self.logger.exception(f"Exception occurred: {ex}. Here's a traceback for you, big boy...")
                
                try:
                    await self.browser.close()
                except:
                    pass  # If it breaks - it breaks. Who cares?
            finally:
                self.is_running = False
    
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
        self.stealth.navigator_user_agent = user_agent
        self.stealth.navigator_user_agent_override = user_agent
        self.logger.info(f"Grabber: User agent is {user_agent}")
        
        # Apply stealth to the context
        await self.stealth.apply_stealth_async(context)

        self.page = await context.new_page()
        await self.page.goto("https://www.avito.ru/")
        await asyncio.sleep(10.0)

        html = await self.page.content()
        self.logger.info(f"Actual user agent: {await self.page.evaluate('navigator.userAgent')}")
        
        if "firewall-container" in html:
            raise AvitoFirewallException("We've been detected by a firewall!")
    
    async def _get_avito_urls(self) -> List[str]:
        """Collect Avito URLs"""
        urls = []
        
        scroll_before = await self.page.evaluate('window.scrollY')

        for _ in range(5):
            await self.page.mouse.wheel(0, 1000)
            await asyncio.sleep(0.25)
        
        scroll_after = await self.page.evaluate('window.scrollY')

        if scroll_before == scroll_after:
            await self.page.reload()
            await asyncio.sleep(10.0)

            html = await self.page.content()
            if "firewall-container" in html:
                raise AvitoFirewallException("We've been detected by a firewall!")

            for _ in range(5):
                await self.page.mouse.wheel(0, 1000)
                await asyncio.sleep(0.25)

        html = await self.page.content()
        soup = BeautifulSoup(html, 'html.parser')
        
        divs = soup.find_all("div", {"data-marker": re.compile(r"item")})
        
        for div in divs:
            a_tag = div.find("a")
            if not a_tag:
                continue
            url = "https://www.avito.ru" + a_tag.get("href")
            if not self.url_mask.get(url, False):
                urls.append(url)
                self.url_counter += 1
                self.logger.info(f"Grabber: URLs collected {self.url_counter}")
            self.url_mask[url] = True
        
        await self.page.mouse.wheel(0, 1000)

        return urls