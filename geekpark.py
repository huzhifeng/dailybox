#!/usr/bin/env python

import os
import datetime
import requests

# https://www.geekpark.net/column/74
feed_urls = [
    'https://mainssl.geekpark.net/api/v1/columns/74'
]
news_url = 'https://www.geekpark.net/news/{id}'

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')

    rss = []
    for url in feed_urls:
        resp = requests.get(url)
        feed = resp.json()
        if 'column' in feed and 'posts' in feed['column']:
            for entry in feed['column']['posts']:
                published_date = datetime.datetime.fromtimestamp(entry['published_timestamp'])
                if today == published_date.strftime('%Y%m%d'):
                    item = {
                        'title': entry['title'],
                        'link': news_url.format(id=entry['id'])
                    }
                    rss.append(item)

    if not rss:
        print('no update')
        return

    md = '## 极客早知道-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = '极客早知道-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
