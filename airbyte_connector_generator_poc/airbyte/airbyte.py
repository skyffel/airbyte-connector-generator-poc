from collections import defaultdict
import json
from pprint import pprint
import yaml
import jsonschema
import os
import dotenv
from openai import OpenAI
from airbyte_connector_generator_poc.logger import logger
import re

dotenv.load_dotenv()
openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

AIRBYTE_PATH = os.path.dirname(os.path.realpath(__file__))


def traverse_yaml_dict_ref(yaml_dict: dict, ref: str):
    if not ref.startswith("#/"):
        raise ValueError(f"Invalid ref: {ref}")

    ref_parts = ref.split("/")[1:]

    current_level = yaml_dict

    for part in ref_parts:
        current_level = current_level.get(part)
        if current_level is None:
            return None

    return current_level


def expand_refs(yaml_dict: dict, current_level=None, is_root=True):
    if is_root and current_level is None:
        current_level = yaml_dict

    if isinstance(current_level, dict):
        new_dict = {}
        for key, value in current_level.items():
            if key == '$ref':
                ref_content = traverse_yaml_dict_ref(yaml_dict, value)
                if ref_content is not None:
                    new_dict.update(expand_refs(yaml_dict, ref_content, False))
            else:
                new_dict[key] = expand_refs(yaml_dict, value, False)
        return new_dict
    elif isinstance(current_level, list):
        return [expand_refs(yaml_dict, item, False) for item in current_level]
    else:
        return current_level


def derive_authenticator(connection_specification: dict, openapi_spec: dict):
    sec_schema = list(openapi_spec.get("components", {}).get(
        "securitySchemes", {}).values())

    authenticator = {"type": "NoAuth"}

    if sec_schema and sec_schema[0]:
        auth_scheme = sec_schema[0].get("scheme")
        auth_type = sec_schema[0].get("type")

        if auth_type == "http" and auth_scheme == "bearer":
            connection_specification["properties"]["api_key"] = {
                "type": "string",
                "title": "API Key",
                "airbyte_secret": True
            }
            connection_specification["required"].append("api_key")
            authenticator = {
                "api_token": "{{ config['api_key'] }}",
                "type": "BearerAuthenticator",
            }
        elif auth_type == "apiKey":
            auth_in = sec_schema[0].get("in")
            auth_name = sec_schema[0].get("name")

            connection_specification["properties"]["api_key"] = {
                "type": "string",
                "title": "API Key",
                "airbyte_secret": True
            }
            connection_specification["required"].append("api_key")

            if auth_in == "header":
                authenticator = {
                    "api_token": "{{ config['api_key'] }}",
                    "type": "ApiKeyAuthenticator",
                    "header": auth_name,
                }

            else:
                authenticator = {
                    "api_token": "{{ config['api_key'] }}",
                    "type": "ApiKeyAuthenticator",
                    "inject_into": "request_parameter" if auth_in == "query" else auth_in,
                    "field_name": auth_name,
                }

        else:
            raise Exception(f"Unsupported auth type: {auth_type}")

    return authenticator


def derive_params(connection_specification: dict, parameters: list[dict], excluded: list[str]) -> dict:
    params = {}

    for param in parameters:
        param_key = param.get("name")
        param_value = param.get("example")
        param_required = param.get("required")

        if param_key in excluded:
            continue

        if param_value is None:
            param_type = param.get("schema", {}).get("type")

            if param_type is None:
                raise ValueError(
                    f"Could not determine type for param: {param_key}")

            connection_specification["properties"][param_key] = {
                "type": param_type,
                "title": param_key,
            }

            if param_required:
                connection_specification["required"].append(param_key)

            param_value = "{{ config['" + param_key + "'] }}"

        params[param_key] = param_value

    return params


def determine_primary_key(response_schema: dict) -> list[str]:
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are an assistant designed to determine the top schema. Always respond with JSON and put the results under the key \"primary_keys\"",
            },
            {
                "role": "user",
                "content": f"Given the response schema, what is the primary key? {json.dumps(response_schema)}"
            },
        ],
        temperature=0,
    )

    primary_keys = json.loads(
        response.choices[0].message.content).get("primary_keys")

    return primary_keys


def determine_top_level_props(response_schema: dict) -> list[str]:
    root_type = response_schema.get("type")

    if root_type == "object":
        properties = response_schema["properties"]
        for prop, type_info in properties.items():
            if type_info.get("type") == "array":
                return [prop]

    return ["*"]


def determine_paginator(connection_specification: dict, parameters: dict, request_body_schema: dict, response_schema: dict) -> dict:
    docs_content = []

    with open(os.path.join(AIRBYTE_PATH, "pagination_yaml.md"), "r") as f:
        docs_content.append(f.read())

    with open(os.path.join(AIRBYTE_PATH, "pagination.md"), "r") as f:
        docs_content.append(f.read())

    response = openai.chat.completions.create(
        model="gpt-4-turbo-preview",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": f"""
                You are an expert data engineer working for Airbyte, specialised in writing low-code YAML paginators.
                Here is the official documentation for paginators: {"\n".join(docs_content)}.
                Always respond with JSON and put the results under the key \"paginator\"!
            """},
            {
                "role": "user",
                "content": f"""Given the request params, request body and response schema, what is the paginator?
                Request Parameters:
                {json.dumps(parameters)}

                Request Body:
                {json.dumps(request_body_schema)}

                Response:
                {json.dumps(response_schema)}
                """
            },
        ],
        temperature=0,
    )

    paginator = json.loads(
        response.choices[0].message.content).get("paginator")

    if "pagination_strategy" not in paginator:
        return paginator

    if paginator.get("pagination_strategy", {}).get("page_size") is None:
        page_size = 100

        if paginator.get("pagination_strategy", {}).get("type") == "OffsetIncrement":
            connection_specification["properties"]["page_size"] = {
                "type": "integer",
                "title": "Page Size",
            }
            connection_specification["required"].append("page_size")
            page_size = "{{ config['page_size'] }}"

        paginator["pagination_strategy"]["page_size"] = page_size

    return paginator


def get_request_body_schema(openapi_spec: dict, resource: dict) -> dict:
    return expand_refs(openapi_spec, resource
                       .get("requestBody", {})
                       .get("content", {})
                       .get("application/json", {})
                       .get("schema", {})
                       )


def get_response_schema(openapi_spec: dict, resource: dict) -> dict:
    return expand_refs(openapi_spec, resource
                       .get("responses", {})
                       .get("200", {})
                       .get("content", {})
                       .get("application/json", {})
                       .get("schema", {})
                       )


def group_paginator_by_inject_into(paginator: dict) -> dict:
    grouped = defaultdict(list)

    for value in paginator.values():
        if isinstance(value, dict) and "inject_into" in value and "field_name" in value:
            grouped["query" if value["inject_into"] ==
                    "request_parameter" else value["inject_into"]].append(value["field_name"])

    return dict(grouped)


def map_request_body(connection_specification: dict, banned_params: dict, data: dict, keys: list[str] = [], is_required: bool = False):
    data_type = data.get("type")

    latest_key = keys[-1] if keys else None

    if latest_key in banned_params.get("body_json", []) + banned_params.get("body_data", []):
        return

    if data_type == "object":
        result = {}

        required_keys = data.get("required", [])

        for k, v in data.get("properties", {}).items():
            is_required = k in required_keys
            output = map_request_body(
                connection_specification, banned_params, v, keys + [k], is_required)
            if output:
                result[k] = output

        return result
    elif data_type in ["string", "number", "integer", "boolean", "array"]:
        config_key = "_".join(keys)
        value = "{{ config['" + config_key + "'] }}"
        enum = data.get("enum")
        example = data.get("example")

        if enum and len(enum) == 1:
            value = enum[0]
        else:
            connection_specification["properties"][config_key] = {
                "type": data_type,
                "title": config_key,
                **({"examples": [example]} if example else {}),
                ** ({"enum": enum} if enum else {}),
            }

            if data_type == "array" and "items" in data and data["items"].get("type") == "object":
                # objects in arrays are not supported for now
                connection_specification["properties"][config_key]["type"] = "string"
                connection_specification["properties"][config_key][
                    "description"] = "This is an array of objects. For now you have to provide a JSON string."
                connection_specification["properties"][config_key]["examples"] = example

            if is_required:
                connection_specification["required"].append(config_key)

        return value

    return data


def derive_url_base(connection_specification: dict, openapi_spec: dict) -> str:
    url_base = openapi_spec.get("servers", [{}])[0].get("url")

    param_pattern = re.compile(r"\{(.+?)\}")
    url_base_config = param_pattern.findall(url_base)

    for config_param in url_base_config:
        config_key = f"url_base_{config_param}"

        url_base = url_base.replace(
            f"{{{config_param}}}", f"{{{{ config['{config_key}'] }}}}")

        connection_specification["required"].append(config_key)
        connection_specification["properties"][config_key] = {
            "type": "string",
            "title": config_key
        }

    if not url_base.startswith("https"):
        url_base = url_base.replace("http", "https", 1)

    return url_base


def generate_airbyte_connector(openapi_spec: str) -> dict:
    connection_specification = {
        "required": [],
        "properties": {},
        "type": "object",
        "$schema": "http://json-schema.org/draft-07/schema#",
    }

    url_base = derive_url_base(connection_specification, openapi_spec)

    first_path = next(iter(openapi_spec.get("paths", {}).values()))
    first_resource = next(iter(first_path.values()))

    authenticator = derive_authenticator(
        connection_specification=connection_specification,
        openapi_spec=openapi_spec
    )

    paginator = determine_paginator(
        connection_specification=connection_specification,
        parameters=expand_refs(
            openapi_spec, first_resource.get("parameters", [])),
        request_body_schema=get_request_body_schema(
            openapi_spec, first_resource),
        response_schema=get_response_schema(openapi_spec, first_resource),
    )

    banned_params = group_paginator_by_inject_into(paginator)

    streams = []

    for path, methods in openapi_spec.get("paths", {}).items():
        for method, resource in methods.items():
            name = f"{path}_{method}"
            parameters = expand_refs(
                openapi_spec, resource.get("parameters", []))
            response_schema = get_response_schema(openapi_spec, resource)
            request_body_schema = get_request_body_schema(
                openapi_spec, resource)

            request_params = {"query": {}, "header": {}, "path": {}}

            for param_type in request_params.keys():
                request_params[param_type] = derive_params(
                    connection_specification=connection_specification,
                    parameters=[
                        param for param in parameters if param["in"] == param_type],
                    excluded=banned_params.get(param_type, [])
                )

            for param, value in request_params["path"].items():
                path = path.replace(
                    f"{{{param}}}", value)

            top_level_properties = determine_top_level_props(response_schema)

            result_schema = {}

            for key in top_level_properties:
                if key == "*":
                    result_schema = response_schema
                    break
                else:
                    result_schema[key] = response_schema.get(
                        "properties", {}).get(key)

            primary_key = determine_primary_key(result_schema)

            body_json = map_request_body(
                connection_specification=connection_specification,
                banned_params=banned_params,
                data=request_body_schema
            )

            stream = {
                "name": name,
                "primary_key": primary_key,
                "type": "DeclarativeStream",
                "retriever": {
                    "type": "SimpleRetriever",
                    "record_selector": {
                        "type": "RecordSelector",
                        "extractor": {
                            "type": "DpathExtractor",
                            "field_path": top_level_properties,
                        },
                    },
                    "paginator": paginator if paginator else {"type": "NoPagination"},
                    "requester": {
                        "authenticator": authenticator,
                        "http_method": method.upper(),
                        "path": path,
                        "type": "HttpRequester",
                        "url_base": url_base,
                        "request_parameters": request_params["query"],
                        "request_headers": request_params["header"],
                        "request_body_json": body_json
                    }
                }
            }

            streams.append(stream)

    connector_yaml = {
        "streams": streams,
        "check": {
            "stream_names": [stream["name"] for stream in streams],
            "type": "CheckStream",
        },
        "spec": {
            "connection_specification": connection_specification,
            "type": "Spec",
        },
        "type": "DeclarativeSource",
        "version": "0.65.0"
    }

    return connector_yaml


def validate_airbyte_connector(connector: dict):
    with open(os.path.join(AIRBYTE_PATH, "airbyte_schema.yaml"), "r") as file:
        airbyte_schema = yaml.safe_load(file)

    try:
        jsonschema.validators.validate(connector, airbyte_schema)
        logger.info("Connector is valid")
    except jsonschema.exceptions.ValidationError as e:
        logger.error("Connector is invalid: %s", e)
        raise e


if __name__ == "__main__":
    with open("openapi.yaml", "r") as file:
        openapi_spec = yaml.safe_load(file)

    airbyte_connector = generate_airbyte_connector(openapi_spec)

    with open("airbyte_connector.yaml", "w") as file:
        yaml.safe_dump(airbyte_connector, file)

    validate_airbyte_connector(airbyte_connector)
