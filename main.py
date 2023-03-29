#!/usr/bin/env python

import os
import shutil
from pathlib import Path
import json
import time
import datetime
import feedparser
import requests

def load_feed_conf():
    with open('feed.json', 'r') as f:
        conf = json.load(f)

    return conf

def publish_md(items):
    categorys = ['博客', '播客', '日报', '资讯', '开源', '漫游']
    md = { category: [] for category in categorys }
    today_str = datetime.datetime.today().strftime('%Y%m%d')
    fname = 'docs/daily-box-{0}.md'.format(today_str)

    txt = '# Daily Box {0}\n这是我每天的收件盒，正如《阿甘正传》里的台词一样“生活就像一盒巧克力，你永远不知道你会得到什么”，希望这个收件盒总能带给我探索新知的欲望和热爱生活的勇气。\n\n'.format(today_str)

    for item in items:
        if item['category'] in categorys:
            md[item['category']].append(item)

    for category in categorys:
        txt += '## {0}\n'.format(category)
        if not md[category]:
            txt += '- N/A\n'
        else:
            for item in md[category]:
                txt += '- {0} | [{1}]({2})\n'.format(item['channel'], item['title'], item['link'])
        txt += '\n'

    txt += 'EOF'
    print(txt)

    Path("docs").mkdir(parents=True, exist_ok=True)
    if not os.path.isfile(fname):
        fd = open(fname, 'w')
        fd.write(txt)
        fd.close()
        shutil.copy(fname, 'README.md')

def main():
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    ts = datetime.datetime.now().timestamp()
    conf = load_feed_conf()
    items = []

    if 'feed' in conf:
        for feed in conf['feed']:
            if 'enable' in feed and feed['enable'] == 0:
                continue
            d = feedparser.parse(feed['url'], modified=yesterday)
            updated = d.feed.get('updated_parsed', today)
            if isinstance(updated, time.struct_time):
                updated = datetime.datetime(*updated[:6])
            if updated < yesterday:
                continue
            if not d.has_key('entries'):
                print('no entries')
                continue

            for entry in d.entries:
                published = entry.get('published_parsed', today)
                if isinstance(published, time.struct_time):
                    published = datetime.datetime(*published[:6])
                if not published or published < yesterday:
                    continue
                item = {
                    'category': feed['category'],
                    'channel': feed['channel'],
                    'title': entry.title,
                    'link': entry.link
                }
                items.append(item)
                print(item)

    if 'api' in conf:
        for api in conf['api']:
            if 'enable' in api and api['enable'] == 0:
                continue
            method = api['request']['method']
            url = api['url']
            if method == 'post':
                if 'payload' in api['request']:
                    payload = api['request']['payload']
                    if '8点1氪' == api['channel']:
                        payload['timestamp'] = ts * 1000
                    res = requests.post(url, json = payload)
                else:
                    res = requests.post(url)
            else:
                res = requests.get(url)
            resp = res.json()
            keys = api['response']['list'].split('.')
            l = len(keys)
            if l == 1 and keys[0] in resp:
                entries = resp[keys[0]]
            elif l == 2 and keys[0] in resp and keys[1] in resp[keys[0]]:
                entries = resp[keys[0]][keys[1]]
            elif l == 3 and keys[0] in resp and keys[1] in resp[keys[0]] and keys[2] in resp[keys[0]][keys[1]]:
                entries = resp[keys[0]][keys[1]][keys[2]]
            else:
                print('{0} response error'.format(api['url']))
                continue

            title = api['entry']['title']
            link = api['entry']['link']
            placeholder = link.split('{')[1].split('}')[0]
            i = 0
            for entry in entries:
                if '轻松一刻' == api['channel']:
                    if not 'source' in entry or not '轻松一刻' == entry['source']:
                        continue
                if '喷嚏网' == api['channel']:
                    if not '喷嚏图卦' in entry.title:
                        continue
                if '晚点早知道' == api['channel']:
                    if not entry['programa'] == '3':
                        continue
                if '8点1氪' == api['channel']:
                    if 'templateMaterial' in entry:
                        entry = entry['templateMaterial']
                if '极客早知道' == api['channel'] and i >= 3:
                    break
                if '先锋作品' == api['channel'] and i >= 3:
                    break
                if '微博热搜' == api['channel'] and i >= 3:
                    break
                m = { placeholder: entry[placeholder] }
                item = {
                    'category': api['category'],
                    'channel': api['channel'],
                    'title': entry[title],
                    'link': link.format_map(m)
                }
                items.append(item)
                i = i + 1
                print(item)

        publish_md(items)

if __name__ == '__main__':
    main()
