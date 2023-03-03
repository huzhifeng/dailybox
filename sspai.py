#!/usr/bin/env python

import os
import datetime
import requests

# https://sspai.com/tag/%E6%B4%BE%E6%97%A9%E6%8A%A5
feed_urls = [
    'https://sspai.com/api/v1/article/tag/page/get?limit=12&offset=0&tag=%E6%B4%BE%E6%97%A9%E6%8A%A5'
]
news_url = 'https://sspai.com/post/{id}'

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')

    rss = []
    for url in feed_urls:
        resp = requests.get(url)
        feed = resp.json()
        if 'data' in feed:
            for entry in feed['data']:
                published_date = datetime.datetime.fromtimestamp(entry['released_time'])
                if today == published_date.strftime('%Y%m%d'):
                    item = {
                        'title': entry['title'],
                        'link': news_url.format(id=entry['id'])
                    }
                    rss.append(item)

    if not rss:
        print('no update')
        return

    md = '## 派早报-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = '派早报-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
