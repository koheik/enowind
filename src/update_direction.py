import os
import json
import io

import boto3
from boto3.dynamodb.conditions import Key, Attr

eng_map = {
	'0':     'N',
	'22.5':  'NNE',
	'45':    'NE',
	'67.5':  'ENE',
	'90':    'E',
	'112.5': 'ESE',
	'135':   'SE',
	'157.5': 'SSE',
	'180':   'S'
}
def update(table_name, bucket_name):
	KNOTS = 1852 / 3600.0
	dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
	s3 = boto3.client('s3', region_name='ap-northeast-1')

	table = dynamodb.Table(table_name)

	response = table.scan()

	for itm in response['Items']:
		if (("tem`perature" in itm) and
			(itm["tem`perature"] == 0)):
			del itm["tem`perature"]
			table.put_item(Item=itm)


		# if ('average_wind_direction_eng' in itm):
		# 	continue
		# if (itm['average_wind_direction'] == '22.5'):
		# 	print(itm)

if __name__ == '__main__':
	update('Enowind2-DataTable-', '')