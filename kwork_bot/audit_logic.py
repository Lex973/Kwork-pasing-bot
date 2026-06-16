import asyncio
import logging
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

async def audit():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        
        url = "https://kwork.ru/projects?c=11&view=0&sort=new"
        print(f"Loading URL: {url}")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_selector(".want-card", timeout=15000)
        
        # Audit Scroll
        print("Scrolling...")
        for i in range(5):
            await page.evaluate("window.scrollBy(0, window.innerHeight)")
            await asyncio.sleep(1)
            cards_count = await page.locator(".want-card").count()
            print(f"Scroll {i+1}: Found {cards_count} cards in DOM")

        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Check all possible card-like containers
        all_cards = soup.select(".want-card")
        print(f"Total .want-card found by BS4: {len(all_cards)}")
        
        # Print first 15 titles and their order in HTML
        for i, card in enumerate(all_cards[:20]):
            title_el = card.select_one(".wants-card__header-title a")
            title = title_el.get_text(strip=True) if title_el else "NO TITLE"
            
            # Check for special classes or attributes (e.g. pinned orders)
            classes = card.get("class", [])
            print(f"#{i+1} [Classes: {classes}] Title: {title}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(audit())
