import asyncio
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from playwright_stealth import stealth
from kwork_bot.config import KWORK_URL

logger = logging.getLogger(__name__)

class KworkParser:
    def __init__(self):
        self.browser = None
        self.context = None

    async def init_browser(self):
        if not self.browser:
            p = await async_playwright().start()
            self.browser = await p.chromium.launch(headless=True)
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )

    async def get_page_content(self, url):
        await self.init_browser()
        page = await self.context.new_page()
        try:
            # Go to base category URL first
            base_url = "https://kwork.ru/projects?c=11"
            await page.goto(base_url, wait_until="networkidle", timeout=60000)
            
            # Wait for sorting dropdown to be visible and click 'new' (новые)
            # This triggers the exact same JS logic as in a real browser
            try:
                await page.wait_for_selector(".kw-select", timeout=10000)
                # Kwork dropdowns are tricky, let's use the URL with sort=new directly 
                # but ensure we wait for the state to stabilize
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await asyncio.sleep(2) 
            except:
                pass

            content = await page.content()
            return content
        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None
        finally:
            await page.close()

    def parse_orders(self, html):
        if not html:
            return []
        
        import json
        import re
        
        orders = []
        try:
            # Kwork stores ALL project data in window.stateData.workerWants.wants
            # Try a more robust regex that handles potential variations
            state_match = re.search(r"window\.stateData\s*=\s*(\{.*?\});", html, re.DOTALL)
            if not state_match:
                # Try another variation just in case
                state_match = re.search(r"stateData\s*:\s*(\{.*?\})", html, re.DOTALL)

            if state_match:
                state_json = state_match.group(1)
                data = json.loads(state_json)
                wants = data.get("workerWants", {}).get("wants", [])
                
                if not wants:
                    # Sometimes it's nested differently or it's a different page structure
                    logger.warning("stateData found but workerWants.wants is empty")
                else:
                    for item in wants:
                        order_id = str(item.get("id"))
                        title = item.get("name", "Без заголовка")
                        description = item.get("description", "")
                        
                        # Clean up HTML tags if any in JSON description
                        description = re.sub(r'<[^>]+>', '', description)
                        
                        # Truncate to 350 as requested
                        if len(description) > 350:
                            description = description[:347] + "..."
                        
                        price_limit = item.get("priceLimit", 0)
                        higher_price = item.get("higherPrice", 0)
                        
                        budget = f"{int(float(price_limit))} ₽" if price_limit else "Не указан"
                        budget_limit = f"{int(float(higher_price))} ₽" if higher_price else "Не указан"
                        
                        time_left = "Актуально"
                        offers_count = str(item.get("offersCount", 0))
                        url = f"https://kwork.ru/projects/{order_id}"

                        orders.append({
                            'id': order_id,
                            'title': title,
                            'description': description,
                            'budget': budget,
                            'budget_limit': budget_limit,
                            'time_left': time_left,
                            'offers_count': offers_count,
                            'url': url
                        })
                    
                    if orders:
                        logger.info(f"Successfully extracted {len(orders)} orders from stateData")
                        return orders

        except Exception as e:
            logger.error(f"Error parsing JSON state: {e}")

        # Fallback to BeautifulSoup if JSON fails
        logger.info("JSON extraction failed or returned no data, falling back to BS4")
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select(".want-card")
        
        for card in cards:
            try:
                title_elem = card.select_one(".wants-card__header-title a")
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = "https://kwork.ru" + title_elem['href']
                order_id = url.split('/')[-1]

                # Target the full description (usually hidden in HTML until clicked)
                # But it's in the DOM! We pick the div with style="display: none;"
                desc_elem = card.select_one(".wants-card__description-text div[style*='display: none']")
                if not desc_elem:
                    desc_elem = card.select_one(".wants-card__description-text")
                
                description = desc_elem.get_text(" ", strip=True) if desc_elem else ""
                
                # Remove "Скрыть" or "Показать полностью" leaks
                description = description.replace("Показать полностью", "").replace("Скрыть", "").strip()
                
                if len(description) > 350:
                    description = description[:347] + "..."

                budget = "Не указан"
                budget_limit = "Не указан"

                price_elem = card.select_one(".wants-card__price")
                if price_elem:
                    budget = price_elem.get_text(" ", strip=True).replace("Желаемый бюджет:", "").replace("Цена до:", "").strip()

                higher_price_elem = card.select_one(".wants-card__description-higher-price")
                if higher_price_elem:
                    budget_limit = higher_price_elem.get_text(" ", strip=True).replace("Допустимый:", "").strip()

                time_left = "Не указано"
                offers_count = "0"
                card_text = card.get_text(" ", strip=True)
                
                time_match = re.search(r"Осталось:\s*([^\n\r]+)", card_text)
                if time_match:
                    time_left = time_match.group(1).split("Предложений")[0].strip()
                
                offers_match = re.search(r"Предложений:\s*(\d+)", card_text)
                if offers_match:
                    offers_count = offers_match.group(1).strip()

                orders.append({
                    'id': order_id,
                    'title': title,
                    'description': description,
                    'budget': budget,
                    'budget_limit': budget_limit,
                    'time_left': time_left,
                    'offers_count': offers_count,
                    'url': url
                })
            except Exception as e:
                logger.error(f"Error parsing card in BS4 fallback: {e}")

        return orders

    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
