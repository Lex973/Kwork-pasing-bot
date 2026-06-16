import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://kwork.ru/projects?c=11&view=0&sort=new")
        await page.wait_for_selector(".want-card")
        
        # Capture the whole want-list container HTML
        container = await page.query_selector(".js-wants-list") or await page.query_selector(".wants-content")
        if container:
            html = await container.inner_html()
            with open("container.html", "w") as f:
                f.write(html)
            print("Saved container.html")
        else:
            print("Container not found")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
