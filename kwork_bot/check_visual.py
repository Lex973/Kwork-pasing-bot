import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a more realistic window size
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        url = "https://kwork.ru/projects?c=11&view=0&sort=new"
        print(f"Opening {url}")
        await page.goto(url, wait_until="networkidle")
        
        # Wait for cards
        await page.wait_for_selector(".want-card")
        
        # Check if there is a pagination button or "show more"
        show_more = await page.query_selector("text=Показать еще")
        if show_more:
            print("Found 'Show more' button. Clicking...")
            await show_more.click()
            await asyncio.sleep(2)
            
        # Count again
        cards = await page.query_selector_all(".want-card")
        print(f"Final card count on page: {len(cards)}")
        
        # Check if titles match the screenshot
        for i, card in enumerate(cards[:10]):
            title = await card.query_selector(".wants-card__header-title a")
            if title:
                print(f"#{i+1}: {await title.inner_text()}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
