
from bs4 import Tag

EXCLUDED_TAGS = ['script', 'svg', 'style', 'head', 'meta']


def build_html_tree(element: Tag, level=0) -> str:
    ast = ""
    if element.name and element.name not in EXCLUDED_TAGS:
        # Create a string to represent the element's attributes
        attributes = []
        for k, v in element.attrs.items():
            if k not in ["style", "class"]:
                if not isinstance(v, list):
                    attributes.append(f'{k}="{v}"')
                else:
                    exclusion_rules = ['css-', 'js-', 'r-']
                    filtered_values = []
                    for attr in v:
                        if not any(attr.startswith(rule) for rule in exclusion_rules):
                            digit_count = sum(c.isdigit() for c in attr)
                            if digit_count <= 2:
                                filtered_values.append(attr)
                    if filtered_values:
                        attributes.append(f'{k}="{" ".join(filtered_values)}"')
        attribute_str = str(" ".join(attributes))
        ast += (f"<{element.name} {attribute_str.strip()
                                   }>" if attribute_str else f"<{element.name}>").replace("\n", "").strip()
        for child in element.children:
            if isinstance(child, Tag) and child.name not in EXCLUDED_TAGS:
                ast += build_html_tree(child, level +
                                       1).replace("\n", "").strip()
        if element.name and element.name not in EXCLUDED_TAGS:
            ast += f"</{element.name}>".replace("\n", "").strip()
    return ast
