#!/usr/bin/env python

import os
import datetime
import requests

# https://www.latepost.com/news/index?proma=3
feed_urls = [
    'https://www.latepost.com/news/get-news-data'
]
news_url = 'https://www.latepost.com/news/dj_detail?id={id}'

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')
    payload = {
            'page': 1,
            'limit': 10,
            'programa': 3
    }

    rss = []
    for url in feed_urls:
        resp = requests.post(url, json = payload)
        feed = resp.json()
        if 'data' in feed:
            for entry in feed['data']:
                published_date = entry['release_time']
                if entry['programa'] == '3' and '昨天' == published_date:
                    item = {
                        'title': entry['title'],
                        'link': news_url.format(id=entry['id'])
                    }
                    rss.append(item)

    if not rss:
        print('no update')
        return

    md = '## 晚点早知道-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = '晚点早知道-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
