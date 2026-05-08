import json
from xml2json import Schema, convert
from lxml import etree


def load_as_json_using_schema(filename: str, schemafile: str):
    if filename.endswith(".xml"):
        tree = etree.parse(filename)
        json_string = convert(filename, schemafile)
        json_input = json.loads(json_string)
    elif filename.endswith(".json"):
        with open(filename) as f:
            json_input = json.load(f)

    return json_input


def find(a_dict, simplified_xpath, default_value=None):
    paths = simplified_xpath.split("/")
    elem = a_dict
    for path in paths:
        elem = elem.get(path)
        if elem is None:
            return default_value

    return elem


def xpath_dict(data, path):
    """
    Simple XPath-like lookup for nested dict/list structures.

    Supported:
    - "/" path separator
    """

    parts = [p for p in path.strip("/").split("/") if p]

    def _search(current, remaining):
        if not remaining:
            if isinstance(current, list):
                return current
            else:
                return [current]

        key = remaining[0]
        rest = remaining[1:]
        results = []

        if isinstance(current, dict):
            if key in current:
                results.extend(_search(current[key], rest))

        elif isinstance(current, list):
            try:
                idx = int(key)
                if 0 <= idx < len(current):
                    results.extend(_search(current[idx], rest))
            except ValueError:
                for item in current:
                    results.extend(_search(item, remaining))

        return results

    return _search(data, parts)


def replace(
    value,
    current_key,
    renamings: dict[str, str],
    value_transforms: dict,
    keys_to_drop: dict[str, [str]],
    type_mappings: dict[str, str],
    keys_to_pull_up: dict[str, list[str]],
):
    # renamings: dict of old keys which shall be replaced by new keys
    # keys_to_drop: dict of keys which should be removed from dicts, if their parent key equals keys_to_drop[key]'s value (or value is None)
    # type_mappings: dict of type values which, if present as 'type': type_mapping_key will result in an object {type_mapping_value: {} }
    # keys_to_pull_up: list of keys, which will be replaced by the key/value pairs of its value dict
    if isinstance(value, dict):
        # iterate over keys
        new_dict = {}
        for key in value:
            if (
                not value[key] is None
                and not (
                    key in keys_to_drop
                    and (keys_to_drop[key] is None or current_key in keys_to_drop[key])
                )
                and not (key == "type" and value["type"] in type_mappings)
            ):
                replaced = replace(
                    value[key],
                    key,
                    renamings,
                    value_transforms,
                    keys_to_drop,
                    type_mappings,
                    keys_to_pull_up,
                )

                new_dict[renamings.get(key, key)] = replaced

        for parent_key, children_keys in keys_to_pull_up.items():
            if parent_key in new_dict:
                if children_keys and len(children_keys) > 0:
                    # copy only intended children
                    for child_key in children_keys:
                        if child_key in new_dict[parent_key]:
                            new_dict[child_key] = new_dict[parent_key].pop(child_key)
                else:
                    # copy only intended children
                    dict_to_merge = new_dict.pop(parent_key)
                    new_dict = new_dict | dict_to_merge

        if "@xsi:type" in value and value["@xsi:type"] in type_mappings:
            new_dict = {type_mappings[value["@xsi:type"]]: new_dict}

        if current_key is not None and current_key in value_transforms:
            return value_transforms[current_key](new_dict)
        return new_dict
    if isinstance(value, list):
        return [
            replace(
                v,
                current_key,
                renamings,
                value_transforms,
                keys_to_drop,
                type_mappings,
                keys_to_pull_up,
            )
            for v in value
            if v is not None
        ]
    else:
        return (
            value_transforms[current_key](value)
            if current_key is not None and current_key in value_transforms
            else value
        )
