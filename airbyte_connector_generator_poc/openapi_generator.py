import os
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


async def generate_openapi_spec(url_html_documents: dict, user_goal: str):
    assert len(url_html_documents.keys()) > 0

    logger.debug(f"Start generating OpenAPI spec for user goal: {user_goal}")
    write_debug_file("html_documents_combined.html",
                     "\n".join(url_html_documents.values()))

    url_selector_cache = LocalCache(
        os.path.join(SKYFFEL_DIR, 'selector_cache.json'))

    relevant_html_tags = []

    for url, html_document in url_html_documents.items():
        url_key = hashlib.md5(url.encode()).hexdigest()

        logger.debug(
            f"Start extracting relevant HTML from docs URL: %s (%s)", url, url_key)

        selectors = url_selector_cache.get(key=url_key) or {}

        main_section_selector = selectors.get("main_section_selector")
        irrelevant_sections_selectors = selectors.get(
            "irrelevant_sections_selectors")

        relevant_html, main_section_selector, irrelevant_sections_selectors = extract_relevant_html(
            html_document, main_section_selector, irrelevant_sections_selectors)

        logger.info(
            f"Extracted relevant HTML from docs URL: %s (%s)", url, url_key)

        write_debug_file(f"relevant_html_{
                         url_key}.html", relevant_html.prettify())

        url_selector_cache.set(key=url_key, value={
            "main_section_selector": main_section_selector,
            "irrelevant_sections_selectors": irrelevant_sections_selectors,
            "url": url,
        })

        relevant_html_tags.append(relevant_html)

    relevant_html_combined = "\n".join(
        [tag.prettify() for tag in relevant_html_tags])

    write_debug_file("relevant_html_combined.html", relevant_html_combined)

    logger.debug(f"Start converting relevant HTML to markdown")
    markdown = convert_html_to_markdown(relevant_html_combined)
    write_debug_file("markdown.md", markdown)

    openapi_spec_json = await generate_openapi_spec_from_markdown(markdown, user_goal)
    clean_openapi_spec(openapi_spec_json)

    validate_openapi_spec(openapi_spec_json)

    return openapi_spec_json
