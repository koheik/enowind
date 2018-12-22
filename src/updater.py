from datetime import datetime
import os
import json
import io

import boto3
from boto3.dynamodb.conditions import Key, Attr

def update(table_name, bucket_name):
	KNOTS = 1852 / 3600.0
	dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
	s3 = boto3.client('s3', region_name='ap-northeast-1')

	table = dynamodb.Table(table_name)

	today = datetime.now().strftime('%Y-%m-%d')
	low = today + ' 00:00:00'
	high = today + ' 23:59:59'

	# response = table.query(
	#     KeyConditionExpression=Key('timestamp').between(low, high)
	# )

	response = table.scan(
		FilterExpression=Key('timestamp').between(low, high)
	)

	data = []
	for itm in response['Items']:
		dt = datetime.strptime(itm['timestamp'], '%Y-%m-%d %H:%M:%S')
		data.append([
			dt.strftime('%Y-%m-%d %H:%M:%S'),
			float(itm['average_wind_speed']),
			float(itm['max_wind_speed']),
			float(itm['average_wind_direction'])
		])

	data.sort()

	x = []
	y = []
	z = []
	d = []
	for r in data:
		x.append(r[0])
		y.append(round(r[1] / KNOTS, 1))
		z.append(round(r[2] / KNOTS, 1))
		d.append(r[3])

	buf = io.StringIO()

	json.dump({
		'timestamp': x,
		'average_wind_speed': y,
		'max_wind_speed': z,
		'average_wind_direction': d
	}, buf ,indent=4)

	# buf.seek(0)
	# with open('current.json', 'w') as f:
	# 	f.write(buf.read())

	buf.seek(0)
	ret = s3.put_object(
	    Body=buf.read(),
	    Bucket=bucket_name,
	    Key='current.json',
	    ACL='public-read'
	)

	buf.seek(0)
	ret = s3.put_object(
	    Body=buf.read(),
	    Bucket=bucket_name,
	    Key='data/' + today + '.json',
	    ACL='public-read'
	)

	buf.close()

if (__name__ == '__main__'):
	update('Enowind-DataTable-', 'enowind.koheik.com')
