#!/usr/bin/env python

import os
import datetime
import feedparser

feed_urls = [
    'https://ruanyifeng.com/blog/atom.xml',
    'https://coolshell.cn/feed'
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

    md = '## RSS-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = 'RSS-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
