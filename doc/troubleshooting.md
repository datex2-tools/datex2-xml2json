# Troubleshooting

As the mapping is built bottom up and not derived from a specification, there will be gaps.
Follwoing hints should help troubleshooting these by giving hints which common errors may happen and how they can be fixed.

## ...disturbanceActivityType: 'demonstration' is not of type 'object'
This error is usually caused by a property not wrapped as value.
Adding `'disturbanceActivityType': wrap_with_value` to `transformation_rules.py` might help.


## .routeDestination[0]: Additional properties are not allowed ('area' was unexpected)
Probably, the area element should be wrapped by a wrapper object in DATEXII JSON.
Check the original xml if the parent routeDestination element has an xsi type, which should be mapped to a wrapped object. In this case `xsi:type="AreaDestination"` requires a mapping `AreaDestination": "locAreaDestination"` in `transformation_rules.py`'s `datex_xml_2_json_xsitype_mappings` dict.
In addition, `Area` needs to be renamed to `AreaLocation`

## alertCArea: {'alertCLocationCountryCode': 'D', ...} is not of type 'array'
In v2, alertCArea was implicitly maxOccurs 1 <xs:element name="alertCArea" type="D2LogicalModel:AlertCArea" minOccurs="0". In v3 ist unbounded: name="alertCArea" type="loc:AlertCArea" minOccurs="0" maxOccurs="unbounded"
It's value needs to be wrapped in an array: Add `"alertCArea": lambda v: [v],` to `value_transforms`.