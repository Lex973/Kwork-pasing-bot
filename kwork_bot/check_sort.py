import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://kwork.ru/projects?c=11")
        print(f"Base URL: {page.url}")
        
        # Look for the sorting dropdown or active sort
        # In the screenshot it says "Показать: новые"
        # We need to find what URL that generates
        # Let's try to find an 'a' tag with 'sort' in it
        links = await page.query_selector_all("a")
        for link in links:
            href = await link.get_attribute("href")
            text = await link.inner_text()
            if href and "sort" in href:
                print(f"Sort link: {text} -> {href}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
