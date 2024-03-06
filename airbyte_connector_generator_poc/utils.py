import re
import yaml
import os
import validators
import os
import shutil
from airbyte_connector_generator_poc.logger import logger


ENV_PATH = os.path.join(os.getcwd(), ".env")
SKYFFEL_DIR = os.path.join(os.getcwd(), ".skyffel")


def extract_yaml_from_markdown(content) -> dict:
    pattern = r"```yaml(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)

    if matches:
        yaml_content = matches[0]
    else:
        yaml_content = content
    try:
        return yaml.safe_load(yaml_content.strip())
    except Exception as e:
        write_debug_file("error_extracting_yaml.txt", content)
        logger.debug(f"Error extracting YAML: {yaml_content}")
        raise e


def check_env_for_key(env_key):
    if not os.path.exists(ENV_PATH):
        open(ENV_PATH, 'a').close()
        logger.debug("Notice: .env file was missing and has been created.")

    with open(ENV_PATH, 'r') as env_file:
        lines = env_file.readlines()
        for line in lines:
            if line.strip().startswith(f'{env_key}='):
                return True
        return False


def write_env_variable(key, value):
    with open(ENV_PATH, 'a') as env_file:
        env_file.write(f"{key}={value}\n")
        logger.debug(f"{key} added to .env file.")


def validate_urls(urls: list[str]):
    urls = [url.strip() for url in urls]
    invalid_urls = [url for url in urls if not validators.url(url)]
    if invalid_urls:
        raise ValueError(f"Invalid URLs found: {invalid_urls}")
    return urls


def write_debug_file(file_name, content):
    if not os.path.exists(SKYFFEL_DIR):
        os.makedirs(SKYFFEL_DIR)
    file_path = os.path.join(SKYFFEL_DIR, file_name)
    with open(file_path, 'w') as file:  # Changed mode from 'w' to 'a' to append if file exists
        file.write(content)
    logger.debug(f"Debug file written: {file_path}")


def nuke_debug_directory():
    if not os.path.exists(SKYFFEL_DIR):
        return
    for item in os.listdir(SKYFFEL_DIR):
        item_path = os.path.join(SKYFFEL_DIR, item)
        if item != "selector_cache.json":
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
            else:
                shutil.rmtree(item_path)
    logger.debug("Debug directory reset.")
