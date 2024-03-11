import os
import traceback

from rich.console import Console
from rich.status import Status
from rich.progress import Progress
from rich.progress import SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn

from airbyte_connector_generator_poc.utils import SKYFFEL_DIR, write_debug_file
from airbyte_connector_generator_poc.docs_parser import (convert_html_to_markdown,
                                                         extract_relevant_html)
from dotenv import load_dotenv
from airbyte_connector_generator_poc.local_cache import LocalCache
from airbyte_connector_generator_poc.openapi_spec import (clean_openapi_spec, generate_openapi_spec_from_markdown,
                                                          validate_openapi_spec)

from airbyte_connector_generator_poc.logger import logger

import hashlib

load_dotenv()

console = Console(log_time=False)
progress = Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TaskProgressColumn(),
    TimeElapsedColumn(),
)


async def generate_openapi_spec(url_html_documents: dict, user_goal: str):
    assert len(url_html_documents.keys()) > 0

    logger.debug(f"Start generating OpenAPI spec for user goal: {user_goal}")
    write_debug_file("html_documents_combined.html",
                     "\n".join(url_html_documents.values()))

    url_selector_cache = LocalCache(
        os.path.join(SKYFFEL_DIR, 'selector_cache.json'))

    relevant_html_tags = []

    with progress:
        preprocessing_task = progress.add_task(
            "[bold green]Preprocessing docs...", total=len(url_html_documents.keys()))

        for url, html_document in url_html_documents.items():
            progress.update(preprocessing_task,
                            description=f"[bold cyan]Preprocessing[/bold cyan] {url}")

            url_key = hashlib.md5(url.encode()).hexdigest()

            selectors = url_selector_cache.get(key=url_key) or {}

            main_section_selector = selectors.get("main_section_selector")
            irrelevant_sections_selectors = selectors.get(
                "irrelevant_sections_selectors")

            relevant_html, main_section_selector, irrelevant_sections_selectors = extract_relevant_html(
                html_document, main_section_selector, irrelevant_sections_selectors)

            write_debug_file(f"relevant_html_{
                url_key}.html", relevant_html.prettify())

            url_selector_cache.set(key=url_key, value={
                "main_section_selector": main_section_selector,
                "irrelevant_sections_selectors": irrelevant_sections_selectors,
                "url": url,
            })

            relevant_html_tags.append(relevant_html)

            progress.update(preprocessing_task, advance=1)

        progress.update(preprocessing_task,
                        description="[bold green]✅ Preprocessed docs")

    relevant_html_combined = "\n".join(
        [tag.prettify() for tag in relevant_html_tags])

    write_debug_file("relevant_html_combined.html", relevant_html_combined)

    logger.debug(f"Start converting relevant HTML to markdown")
    markdown = convert_html_to_markdown(relevant_html_combined)
    write_debug_file("markdown.md", markdown)

    with Status("[bold cyan]Generating OpenAPI spec...", console=console):
        openapi_spec_json = await generate_openapi_spec_from_markdown(markdown, user_goal)
        clean_openapi_spec(openapi_spec_json)
        console.log("[bold green]  ✅ OpenAPI spec generated")

    ok, err = validate_openapi_spec(openapi_spec_json)

    if ok:
        console.log("[green bold]  ✅ OpenAPI spec is valid")
    else:
        console.log(
            "[red bold]  ❌ OpenAPI spec is invalid (check .skyffel/openapi_validation_error.log for more details)")
        write_debug_file("openapi_validation_error.log",
                         "".join(traceback.format_exception(err)))
        exit(1)

    return openapi_spec_json
