#!/usr/bin/env python

import os
import datetime
import feedparser

# https://www.producthunt.com/
# https://www.producthunt.com/feed
# https://www.producthunt.com/time-travel
# https://www.producthunt.com/time-travel/2023
# https://www.producthunt.com/time-travel/2023/1
# https://www.producthunt.com/time-travel/2023/1/1
# https://www.producthunt.com/products?order=best_rated&period=2023-1
# https://github.com/producthunt/producthunt-api
# https://github.com/headllines/producthunt-daily-rss
feed_urls = [
    'https://news.ycombinator.com/rss'
]

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')

    rss = []
    for url in feed_urls:
        feed = feedparser.parse(url)
        if feed.has_key('entries'):
            for entry in feed.entries:
                item = {
                    'title': entry.title,
                    'link': entry.link
                }
                rss.append(item)

    if not rss:
        print('no update')
        return

    md = '## HN-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = 'HN-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
