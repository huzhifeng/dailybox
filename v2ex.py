#!/usr/bin/env python

import os
import datetime
import requests

# https://www.v2ex.com/?tab=hot
# https://www.v2ex.com/t/170154
# https://v2ex.com/t/726858
feed_urls = [
    'https://www.v2ex.com/api/topics/hot.json'
]

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')

    rss = []
    for url in feed_urls:
        resp = requests.get(url)
        feed = resp.json()
        if feed:
            for entry in feed:
                published_date = datetime.datetime.fromtimestamp(entry['created'])
                if today == published_date.strftime('%Y%m%d'):
                    item = {
                        'title': entry['title'],
                        'link': entry['url']
                    }
                    rss.append(item)

    if not rss:
        print('no update')
        return

    md = '## 今日热议-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = '今日热议-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
