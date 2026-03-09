
def find(a_dict, simplified_xpath, default_value = None):
    paths = simplified_xpath.split('/')
    elem = a_dict
    for path in paths:
        elem = elem.get(path)
        if elem is None:
            return default_value

    return elem

def replace(value, current_key, renamings: dict[str,str], value_transforms: dict, keys_to_drop: dict[str,str|None], type_mappings: dict[str, str], keys_to_pull_up: list[str]):
    # renamings: dict of old keys which shall be replaced by new keys
    # keys_to_drop: dict of keys which should be removed from dicts, if their parent key equals keys_to_drop[key]'s value (or value is None)
    # type_mappings: dict of type values which, if present as 'type': type_mapping_key will result in an object {type_mapping_value: {} } 
    # keys_to_pull_up: list of keys, which will be replaced by the key/value pairs of its value dict
    if isinstance(value, dict):
        # iterate over keys
        new_dict = {}
        for key in value:
            if not value[key] is None and not (key in keys_to_drop and (keys_to_drop[key] is None or current_key in keys_to_drop[key])) and not (key =='type' and value['type'] in type_mappings):
                replaced = replace(value[key], key, renamings, value_transforms, keys_to_drop, type_mappings, keys_to_pull_up)

                if key in keys_to_pull_up:
                    for inner_key in replaced:
                        new_dict[renamings.get(inner_key, inner_key)] = replaced[inner_key]
                else:
                    new_dict[renamings.get(key, key)] = replaced

        if '@xsi:type' in value and value['@xsi:type'] in type_mappings:
            new_dict = { type_mappings[value['@xsi:type']]: new_dict}
        
        if current_key is not None and current_key in value_transforms:
            return value_transforms[current_key](new_dict)
        return new_dict
    if isinstance(value, list):
        new_list = [replace(v, current_key, renamings, value_transforms, keys_to_drop, type_mappings, keys_to_pull_up) for v in value if v is not None]
        #return value_transforms[current_key](new_list) if current_key is not None and current_key in value_transforms else new_list
        return new_list
    else:
        return value_transforms[current_key](value) if current_key is not None and current_key in value_transforms else value

def pull_up_first_length_affected(v: dict):
    if 'carriageway' in v:
        for c in v['carriageway']:
            lengthAffected = c.pop('lengthAffected', None)
            if lengthAffected is not None:
                return v | {'lengthAffected': float(lengthAffected)}
    return v

def wrap_lroffset(lr_dict: dict):
    new_dict = {}
    for k in lr_dict:
        if k == 'openlrPositiveOffset':
            new_dict['openlrOffsets'] = {k: lr_dict[k]}
        else:
            new_dict[k] = lr_dict[k]
    return new_dict