#!/usr/bin/env python

import os
import datetime
import requests
import urllib

# https://weibo.com/newlogin?tabtype=search
feed_urls = [
    'https://weibo.com/ajax/side/hotSearch'
]
news_url = 'https://s.weibo.com/weibo?q={hash1}{key}{hash2}'

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')

    rss = []
    for url in feed_urls:
        resp = requests.get(url)
        feed = resp.json()
        if 'data' in feed and 'realtime' in feed['data']:
            for entry in feed['data']['realtime']:
                item = {
                    'title': entry['word'],
                    'link': news_url.format(hash1=urllib.parse.quote('#'), key=entry['word'], hash2=urllib.parse.quote('#'))
                }
                rss.append(item)
                if len(rss) == 3:
                    break

    md = '## 微博热搜-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = '微博热搜-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
