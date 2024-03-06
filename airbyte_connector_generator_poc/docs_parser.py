from pprint import pprint
from html2text import HTML2Text
from bs4 import BeautifulSoup, Tag
import json
from openai import OpenAI
from airbyte_connector_generator_poc.logger import logger
from airbyte_connector_generator_poc.html_tree import build_html_tree
from dotenv import load_dotenv
load_dotenv()


openai = OpenAI()


def elect_main_section_selector(html_tree_str: str):
    # Get selector for the main area we want to keep
    response = openai.chat.completions.create(
        messages=[{
            "role": "system",
            "content": """
        You're an HTML expert. Your task is to find the section with most relevant content of a page given an HTML document.
        Avoid long chain of child selectors (>).
        Output the selector as JSON in the `selector` property.
      """
        }, {
            "role": "user",
            "content": f"Find the main section of this page: {html_tree_str}"
        }],
        response_format={
            "type": "json_object"
        },
        model="gpt-4-turbo-preview",
        temperature=0,
        frequency_penalty=0.7,
    )
    print(f"get_main_section_selector: {response.usage.total_tokens} tokens")
    selector_json = json.loads(response.choices[0].message.content)
    pprint(json.dumps(selector_json))
    selector = selector_json["selector"]
    return selector


def get_irrelevant_sections_selectors(html_tree_str: str):
    response = openai.chat.completions.create(
        messages=[{
            "role": "system",
            "content": """
            You're an HTML expert. Your task is to remove sections that are not relevant to the main content. Things like:
            - Navigation (also knows as Nav, Navbar, etc.)
            - Menus
            - Sidebars with navigation or menus in them
            - Advertisements
            - Footer
            Descendant children of this HTML might be relevant to keep, so be aware!
            Output the selectors to remove as JSON in the `selectors` property.
            """
        }, {
            "role": "user",
            "content": f"Find the section to remove of this page: {html_tree_str}"
        }],
        response_format={
            "type": "json_object"
        },
        model="gpt-4-turbo-preview",
        temperature=0,
        frequency_penalty=0.7,
    )

    print(f"get_irrelevant_sections_selectors: {
          response.usage.total_tokens} tokens")
    selector_json = json.loads(response.choices[0].message.content)
    pprint(selector_json)
    return selector_json["selectors"]


def remove_irrelevant_sections(html: Tag, selectors: list[str]):
    for selector in selectors:
        selected_list = html.select(selector)
        logger.debug(f"{selector}: {len(selected_list)} elements found")

        for selected in selected_list:

            selected.extract()

    return html


def convert_html_to_markdown(raw_html: str):
    # Create an HTML to text converter
    text_maker = HTML2Text()
    # Ignore converting links from HTML
    text_maker.ignore_links = False
    # Convert the HTML to Markdown
    return text_maker.handle(raw_html)


def extract_relevant_html(raw_html: str, main_section_selector=None, irrelevant_sections_selectors=None):
    html = BeautifulSoup(raw_html, "html.parser")
    html_tree = build_html_tree(html)

    if main_section_selector is None:
        main_section_selector = elect_main_section_selector(html_tree)

    html_main_content = html.select_one(main_section_selector)

    # TODO: self heal
    if html_main_content is None:
        raise ValueError(f"No main content found with selector `{
                         main_section_selector}`.")

    html_main_content_tree = build_html_tree(html_main_content)

    if irrelevant_sections_selectors is None:
        irrelevant_sections_selectors = get_irrelevant_sections_selectors(
            html_main_content_tree)

    cleaned_html_main_content = remove_irrelevant_sections(
        html_main_content, irrelevant_sections_selectors)

    return cleaned_html_main_content, main_section_selector, irrelevant_sections_selectors
