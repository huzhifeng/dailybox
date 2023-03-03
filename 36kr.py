#!/usr/bin/env python

import os
import datetime
import requests

# https://36kr.com/user/5652071
# https://gateway.36kr.com/api/mis/me/article
# {"partner_id":"web","timestamp":1676644640167,"param":{"userId":"5652071","pageEvent":0,"pageSize":20,"pageCallback":"","siteId":1,"platformId":2}}
feed_urls = [
    'https://gateway.36kr.com/api/mis/me/article'
]
news_url = 'https://36kr.com/p/{id}'

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')
    ct = datetime.datetime.now()
    ts = ct.timestamp() * 1000
    payload= {
            'partner_id': 'web',
            'timestamp': ts,
            'param': {
                'userId': '5652071',
                'pageEvent': 0,
                'pageSize': 10,
                'pageCallback': '',
                'siteId': 1,
                'platformId': 2
            }
    }

    rss = []
    for url in feed_urls:
        resp = requests.post(url, json = payload)
        feed = resp.json()
        if 'data' in feed:
            for entry in feed['data']['itemList']:
                published_date = datetime.datetime.fromtimestamp(entry['templateMaterial']['publishTime'] / 1000)
                #if today == published_date.strftime('%Y%m%d'):
                if True:
                    item = {
                        'title': entry['templateMaterial']['widgetTitle'],
                        'link': news_url.format(id=entry['templateMaterial']['itemId'])
                    }
                    rss.append(item)

    if not rss:
        print('no update')
        return

    md = '## 8点1氪-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = '8点1氪-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
