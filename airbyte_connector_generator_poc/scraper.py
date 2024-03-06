from playwright.async_api import async_playwright


async def scrape_urls(urls: list[str]) -> dict:
    content_by_url = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for url in urls:
            page = await browser.new_page()
            await page.goto(url)
            await page.wait_for_load_state("networkidle")
            content = await page.content()
            content_by_url[url] = content
        await browser.close()
    return content_by_url
