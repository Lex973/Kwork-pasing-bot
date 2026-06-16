import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://kwork.ru/projects?c=11")
        
        # Capture the HTML of the sorting dropdown area
        # Usually it's in a div with some specific class
        # Let's just find "новые"
        try:
            # Look for links containing "новые" in text
            handles = await page.query_selector_all("a")
            for h in handles:
                text = await h.inner_text()
                if "новые" in text.lower():
                    href = await h.get_attribute("href")
                    print(f"FOUND: '{text}' -> {href}")
        except Exception as e:
            print(e)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
