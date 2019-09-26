import re
from bs4 import BeautifulSoup as bs
from urllib.request import Request, urlopen, URLError
from sys import exit
from os import system

def map(arr, func):
	try: return [func(x) for x in arr]
	except TypeError: 
		try: return [func(arr[i], i) for i in range(len(arr))]
		except TypeError: return [func(arr[i], i, arr) for i in range(len(arr))]

def filter(arr, func):
	try: return [x for x in arr if func(x)]
	except TypeError: 
		try: return [arr[i] for i in range(len(arr)) if func(arr[i], i)]
		except TypeError: return [arr[i] for i in range(len(arr)) if func(arr[i], i, arr)]

def open_url(url, headers={}):
	headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
	headers['Connection'] = 'keep-alive'
	while True:
		try: return bs(urlopen(Request(url, headers=headers)).read().decode('utf-8'), 'html.parser')
		except: print('There\'s an error with the connection! Retrying...')

SITE_COUNTER = 0
crawled = []
def crawl(start_url, domain_url=None, absolute_url=None, matcher=r"^.*$"):
	global SITE_COUNTER
	global crawled
	crawled.append(start_url)
	soup = open_url(start_url)
	if re.match(matcher, start_url): 
		SITE_COUNTER += 1
		yield soup, start_url
	else: print('Got unmatched URL: {}'.format(start_url))
	if domain_url == None or absolute_url == None:
		absolute_url = start_url if start_url[-1] == '/' else '{}/'.format(start_url)
		arg = start_url.split('://')
		domain_url = '{}://{}'.format('http' if len(arg) != 2 else arg[0], arg[1 if len(arg) == 2 else 0].split('/')[0])
	for a in soup.find_all('a'):
		try: url = a['href']
		except KeyError: continue

		if re.match(r'^(?!http)\/?[^\/#][^.]+$', url) and not re.match(r'^\/.+?$', url):
			url = '/{}'.format(url)
		full_url = '{}{}'.format(domain_url, url)

		if re.match(r'^http(s)?:\/\/.+$', url) or re.match(r'.+#$', full_url) or re.match(r'^#.+$', url):
			# Probably url for other site. Ignore... or url with hashes
			continue
		if re.match(r'.*?@.*', full_url): continue # Ignore E-mail

		if not full_url in crawled:
			try:
				yield from crawl(full_url, domain_url=domain_url, absolute_url=absolute_url, matcher=matcher)
			except Exception as e: print(e)

def crawl2(page=1, matcher=r'^.*$'):
	try: 
		page_url = 'https://says.com/my/stories/search?page={}&q=news'.format(page)
		for a in open_url(page_url).find_all('a', {'target': '_self'}):
			try: url = 'https://says.com{}'.format(a['href'])
			except KeyError: continue
			print(url)
			if not re.match(matcher, url): continue
			yield open_url(url), url
	except URLError as e: print(e)

def prettify(input, depth):
	if isinstance(input, list): return '[ {} ]'.format(', '.join(map(input, lambda item : prettify(item, depth))))
	elif isinstance(input, dict): return prettify_json(input, depth)
	elif input == None: return 'null'
	else: return '"{}"'.format(re.sub(r'"', '', str(input)))

def prettify_json(obj, depth=0):
	num_tabs = ''.join(['\t' for _ in range(depth)])
	return "{\n\t" + \
	num_tabs + '{}'.format((",\n\t{}").format(num_tabs).join(['{}: {}'.format(prettify(prop, depth+1), prettify(obj[prop], depth+1)) for prop in obj])) + \
	num_tabs + "\n" + num_tabs + "}"

def write_json(obj, filename='output.json'):
	with open(filename, 'w', encoding='utf-8') as file:
		file.write(prettify_json(obj))

START_URL = 'https://says.com/my/news/public-university-students-will-have-to-take-two-new-compulsory-courses'
NEWS_URL_MATCHER = r'^https://says\.com/my/news/.+$'

if __name__ == '__main__':
	# exit(0)
	i = 0
	results = {'items': []}
	for soup, url in crawl2(matcher=NEWS_URL_MATCHER):
		i += 1
		print('Got {}'.format(i))
		items = {}
		for meta in soup.find_all('meta'):
			# print(meta)
			try: 
				name, content = meta['name'], meta['content']
				if not re.match(r'^csrf-.+$', name): items[name] = content
			except KeyError as e: 
				try: 
					content, property = meta['content'], meta['property']
					if re.match(r'article:\w+?_time', property):
						args = re.split(r'[T+]', content)
						type = re.sub(r'^\w+:', '', property).replace('_time', '')
						j = 0
						for x in ['date', 'time', 'gmt']:
							items['{}_{}'.format(type, x)] = args[j]
							j += 1
					else: items[property] = content
				except KeyError: pass
		if i >= 10: break
		items['language'] = 'english'
		items['id'] = url
		items['field_article_images_caption'] = None
		results['items'].append(items)
		# print(prettify_json(items))
		# break
	write_json(results)