"""Dialy Box Bot."""
import os
import shutil
from pathlib import Path
import json
import time
import datetime
import dateutil.parser
import dateparser
import feedparser
import requests


def load_feed_conf():
    """Load configuration."""
    with open('feed.json', mode='r', encoding='utf-8') as f:
        conf = json.load(f)

    return conf


def publish_md(items):
    """Publish to markdown."""
    categorys = ['博客', '播客', '视频', '日报', '资讯', '开源', '漫游']
    categorys_obj = {category: [] for category in categorys}
    today_str = datetime.datetime.today().strftime('%Y%m%d')
    fname = f'docs/daily-box-{today_str}.md'

    txt = f'# Daily Box {today_str}\n生活就像一盒巧克力，你永远不知道你会得到什么。\n\n'

    for item in items:
        if item['category'] in categorys:
            categorys_obj[item['category']].append(item)

    for category in categorys:
        txt += f'## {category}\n'
        if not categorys_obj[category]:
            txt += '- N/A\n'
        else:
            for item in categorys_obj[category]:
                txt += f'- {item["channel"]} | [{item["title"]}]({item["link"]})\n'
        txt += '\n'

    txt += 'EOF'
    print(txt)

    Path("docs").mkdir(parents=True, exist_ok=True)
    if not os.path.isfile(fname):
        fd = open(fname, mode='w', encoding='utf-8')
        fd.write(txt)
        fd.close()
        shutil.copy(fname, 'README.md')


def main():
    """Main loop."""
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
                published = entry.get('published_parsed' if entry.has_key(
                    'published_parsed') else 'updated_parsed', today)
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
                    res = requests.post(url, json=payload, timeout=10)
                else:
                    res = requests.post(url, timeout=10)
            else:
                res = requests.get(url, timeout=10)
            resp = res.json()
            keys = api['response']['list'].split('.')
            l = len(keys)
            if l == 1 and keys[0] in resp:
                entries = resp[keys[0]]
            elif l == 2 and keys[0] in resp and keys[1] in resp[keys[0]]:
                entries = resp[keys[0]][keys[1]]
            elif l == 3 and keys[0] in resp and keys[1] in resp[keys[0]] \
                and keys[2] in resp[keys[0]][keys[1]]:
                entries = resp[keys[0]][keys[1]][keys[2]]
            else:
                print(f'{api["url"]} response error')
                continue

            title = api['entry']['title']
            link = api['entry']['link']
            date = api['entry']['date']
            placeholder = link.split('{')[1].split('}')[0]
            i = 0
            for entry in entries:
                if '8点1氪' == api['channel']:
                    if 'templateMaterial' in entry:
                        entry = entry['templateMaterial']
                if isinstance(entry[date], int):
                    if '8点1氪' == api['channel']:
                        published = datetime.datetime.fromtimestamp(
                            entry[date] / 1000)
                    else:
                        published = datetime.datetime.fromtimestamp(
                            entry[date])
                else:
                    if '晚点早知道' == api['channel']:
                        published = dateparser.parse(entry[date])  # '今天'/'昨天'
                    elif '先锋作品' == api['channel'] or '上周热门' == api['channel']:
                        # '1.9小时前'/'1680614161357'
                        published = dateparser.parse(entry[date])
                    else:
                        published = dateutil.parser.parse(entry[date])
                if not published or published < yesterday:
                    continue
                if '网易轻松一刻' == api['channel']:
                    if not 'source' in entry or not '轻松一刻' == entry['source']:
                        continue
                if '喷嚏网' == api['channel']:
                    if not '喷嚏图卦' in entry.title:
                        continue
                if '晚点早知道' == api['channel']:
                    if not entry['programa'] == '3':
                        continue
                if '极客早知道' == api['channel'] and i >= 3:
                    break
                if '先锋作品' == api['channel'] and i >= 3:
                    break
                if '微博热搜' == api['channel'] and i >= 3:
                    break
                if '什么值得买|文章榜' == api['channel'] and i >= 3:
                    break
                link_map = {placeholder: entry[placeholder]}
                item = {
                    'category': api['category'],
                    'channel': api['channel'],
                    'title': entry[title],
                    'link': link.format_map(link_map)
                }
                items.append(item)
                i = i + 1
                print(item)

        publish_md(items)


if __name__ == '__main__':
    main()
