#!/usr/bin/env python

import os
import datetime
import requests

# https://github.com/trending?since=daily
# http://developer.github.com/v3/search/#search-repositories
# https://docs.github.com/en/search-github/searching-on-github/searching-for-repositories
# https://github.com/search/advanced
# https://gist.github.com/jasonrudolph/6065289#find-the-hottest-repositories-created-in-the-last-week
# curl -H "Accept: application/vnd.github+json" "https://api.github.com/search/repositories?q=created:>2023-02-10 stars:>100 forks:>10&sort=stars&order=desc&per_page=10"
feed_urls = [
    'https://api.github.com/search/repositories?q=created:>{date} stars:>100 forks:>10&sort=stars&order=desc&per_page=10'
]

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')
    yesterday = (datetime.datetime.now() - datetime.timedelta(7)).strftime('%Y-%m-%d')

    rss = []
    for url in feed_urls:
        resp = requests.get(url.format(date=yesterday))
        feed = resp.json()
        if 'items' in feed:
            for entry in feed['items']:
                item = {
                    'title': entry['full_name'],
                    'link': entry['html_url']
                }
                rss.append(item)

    if not rss:
        print('no update')
        return

    md = '## GitHub新锐榜' + today + '\n'
    for item in rss:
        md += '[' + item['title'] + ']' + '(' + item['link'] + ')' + '\n'

    fname = 'GitHub新锐榜-' + today + '.md'
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(md)
        fd.close()
    else:
        print(fname + ' exist')

if __name__ == '__main__':
    main()
