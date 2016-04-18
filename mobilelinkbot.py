#! /usr/bin/env python35

import praw
import re
import requests
import time
import urllib.parse

ID = 'XXX'
SECRET = 'XXX'
REDIRECT_URL = 'http://127.0.0.1:65010/authorize_callback'
OAUTH = 'XXX'
ACCESS_TOKEN = 'XXX'
REFRESH_TOKEN = 'XXX'

USER_AGENT = 'python:fixer.link.mobile:v1.0.0 (by /u/shittymobilelinkfixr)'
OAUTH_SCOPE = 'identity edit history read submit'

MOBILE_LINK_RE_STR = r"((?:https?://m[.]|www\d{0,3}[.]m[.]|m[.][a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
MOBILE_LINK_RE = re.compile(MOBILE_LINK_RE_STR)

LINK_RE = re.compile(r"(\[([^\]]*?)]\(" + MOBILE_LINK_RE_STR + r"\))")

test = 'https://m.youtube.com/watch?v=4Bp5jfu44Ec'
CHROME_USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'

BAD_DOMAINS = ['aliexpress']


def get_nonmobile_link(url):
    p = urllib.parse.urlparse(url)
    host = p.hostname.lower()
    for d in BAD_DOMAINS:
        if d in host:
            return None

    url = url.replace('m.', '', 1)
    if host.endswith('flickr.com'):
        if '/#/' in url:
            url = url.replace('/#/', '/')

    if url.endswith('app=m'):
        url = url[:-5]
    elif url.endswith('app=mobile'):
        url = url[:-10]

    url = url.replace('(', '\(').replace(')', '\)')
    return url, p


def handle_ratelimit(func, *args, **kwargs):
    while True:
        try:
            func(*args, **kwargs)
            break
        except praw.errors.RateLimitExceeded as error:
            print('\tSleeping for %d seconds' % error.sleep_time)
            time.sleep(error.sleep_time)


def get_mobile_links(c):
    matches = re.findall(LINK_RE, c.body)
    if matches:
        return matches
    return None


def reply(c, links, respond=False):
    head = 'Non-mobile links:\n\n'
    fixed = []

    for l in links:
        try:
            if 'mobile' in l[1].lower():
                continue

            res = requests.head(l[2], allow_redirects=True, headers={'user-agent': CHROME_USER_AGENT, 'Connection': 'close'})

            if res.status_code == 200 and re.match(MOBILE_LINK_RE, res.url):
                #new_url = res.url.replace('m.', '', 1)
                new_url, parsed = get_nonmobile_link(res.url)

                if new_url:
                    new_res = requests.head(new_url, allow_redirects=True, headers={'user-agent': CHROME_USER_AGENT})
                    new_parsed = urllib.parse.urlparse(new_res.url)
                    if new_res.status_code == 200 and parsed.path == new_parsed.path and 'content-type' in new_res.headers and 'text/html' in new_res.headers['content-type']:
                        #body += '[{}]({})\n\n'.format(l[1], new_url)
                        fixed.append('[{}]({})'.format(l[1], new_url))
                    else:
                        print('bad non mobile {}\n\t{}'.format(l, new_url))
                else:
                    print('couldnt get non mobile {}'.format(new_url))
            else:
                print('good link ' + res.url)
        except Exception as e:
            print('Exception {}'.format(l))
            print(e)

    if fixed:
        if len(fixed) > 1:
            msg = 'Non-mobile links:\n\n'
        else:
            msg = 'Non-mobile link:\n\n'
        msg += '\n\n'.join(fixed)
        print(msg)

        if respond:
            try:
                handle_ratelimit(c.reply, msg)
            except Exception as e:
                print('reply error')
                print(e)

class s:
    def __init__(self, c):
        self.body = c

if __name__ == '__main__':
    r = praw.Reddit(USER_AGENT)
    r.set_oauth_app_info(client_id=ID, client_secret=SECRET, redirect_uri=REDIRECT_URL)
    r.refresh_access_information(REFRESH_TOKEN)

    # auth_url = r.get_authorize_url('someKey', OAUTH_SCOPE, True)
    # webbrowser.open(auth_url)
    #access_info = r.get_access_information(OAUTH)
    #r.set_access_credentials(**access_info)
    #r.refresh_access_information(access_info['refresh_token'])

    user = r.get_me()
    print(user.name, user.comment_karma)

    while True:
        try:
            for c in praw.helpers.comment_stream(r, 'all', verbosity=0):
                links = get_mobile_links(c)
                if links:
                    reply(c, links, respond=True)
        except Exception as e:
            print(e)
