"""Dialy Box Bot."""
import os
from pathlib import Path
import json
import logging
import socket
import time
import datetime
import dateutil.parser
import dateparser
import pytz
import feedparser
import requests
import xml


def check_url_in_tag_file(tag, link):
    """Check if the URL already exists"""
    fname_tag = f'tags/{tag}.md'

    if os.path.isfile(fname_tag):
        with open(fname_tag, mode='r', encoding='utf-8') as fd_tag:
            txt = fd_tag.read()
            if txt.find(link) != -1:
                return True

    return False

def main():
    """Main loop."""
    timezone = pytz.timezone('Asia/Shanghai')
    now = datetime.datetime.now(timezone)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    yesterday = today - datetime.timedelta(days=1)
    tomorrow = today + datetime.timedelta(days=1)
    lastweek = today - datetime.timedelta(weeks=1)
    timestamp = datetime.datetime.now().timestamp()
    items = []
    request_timeout = int(os.getenv('TIMEOUT', '180'))
    entry_limit = int(os.getenv('LIMIT', '1'))
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) '\
        'AppleWebKit/537.36 (KHTML, like Gecko) '\
        'Chrome/109.0.0.0 Safari/537.36'
    request_headers = {
        'user-agent': user_agent
    }
    feedparser.USER_AGENT = user_agent
    socket.setdefaulttimeout(request_timeout)

    logger = logging.getLogger(__name__)
    logger.setLevel(os.environ.get('LOGLEVEL', 'INFO'))
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)

    conf = {}
    with open('feed.json', mode='r', encoding='utf-8') as fd_conf:
        conf = json.load(fd_conf)

    if 'feed' in conf:
        for feed in conf['feed']:
            if 'enable' in feed and feed['enable'] == 0:
                continue
            logger.debug(feed['url'])
            try:
                resp = feedparser.parse(
                    feed['url'], request_headers=request_headers)
            except TimeoutError as e_timeout:
                logger.warning(e_timeout)
                continue
            except Exception as e_req:
                logger.warning(e_req)
                continue
            if resp.bozo:
                logger.warning('bozo exception: %s', resp.bozo_exception)
                if isinstance(resp.bozo_exception, feedparser.exceptions.CharacterEncodingOverride):
                    # Validate a feed online:
                    # https://validator.w3.org/feed/
                    # Handling Incorrectly-Declared Encodings:
                    # https://pythonhosted.org/feedparser/character-encoding.html#handling-incorrectly-declared-encodings
                    logger.info(
                        'Ignore warning: document declared as us-ascii, but parsed as utf-8')
                elif isinstance(resp.bozo_exception, xml.sax._exceptions.SAXParseException):
                    # fix exception 'junk after document element' for https://www.oschina.net/news/rss
                    logger.info(
                        'Ignore SAXParseException: Extra content at the end of the document')
                else:
                    logger.warning('Other bozo exception, please attention')
                    continue
            updated = resp.feed.get('updated_parsed', today)
            if isinstance(updated, time.struct_time):
                updated = datetime.datetime(*updated[:6])
            if updated < today:
                logger.debug('updated date(%s) < today(%s), feed: %s', updated, today, feed['channel'])
                if 'ignoredate' in feed and feed['ignoredate'] == 1:
                    logger.debug('ignore date')
                else:
                    continue
            if not resp.has_key('entries'):
                logger.debug('no entries')
                continue
            if 'filter' in feed and len(feed['filter']) > 0:
                resp.entries = [entry for entry in resp.entries
                                if any(k in entry.title for k in feed['filter'])]

            i = 0
            for entry in resp.entries:
                if i >= entry_limit:
                    break
                if 'Hacker News' == feed['channel'] \
                        or 'Lobsters' == feed['channel']:
                    if 'comments' in entry:
                        entry.link = entry.comments
                elif 'Slashdot' == feed['channel']:
                    if 'slash_comments' in entry and int(entry['slash_comments']) < 10:
                        continue
                published = entry.get('published_parsed' if entry.has_key(
                    'published_parsed') else 'updated_parsed', today)
                if isinstance(published, time.struct_time):
                    published = datetime.datetime(*published[:6])
                if not published:
                    if '喷嚏网' == feed['channel']:
                        if 'Wes' in entry.published:
                            # typo, Wes should be Wed
                            published = dateparser.parse(
                                entry.published.replace('Wes', 'Wed'))
                            published = published.replace(tzinfo=None)
                    else:
                        continue
                if published.date() != today.date():
                    logger.debug('published date(%s) != today(%s), feed %s, entry: %s %s',
                                    published, today, feed['channel'], entry.title, entry.link)
                    if 'ignoredate' in feed and feed['ignoredate'] == 1:
                        logger.debug('ignore published date, check url instead')
                        if check_url_in_tag_file(feed['tags'][0], entry.link):
                            continue
                    else:
                        continue
                item = {
                    'category': feed['category'],
                    'tags': feed['tags'].copy(),
                    'channel': feed['channel'],
                    'portal': feed['portal'],
                    'title': entry.title,
                    'link': entry.link
                }
                if '周刊' in item['title'] \
                        or 'Weekly'.casefold() in item['title'].casefold():
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
                        payload['timestamp'] = timestamp * 1000
                    elif 'Product Hunt' == api['channel']:
                        payload['variables']['year'] = today.year
                        payload['variables']['month'] = today.month
                        payload['variables']['day'] = yesterday.day
                    try:
                        resp = requests.post(
                            url, json=payload, timeout=request_timeout, headers=request_headers)
                        resp.raise_for_status()
                    except requests.exceptions.RequestException as e_req:
                        logger.warning(e_req)
                        continue
                else:
                    try:
                        resp = requests.post(
                            url, timeout=request_timeout, headers=request_headers)
                        resp.raise_for_status()
                    except requests.exceptions.RequestException as e_req:
                        logger.warning(e_req)
                        continue
            else:
                if 'GitHub Advanced Search' == api['channel']:
                    url = url.format(date=lastweek.strftime('%Y-%m-%d'))
                try:
                    resp = requests.get(
                        url, timeout=request_timeout, headers=request_headers)
                    resp.raise_for_status()
                except requests.exceptions.RequestException as e_req:
                    logger.warning(e_req)
                    continue
            resp_json = resp.json()
            keys = api['response']['list'].split('.')
            nesting_level = len(keys)
            if nesting_level == 1:
                if not keys[0]:
                    entries = resp_json
                elif keys[0] in resp_json:
                    entries = resp_json[keys[0]]
                else:
                    logger.debug('%s response error', url)
                    continue
            elif nesting_level == 2 and keys[0] in resp_json and keys[1] in resp_json[keys[0]]:
                entries = resp_json[keys[0]][keys[1]]
            elif nesting_level == 3 and keys[0] in resp_json and keys[1] in resp_json[keys[0]] \
                    and keys[2] in resp_json[keys[0]][keys[1]]:
                entries = resp_json[keys[0]][keys[1]][keys[2]]
            else:
                logger.debug('%s response error', url)
                continue

            title = api['entry']['title']
            link = api['entry']['link']
            date = api['entry']['date']
            placeholder = link.split('{')[1].split('}')[0]
            i = 0
            for entry in entries:
                if i >= entry_limit:
                    break
                if '8点1氪' == api['channel']:
                    if 'templateMaterial' in entry:
                        entry = entry['templateMaterial']
                elif 'Product Hunt' == api['channel']:
                    if 'node' in entry:
                        entry = entry['node']

                if date not in entry:
                    continue
                elif isinstance(entry[date], int):
                    if '8点1氪' == api['channel']:
                        published = datetime.datetime.fromtimestamp(
                            entry[date] / 1000)
                    else:
                        published = datetime.datetime.fromtimestamp(
                            entry[date])
                else:
                    if '晚点早知道' == api['channel']:
                        published = dateparser.parse(
                            entry[date])  # '今天' or '昨天'
                    elif '竹白先锋作品' == api['channel'] \
                            or '竹白新锐作品' == api['channel'] \
                            or '竹白上周热门' == api['channel']:
                        # '1.9小时前' or '1680614161357'
                        published = dateparser.parse(entry[date])
                    elif 'GitHub中文社区' == api['channel'] \
                            or 'GitHub Advanced Search' == api['channel'] \
                            or 'diff.blog' == api['channel'] \
                            or 'Product Hunt' == api['channel']:
                        # '2023-04-07T10:38:28Z' or '2023-04-10T00:01:00-07:00'
                        published = dateparser.parse(entry[date])
                        published = published.replace(tzinfo=None)
                    else:
                        published = dateutil.parser.parse(entry[date])
                if not published or published.date() != today.date():
                    continue
                if '晚点早知道' == api['channel']:
                    if not entry['programa'] == '3':
                        continue
                if 'Product Hunt' == api['channel']:
                    if '_score' not in entry or int(entry['_score']) < 100:
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
                if 'Product Hunt' == api['channel']:
                    if '_title_prefix' in entry and '_links' in entry:
                        item['title'] = entry['_title_prefix'].removesuffix(
                            ' - ')
                        item['link'] = entry['_links'][0]['url']
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
                resp = requests.get(
                    url, timeout=request_timeout, headers=request_headers,verify=False)
                resp.raise_for_status()
            except requests.exceptions.RequestException as e_req:
                logger.warning(e_req)
                continue
            entry = resp.json()
            if quote['content'] not in entry or not entry[quote['content']]:
                continue
            if quote['author'] not in entry or not entry[quote['author']]:
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

    categories_obj = {}
    tags_obj = {}
    today_str = today.strftime('%Y%m%d')
    yesterday_str = yesterday.strftime('%Y%m%d')
    tomorrow_str = tomorrow.strftime('%Y%m%d')
    fname_daily_box_today = f'archives/daily-box-{today_str}.md'
    md_daily_box = f'# Daily Box {today_str}\n\n'

    for item in items:
        category = item['category']
        if category not in categories_obj:
            categories_obj[category] = ''

        tags = item['tags'] if 'tags' in item else []
        for tag in tags:
            if tag not in tags_obj:
                tags_obj[tag] = ''

        md_entry = ''
        if '语录' == category:
            if item['origin']:
                md_entry = f'- "{item["content"]}" - {item["author"]} 《{item["origin"]}》\n'
            else:
                md_entry = f'- "{item["content"]}" - {item["author"]}\n'
        else:
            md_entry = f'- [{item["channel"]}]({item["portal"]}) '\
                f'| [{item["title"]}]({item["link"]})\n'

        categories_obj[category] += md_entry
        for tag in tags:
            tags_obj[tag] += md_entry

    for category, category_val in categories_obj.items():
        md_daily_box += f'## {category}\n'
        md_daily_box += f'{category_val}\n'
        md_category = f'## {today_str}\n{category_val}\n'
        Path('categories').mkdir(parents=True, exist_ok=True)
        fname_category = f'categories/{category}.md'
        md_old = ''
        if os.path.isfile(fname_category):
            with open(fname_category, mode='r', encoding='utf-8') as fd_category_old:
                md_old = fd_category_old.read()
        with open(fname_category, mode='w', encoding='utf-8') as fd_category_new:
            fd_category_new.write(f'{md_category}{md_old}')

    md_daily_box += '## 更多\n'
    md_daily_box += f'- [前一天](daily-box-{yesterday_str}.md)\n'
    md_daily_box += f'- [后一天](daily-box-{tomorrow_str}.md)\n\n'
    md_daily_box += 'EOF'
    print(md_daily_box)

    Path('archives').mkdir(parents=True, exist_ok=True)
    fd_daily_box = open(fname_daily_box_today, mode='w', encoding='utf-8')
    fd_daily_box.write(md_daily_box)
    fd_daily_box.close()

    # Update README.md
    md_daily_box = md_daily_box.replace('daily-box-', 'archives/daily-box-')
    fd_readme = open('README.md', mode='w', encoding='utf-8')
    fd_readme.write(md_daily_box)
    fd_readme.close()

    for tag, tag_val in tags_obj.items():
        md_tag = f'## {today_str}\n{tag_val}\n'
        Path('tags').mkdir(parents=True, exist_ok=True)
        fname_tag = f'tags/{tag}.md'
        md_old = ''
        if os.path.isfile(fname_tag):
            with open(fname_tag, mode='r', encoding='utf-8') as fd_tag_old:
                md_old = fd_tag_old.read()
        with open(fname_tag, mode='w', encoding='utf-8') as fd_tag_new:
            fd_tag_new.write(f'{md_tag}{md_old}')


if __name__ == '__main__':
    main()
