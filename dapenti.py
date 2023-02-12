#!/usr/bin/env python

import os
import datetime
import feedparser

# http://www.dapenti.com/blog/blog.asp?subjectid=70&name=xilei
feed_urls = [
    'https://www.dapenti.com/blog/rss2.asp?name=xilei'
]

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')

    rss = []
    for url in feed_urls:
        feed = feedparser.parse(url)
        if feed.has_key('entries'):
            for entry in feed.entries:
                if '喷嚏图卦' in entry.title:
                    published_date = datetime.datetime.strptime(entry['published'], '%a, %d %b %Y %H:%M:%S %z')
                    if today == published_date.strftime('%Y%m%d'):
                        item = {
                            'title': entry.title,
                            'link': entry.link
                        }
                        rss.append(item)

    if not rss:
        print('no update')
        return

    md = '## 喷嚏图卦-' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = '喷嚏图卦-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
