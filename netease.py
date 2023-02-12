#!/usr/bin/env python

import os
import datetime
import requests

# https://3g.163.com/touch/exclusive/sub/qsyk
feed_urls = [
    'https://c.m.163.com/nc/article/headline/T1350383429665/0-10.html'
]

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')

    rss = []
    for url in feed_urls:
        resp = requests.get(url)
        feed = resp.json()
        if 'T1350383429665' in feed:
            for entry in feed['T1350383429665']:
                if '轻松一刻' == entry['source']:
                    published_date = datetime.datetime.strptime(entry['ptime'], '%Y-%m-%d %H:%M:%S')
                    if today == published_date.strftime('%Y%m%d'):
                        item = {
                            'title': entry['title'],
                            'link': entry['url']
                        }
                        rss.append(item)

    if not rss:
        print('no update')
        return

    md = '## 轻松一刻-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = '轻松一刻-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
