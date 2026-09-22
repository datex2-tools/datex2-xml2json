from datex2_xml2json.transform import CifsTransformer


def test_post_transform():
	transformer = CifsTransformer()
	incidents = {'incidents': [
	  {'id': '1487640-1487641-1487644-3508083', 'type': 'HAZARD'},
	  {
		'id': '1487640-1487641-1487644-3508083-sperrung',
		'type': 'ROAD_CLOSED',
		'polyline':[
	        [
	          8.110721,
	          47.606249
	        ],
	        [
	          8.110684,
	          47.60628
	        ]
	    ]
	},	
	]}
	expected = {
		'incidents': [
		{
		'id': '1487640-1487641-1487644-3508083-sperrung',
		'type': 'ROAD_CLOSED',
		'polyline': '47.606249 8.110721 47.60628 8.110684',
	},	
		]
	}
	actual = transformer.post_transform(incidents)
	assert expected == actual