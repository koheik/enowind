from datetime import datetime
import os
import re

import requests
from bs4 import BeautifulSoup
import boto3

import updater
# import plotter

def parse_table1(data, tds):
	for td in tds:
		m = re.match(r'(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s+現在', td.text)
		if (m):
			dt = datetime.strptime(m[1] + ' ' + m[2], '%Y/%m/%d %H:%M')
			data['timestamp'] = dt.strftime('%Y-%m-%d %H:%M:%S')
			data['date'] = dt.strftime('%Y-%m-%d')
			data['time'] = dt.strftime('%H:%M:%S')

	return data

def parse_table2(data, tds):
	direction = {
		'北':      0.0, '北北東':  22.5,
		'北東':   45.0, '東北東':  67.5,
		'東':     90.0, '東南東': 112.5,
		'南東':  135.0, '南南東': 157.5,
		'南':    180.0, '南南西': 202.5,
		'南西':   225.0, '西南西': 257.5,
		'西':     270.0, '西北西': 292.5,
		'北西':   315.0, '北北西': 337.5
	}

	kanji_to_eng = {
		'北':     'N', '北北東':  'NNE',
		'北東':   'NE', '東北東': 'ENE',
		'東':     'E', '東南東':  'ESE',
		'南東':   'SE', '南南東': 'SSE',
		'南':     'S', '南南西': 'SSW',
		'南西':   'SW', '西南西': 'WSW',
		'西':     'W', '西北西': 'WNW',
		'北西':   'NW', '北北西': 'NNW'
	}

	next_token = None

	for td in tds:
		m = re.match(r'(\d{4}/\d{2}/\d{2})\s+(\d{2}:\d{2})\s+現在', td.text)
		if (m):
			dt = datetime.strptime(s, '%Y/%m/%d %H:%M')
			data['updated_at'] = dt

		m = re.match(r'\s+平均風速$', td.text)
		if (m):
			next_token = 'average_wind_speed'
			continue

		m = re.match(r'\s+最大風速$', td.text)
		if (m):
			next_token = 'max_wind_speed'
			continue

		m = re.match(r'\s+平均風向$', td.text)
		if (m):
			next_token = 'average_wind_direction'
			continue

		m = re.match(r'\s+最大風速時の風向$', td.text)
		if (m):
			next_token = 'max_wind_direction'
			continue

		if (next_token == 'average_wind_speed'):
			m = re.match(r'(\d+\.\d+)\s+m/s', td.text)
			if (m):
				data[next_token] = m[1]
			next_token = None

		elif (next_token == 'max_wind_speed'):
			m = re.match(r'(\d+\.\d+)\s+m/s', td.text)
			if (m):
				data[next_token] = m[1]
			next_token = None

		elif (next_token == 'average_wind_direction'):
			m = re.match(r'\s*(\w+)\s*', td.text)
			if (m):
				data[next_token] = str(direction[m[1]])
				data[next_token + '_kanji'] = m[1]
				data[next_token + '_eng'] = kanji_to_eng[m[1]]
			next_token = None

		elif (next_token == 'max_wind_direction'):
			m = re.match(r'\s*(\w+)\s*', td.text)
			if (m):
				data[next_token] = str(direction[m[1]])
				data[next_token + '_kanji'] = m[1]
				data[next_token + '_eng'] = kanji_to_eng[m[1]]
			next_token = None

	return data

def parse_table3(data, trs):
	next_token = None
	for tr in trs:
		td = tr.find('td')
		m = re.match(r'\s+気温$', td.text)
		if (m):
			next_token = 'temperature'
			continue

		m = re.match(r'\s+現地気圧$', td.text)
		if (m):
			next_token = 'pressure'
			continue

		tds = tr.select('td')
		if (next_token == 'temperature'):
			data['temperature'] = re.sub(r'\s*(\d+\.\d+)\s+.+',r'\1', tds[0].text)
			data['humidity'] = re.sub(r'\s*(\d+\.\d+)\s+.+',r'\1', tds[2].text)
			data['effective_humidity'] = re.sub(r'\s*(\d+\.\d+)\s+.+',r'\1', tds[4].text)
			data['rain_fall'] = re.sub(r'\s*(\d+)\s+.+',r'\1', tds[6].text)
			next_token = None
		elif (next_token == 'pressure'):
			data['land_pressure'] = re.sub(r'\s*(\d+\.\d+)\s+.+',r'\1', tds[0].text)
			data['water_pressure'] = re.sub(r'\s*(\d+\.\d+)\s+.+',r'\1', tds[2].text)
			data['tide'] = re.sub(r'\s*(\d+)\s+.+',r'\1', tds[4].text)
			next_token = None

	return data

def handler(event, contenxt):
	res = requests.get('https://www.s-n-p.jp/kishou.htm')
	soup = BeautifulSoup(res.content, 'html.parser', from_encoding = 'shift-jis')

	tbls = soup.select('table')

	data = parse_table1({}, tbls[0].select('td'))
	data = parse_table2(data, tbls[1].select('td'))
	data = parse_table3(data, tbls[2].select('tr'))

	dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-1')
	table    = dynamodb.Table(os.environ['TABLE_NAME'])
	table.put_item(Item = data)

	updater.update(os.environ['TABLE_NAME'], os.environ['BUCKET_NAME'])

	return data

if (__name__ == '__main__'):
	handler({}, {})
