from airbyte_connector_generator_poc.logger import logger
from openapi_spec_validator import validate
from airbyte_connector_generator_poc.utils import write_debug_file
from openai import AsyncOpenAI
from dotenv import load_dotenv
import os
import requests
import yaml
import json
load_dotenv()

openai = AsyncOpenAI()


def clean_openapi_spec(openapi_spec: dict):
    if "security" in openapi_spec:
        del openapi_spec["security"]

    if "components" in openapi_spec and "security" in openapi_spec["components"]:
        del openapi_spec["components"]["security"]

    version = str(openapi_spec["info"]["version"])
    version += ".0" * (2 - version.count('.'))
    openapi_spec["info"]["version"] = version

    recursive_delete_none_properties(
        openapi_spec.get('components', {}).get('schemas', {}))

    convert_angle_brackets_to_curly_braces(openapi_spec)


def recursive_delete_none_properties(schema_dict):
    if isinstance(schema_dict, dict):
        for key in list(schema_dict.keys()):
            if schema_dict[key] is None:
                del schema_dict[key]
            else:
                recursive_delete_none_properties(schema_dict[key])
    elif isinstance(schema_dict, list):
        for item in schema_dict:
            recursive_delete_none_properties(item)


def convert_angle_brackets_to_curly_braces(yaml_content: dict):
    """
    Recursively convert angle brackets to curly braces in all string values of the given dictionary.

    Args:
    - yaml_content (dict): The OpenAPI specification content as a dictionary.

    Returns:
    - None: The conversion is done in-place.
    """
    if isinstance(yaml_content, dict):
        for key, value in yaml_content.items():
            if isinstance(value, str):
                yaml_content[key] = value.replace("<", "{").replace(">", "}")
            elif isinstance(value, (dict, list)):
                convert_angle_brackets_to_curly_braces(value)
    elif isinstance(yaml_content, list):
        for item in yaml_content:
            convert_angle_brackets_to_curly_braces(item)


def validate_openapi_spec(openapi_spec: dict):
    logger.debug("Validating OpenAPI spec")
    try:
        validate(openapi_spec)
        logger.info("OpenAPI spec is valid")
        return True, None
    except Exception as e:
        logger.error(f"OpenAPI spec is not valid: %s", e)
        return False, e


async def extract_details(markdown: str, user_goal: str):
    response = await openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """
You're an expert at extracing information about how to authentication & authorization an API from technical documentation written in markdown.
When including examples, prefer agnostic code such as cURL or HTTPie over language-specific code.
Prefer Basic Authentication, API Keys and Bearer Authentication over other methods.
                
You're an expert at extracing pagination strategies from technical API documentation written in markdown.

You're an HTTP API expert. Given this API documentation in markdown, get the relevant endpoint and describe the resource with:
- Path
- HTTP Method
- Requests body schema
- Response schema
- Request headers
- Request cookies
- Request query Parameters

NEVER EVER OMIT ANYTHING FOR BREVITY.
The user will provide a goal, make sure to follow that.

Take a deep breath, think step by step, and reason yourself to the correct answer.
                """
            },
            {
                "role": "user",
                "content": f"My goal: {user_goal}. Extract relevant information from this documentation: {markdown} "
            }
        ]
    )

    return response.choices[0].message.content


async def generate_openapi_spec_from_markdown(markdown: str, user_goal: str):
    logger.debug(
        f"Start extracting relevant markdown given user goal: %s", user_goal)

    info = await extract_details(markdown, user_goal)

    SYSTEM_PROMPT = f"""
You’re an expert at writing OpenAPI 3.0 specifications.
Your task is to produce an OpenAPI 3.0 specification from the documentation and a goal given by the user.

Keep this in mind:
- Include every optional argument and parameter in the specification.
- Required version headers are very important. E.g the `Notion-Version` header should always be included as a header in the specification
- If there is any URL path with an extension like `.json` or `.xml` then you must include it.

OUTPUT ONLY JSON!
    """
    USER_PROMPT = f"""
My goal as a user, {user_goal}. This is very important to me.

# Here's the information you need:
{info}

Take a deep breath, think step by step, and reason yourself to the correct answer.
Write the OpenAPI 3.0 specification.
    """

    write_debug_file("system_prompt.txt", SYSTEM_PROMPT)
    write_debug_file("user_prompt.txt", USER_PROMPT)

    logger.info("Generating OpenAPI spec")

    response = await openai.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT}
        ],
        model="gpt-4-turbo-preview",
        temperature=0,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)


def load_openapi_spec_from_path_or_url(path: str):
    if path.startswith("http"):
        response = requests.get(path)
        openapi_spec_raw = response.json()
    else:
        if not os.path.exists(path):
            raise FileNotFoundError(f"The file {path} does not exist.")
        with open(path, 'r') as file:
            openapi_spec_raw = file.read()
    return yaml.safe_load(openapi_spec_raw)
