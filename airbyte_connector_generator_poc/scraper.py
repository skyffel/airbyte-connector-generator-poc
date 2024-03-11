from playwright.async_api import async_playwright
from rich.progress import Progress
from rich.progress import SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
    TimeElapsedColumn(),
)


async def scrape_urls(urls: list[str]) -> dict:
    with progress:
        scrape_progress_task = progress.add_task(
            "[bold cyan]Scraping URLs...", total=len(urls))

        content_by_url = {}
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            for url in urls:
                progress.update(scrape_progress_task,
                                description=f"[bold cyan]Scraping[/bold cyan] {url}")
                page = await browser.new_page()
                await page.goto(url)
                await page.wait_for_load_state("networkidle")
                content = await page.content()
                content_by_url[url] = content
                progress.update(scrape_progress_task, advance=1)
            await browser.close()

        progress.update(scrape_progress_task,
                        description="[bold green]✅ Scraped URLs")

        return content_by_url
