"""Dialy Box Bot."""
import os
import shutil
from pathlib import Path
import json
import logging
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
    categories_obj = {}
    tags_obj = {}
    today_str = datetime.datetime.today().strftime('%Y%m%d')
    fname_daily_box = f'archives/daily-box-{today_str}.md'
    md_daily_box = f'# Daily Box {today_str}\n\n'

    for item in items:
        category = item['category']
        if not category in categories_obj:
            categories_obj[category] = ''

        tags = item['tags'] if 'tags' in item else [];
        for tag in tags:
            if not tag in tags_obj:
                tags_obj[tag] = ''

        md_entry = ''
        if '语录' == category:
            if item['origin']:
                md_entry = f'- "{item["content"]}" - {item["author"]} 《{item["origin"]}》\n'
            else:
                md_entry = f'- "{item["content"]}" - {item["author"]}\n'
        else:
            md_entry = f'- [{item["channel"]}]({item["portal"]}) | [{item["title"]}]({item["link"]})\n'

        categories_obj[category] += md_entry
        for tag in tags:
            tags_obj[tag] += md_entry

    for category in categories_obj:
        md_daily_box += f'## {category}\n'
        md_daily_box += f'{categories_obj[category]}\n'
        md_category = f'## {today_str}\n{categories_obj[category]}\n'
        Path('categories').mkdir(parents=True, exist_ok=True)
        fname_category = f'categories/{category}.md'
        md_old = ''
        if os.path.isfile(fname_category):
            with open(fname_category, mode='r', encoding='utf-8') as fd_category_old:
                md_old = fd_category_old.read()
        with open(fname_category, mode='w', encoding='utf-8') as fd_category_new:
            fd_category_new.write(f'{md_category}{md_old}')

    md_daily_box += 'EOF'
    print(md_daily_box)

    Path('archives').mkdir(parents=True, exist_ok=True)
    if not os.path.isfile(fname_daily_box):
        fd_daily_box = open(fname_daily_box, mode='w', encoding='utf-8')
        fd_daily_box.write(md_daily_box)
        fd_daily_box.close()
        shutil.copy(fname_daily_box, 'README.md')

    for tag in tags_obj:
        md_tag = f'## {today_str}\n{tags_obj[tag]}\n'
        Path('tags').mkdir(parents=True, exist_ok=True)
        fname_tag = f'tags/{tag}.md'
        md_old = ''
        if os.path.isfile(fname_tag):
            with open(fname_tag, mode='r', encoding='utf-8') as fd_tag_old:
                md_old = fd_tag_old.read()
        with open(fname_tag, mode='w', encoding='utf-8') as fd_tag_new:
            fd_tag_new.write(f'{md_tag}{md_old}')


def main():
    """Main loop."""
    today = datetime.datetime.today()
    yesterday = today - datetime.timedelta(days=1)
    lastweek = today - datetime.timedelta(weeks=1)
    ts = datetime.datetime.now().timestamp()
    conf = load_feed_conf()
    items = []

    logger = logging.getLogger(__name__)
    logger.setLevel(os.environ.get('LOGLEVEL', 'INFO'))
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)

    if 'feed' in conf:
        for feed in conf['feed']:
            if 'enable' in feed and feed['enable'] == 0:
                continue
            try:
                logger.debug(feed['url'])
                d = feedparser.parse(feed['url'], modified=yesterday)
            except Exception as e:
                logger.warning(e)
                continue
            updated = d.feed.get('updated_parsed', today)
            if isinstance(updated, time.struct_time):
                updated = datetime.datetime(*updated[:6])
            if updated < yesterday:
                continue
            if not d.has_key('entries'):
                logger.debug('no entries')
                continue

            i = 0
            for entry in d.entries:
                if i >= 3:
                    break
                if '喷嚏网' == feed['channel']:
                    if not '喷嚏图卦' in entry.title:
                        continue
                elif '津津乐道' == feed['channel']:
                    if not '科技乱炖' in entry.title and not '编码人声' in entry.title:
                        continue
                elif '硬核观察' == feed['channel']:
                    if not '硬核观察' in entry.title:
                        continue
                elif '泰晓资讯' == feed['channel']:
                    if not '泰晓资讯' in entry.title:
                        continue
                elif 'Hacker News' == feed['channel']:
                    if 'comments' in entry:
                        entry.link = entry.comments
                elif '科技早知道' == feed['channel']:
                    if 'itunes_episode' in entry:
                        entry.link = f'https://guiguzaozhidao.fireside.fm/{entry.itunes_episode}'
                published = entry.get('published_parsed' if entry.has_key(
                    'published_parsed') else 'updated_parsed', today)
                if isinstance(published, time.struct_time):
                    published = datetime.datetime(*published[:6])
                if not published or published < yesterday:
                    continue
                item = {
                    'category': feed['category'],
                    'tags': feed['tags'],
                    'channel': feed['channel'],
                    'portal': feed['portal'],
                    'title': entry.title,
                    'link': entry.link
                }
                if '周刊' in item['title'] or 'Weekly'.casefold() in item['title'].casefold():
                    item['tags'].append('周刊')
                items.append(item)
                i = i + 1
                logger.debug(item)

    if 'api' in conf:
        for api in conf['api']:
            if 'enable' in api and api['enable'] == 0:
                continue
            method = api['request']['method']
            url = api['url']
            logger.debug(url)
            if method == 'post':
                if 'payload' in api['request']:
                    payload = api['request']['payload']
                    if '8点1氪' == api['channel']:
                        payload['timestamp'] = ts * 1000
                    elif 'Product Hunt' == api['channel']:
                        payload['variables']['year'] = today.year
                        payload['variables']['month'] = today.month
                        payload['variables']['day'] = today.day
                    try:
                        res = requests.post(url, json=payload, timeout=30)
                        res.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        logger.warning(e)
                        continue
                else:
                    try:
                        res = requests.post(url, timeout=30)
                        res.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        logger.warning(e)
                        continue
            else:
                if 'GitHub Advanced Search' == api['channel']:
                    url = url.format(date=lastweek.strftime('%Y-%m-%d'))
                try:
                    res = requests.get(url, timeout=30)
                    res.raise_for_status()
                except requests.exceptions.RequestException as e:
                    logger.warning(e)
                    continue
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
                logger.debug(f'{url} response error')
                continue

            title = api['entry']['title']
            link = api['entry']['link']
            date = api['entry']['date']
            placeholder = link.split('{')[1].split('}')[0]
            i = 0
            for entry in entries:
                if i >= 3:
                    break
                if '8点1氪' == api['channel']:
                    if 'templateMaterial' in entry:
                        entry = entry['templateMaterial']
                elif 'Product Hunt' == api['channel']:
                    if 'node' in entry:
                        entry = entry['node']

                if isinstance(entry[date], int):
                    if '8点1氪' == api['channel']:
                        published = datetime.datetime.fromtimestamp(
                            entry[date] / 1000)
                    else:
                        published = datetime.datetime.fromtimestamp(
                            entry[date])
                else:
                    if '晚点早知道' == api['channel']:
                        published = dateparser.parse(entry[date])  # '今天' or '昨天'
                    elif '竹白先锋作品' == api['channel'] or '竹白新锐作品' == api['channel'] or '竹白上周热门' == api['channel']:
                        # '1.9小时前' or '1680614161357'
                        published = dateparser.parse(entry[date])
                    elif 'GitHub中文社区' == api['channel'] or 'GitHub Advanced Search' == api['channel'] or 'Product Hunt' == api['channel']:
                        # '2023-04-07T10:38:28Z' or '2023-04-10T00:01:00-07:00'
                        published = dateparser.parse(entry[date])
                        published = published.replace(tzinfo=None)
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
                link_map = {placeholder: entry[placeholder]}
                item = {
                    'category': api['category'],
                    'tags': api['tags'],
                    'channel': api['channel'],
                    'portal': api['portal'],
                    'title': entry[title],
                    'link': link.format_map(link_map)
                }
                items.append(item)
                i = i + 1
                logger.debug(item)

    if 'quote' in conf:
        for quote in conf['quote']:
            if 'enable' in quote and quote['enable'] == 0:
                continue
            url = quote['url']
            try:
                logger.debug(url)
                res = requests.get(url, timeout=30)
                res.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.warning(e)
                continue
            entry = res.json()
            if not quote['content'] in entry or not entry[quote['content']]:
                continue
            if not quote['author'] in entry or not entry[quote['author']]:
                continue
            if 'origin' in quote and quote['origin'] in entry and entry[quote['origin']]:
                origin = entry[quote['origin']]
            else:
                origin = ''
            item = {
                'category': quote['category'],
                'tags': quote['tags'] if 'tags' in quote else [quote['category']],
                'content': entry[quote['content']],
                'origin': origin,
                'author': entry[quote['author']]
            }
            items.append(item)
            logger.debug(item)

    publish_md(items)


if __name__ == '__main__':
    main()
