#!/usr/bin/env python

import os
import json
import datetime
import feedparser
import requests

def load_feed_conf():
    with open('feed.json', 'r') as f:
        conf = json.load(f)

    return conf

def fetch_atom(url):
    feed = feedparser.parse(url)
    if not feed.has_key('entries'):
        print('error atom')
        return []
    else:
        return feed.entries

def main():
    today = datetime.datetime.today().strftime('%Y%m%d')
    ts = datetime.datetime.now().timestamp()
    conf = load_feed_conf()

    if 'atom' in conf:
        print('Atom:')
        for atom in conf['atom']:
            if 'enable' in atom and atom['enable'] == 0:
                print(atom['title'] + ' disabled')
                continue
            entries = fetch_atom(atom['feed'])
            for entry in entries:
                item = {
                    'title': entry.title,
                    'link': entry.link
                }
                print(item)

    if 'rss' in conf:
        print('RSS:')
        for rss in conf['rss']:
            if 'enable' in rss and rss['enable'] == 0:
                print(rss['title'] + ' disabled')
                continue
            entries = fetch_atom(rss['feed'])
            for entry in entries:
                item = {
                    'title': entry.title,
                    'link': entry.link
                }
                print(item)

    if 'api' in conf:
        print('API:')
        for api in conf['api']:
            if 'enable' in api and api['enable'] == 0:
                print(api['title'] + ' disabled')
                continue
            method = api['request']['method']
            url = api['feed']
            if method == 'post':
                if 'payload' in api['request']:
                    payload = api['request']['payload']
                    if '8点1氪' == api['title']:
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
                print('feed ' + api['feed'] + ' reponse error')
                continue

            title = api['entry']['title']
            link = api['entry']['link']
            placeholder = link.split('{')[1].split('}')[0]
            for entry in entries:
                if '轻松一刻' == api['title']:
                    if not 'source' in entry or not '轻松一刻' == entry['source']:
                        print('entry ' + entry[title] + ' ignore')
                        continue
                if '晚点早知道' == api['title']:
                    if not entry['programa'] == '3':
                        print('entry ' + entry[title] + ' ignore')
                        continue
                if '8点1氪' == api['title']:
                    if 'templateMaterial' in entry:
                        entry = entry['templateMaterial']
                m = { placeholder: entry[placeholder] }
                item = {
                    'title': entry[title],
                    'link': link.format_map(m)
                }
                print(item)

if __name__ == '__main__':
    main()
