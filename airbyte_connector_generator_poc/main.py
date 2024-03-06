import yaml
from dotenv import load_dotenv
import typer
from airbyte_connector_generator_poc.utils import check_env_for_key, write_env_variable, validate_urls, nuke_debug_directory
from airbyte_connector_generator_poc.scraper import scrape_urls
from asyncio import run
from airbyte_connector_generator_poc.logger import logger
from airbyte_connector_generator_poc.airbyte.airbyte import generate_airbyte_connector, validate_airbyte_connector

load_dotenv()


async def _main(goal: str, urls: list[str]):
    nuke_debug_directory()

    typer.echo("Welcome to skyffel!")

    if not goal:
        goal = typer.prompt("Tell us, what do you want to integrate?")
    if not check_env_for_key("OPENAI_API_KEY"):
        typer.echo(
            "We'll need an api key to generate the code. We'll store it in a .env file")
        openai_api_key = typer.prompt(
            "Please enter your OpenAI API key", hide_input=True)
        if not openai_api_key.startswith("sk-"):
            raise ValueError("OpenAI API key is required.")
        write_env_variable("OPENAI_API_KEY", openai_api_key)

    load_dotenv()

    from airbyte_connector_generator_poc.openapi_generator import generate_openapi_spec
    from airbyte_connector_generator_poc.openapi_spec import load_openapi_spec_from_path_or_url

    # with Progress() as progress:
    # has_openapi_spec = typer.confirm(
    #     "Do you have an OpenAPI specficitaion?")

    has_openapi_spec = False

    if has_openapi_spec:
        openapi_spec_path = typer.prompt(
            "Please enter the path or url to the OpenAPI spec file")
        openapi_spec = load_openapi_spec_from_path_or_url(
            openapi_spec_path)
    else:
        urls = validate_urls(urls)

        # task_scrape_urls = progress.add_task(
        #     "Scraping URLs", total=len(urls))

        logger.debug(f"Start scraping URLs: %s", urls)
        html_documents = await scrape_urls(urls)
        logger.debug(f"Scraped HTML documents")

        # progress.update(task_scrape_urls, completed=True)

        openapi_spec = await generate_openapi_spec(url_html_documents=html_documents, user_goal=goal)

    with open("openapi.yaml", 'w') as file:
        yaml.safe_dump(openapi_spec, file)

    airbyte_connector = generate_airbyte_connector(openapi_spec)

    logger.debug("Airbyte connector generated")

    validate_airbyte_connector(airbyte_connector)

    logger.debug(f"Writing airbyte connector")
    with open("airbyte_connector.yaml", 'w') as f:
        yaml.safe_dump(airbyte_connector, f)


def main(goal: str = typer.Option(), urls: list[str] = typer.Option()):
    run(_main(goal, urls))


def cli():
    typer.run(main)


if __name__ == "__main__":
    typer.run(main)
