#!/usr/bin/env python
# coding:utf-8

# Copyright (c) 2018 speaktech
# 
# This application is released under the MIT License.
# http://opensource.org/licenses/mit-license.php

"""This application translates your articles on Qiita into English ones with googletrans, and 
upload them to Qiita automatically. 

Example:
    $ python transQiita.py  [-h] [--gist] [--tweet] [--private] [--auto] [--token TOKEN]

optional arguments:
    -h, --help     show this help message and exit
    --gist         upload translated article to gist
    --tweet        tweet about translated article
    --private      set publish format to private
    --auto         execute translation and upload automatically
    --token TOKEN  set Qiita's access token

Requirements:
    googletrans, Qiita access token(Set as Environment variable QIITA_ACCESS_TOKEN)
"""

import os
import sys
import requests
import json
import textwrap
import argparse
import re
from googletrans import Translator

class QiitaArticle:
    # [START QiitaArticle]
    """Hold attributes and functions related to articles on Qiita."""
    def __init__(self, item):
        """Initialize Class holding attributes and functions related to articles on Qiita."""
        # [START __init__]
        self._title      = item['title']
        self._rendered_body  = item['rendered_body']
        self._body    = item['body']
        self._tags       = item['tags']
        self._created_at = item['created_at']
        self._updated_at = item['updated_at']
        self._url        = item['url']
        self._articleid  = item['id']
        self._private =  item['private']
        self._userid   = item['user']['id']
        self._username = item['user']['name']
        # [END __init__]

    def get_title(self):
        """Get article's title."""
        return self._title

    def get_updated_at(self):
        """Get when article was updated."""
        return self._updated_at

    def get_articleid(self):
        """Get article's id."""
        return self._articleid

    def get_private(self):
        """Get article's publish format."""
        return self._private

    def get_update_status(self):
        """Get article's update status."""
        return self._update_status

    def set_update_status(self, status):
        """Set article's update status."""
        self._update_status = status
        return self._update_status

    def detect_lang(self):
        """Detects article's language."""
        title = self._title
        translator = Translator()
        lang = translator.detect(title).lang
        return lang

    def has_banner(self,articleid):
        """Verifies whether article has a banner with the original article's id."""
        if self._body.find(articleid) >= 0:
            return True
        else:
            return False

    def _delete_redundant_space(self,original_str):
        """Deletes redundant space that breaks markdown."""
        target_dict = {
            ': |' : ':|',
            '|: ' : '|:',
            '" ' : '"',
            ' "' : '"',
            '/ ' : '/',
            ' /' : '/',
            '\\ ' : '\\',
            ' \\' : '\\',
            '$ ' : '$',
            ' $' : '$',
            '! [' : '!['
        }
        for key in target_dict:
            original_str = original_str.replace(key,target_dict[key])
        replaced_str = original_str
        return replaced_str

    def _get_translated_body(self):
        # [START _get_translated_body]
        """Gets translated article's body."""
        body  = self._body
        url = self._url
        articleid = self._articleid
        translator = Translator()

        split_body_list = body.split('```')
        chunk_size = 2000
        prefix = '\n\n```'
        suffix = '```\n\n'
        banner = '**This article is an automatic translation of the article[' + articleid + '] below.\n' + url +'**\n\n'
        translated_body = banner
        for i,element in enumerate(split_body_list):
            if i%2 == 0:
                if len(element) > chunk_size:
                    chunk_list = [element[i: i+chunk_size] for i in range(0, len(element), chunk_size)]
                    split_body_list[i] = ''
                    for chunk in chunk_list:
                        split_body_list[i] += translator.translate(chunk,dest='en').text
                else:
                    split_body_list[i] = translator.translate(element,dest='en').text
                split_body_list[i] = self._delete_redundant_space(split_body_list[i])

                if i + 1 == len(split_body_list) or len(split_body_list) == 1:
                    translated_body += split_body_list[i]
                else:
                    translated_body += (split_body_list[i] + prefix)
            else:
                if i + 1 == len(split_body_list) or len(split_body_list) == 1:
                    translated_body += split_body_list[i]
                else:
                    translated_body += (split_body_list[i] + suffix)

        return translated_body
        # [END _get_translated_body]

    def _get_translated_title(self):
        """Get translated article's title."""
        title = self._title
        translator = Translator()
        translated_title = translator.translate(title,dest='en').text
        return translated_title

    def upload_translation(self, gist, tweet, private, token):
        # [START upload_translation]
        """Upload translated article to Qiita."""
        body = self._get_translated_body()
        title = self._get_translated_title()
        tags = self._tags
        url = 'https://qiita.com/api/v2/items'

        params = {
            'body'     : body,
            'coediting' : False,
            'gist' : gist,
            'group_url_name' : None,
            'private' : private,
            'tags' : tags,
            'title' : title,
            'tweet' : tweet
        }

        proxies = {
            "http": os.getenv('HTTP_PROXY'),
            "https": os.getenv('HTTPS_PROXY'),
        }

        headers = {
            'content-type'  : 'application/json',
            'charset'       : 'utf-8',
            'Authorization' : 'Bearer {0}'.format(token)
        }

        response = post(url, params, proxies, headers)
        verify_response(response)
        uploaded_item = response.json()
        return uploaded_item
        # [END upload_translation]

    def update_translation(self, translation_articleid, private, token):
        # [START update_translation]
        """Update translated article on Qiita."""
        body = self._get_translated_body()
        title = self._get_translated_title()
        tags = self._tags
        url = 'https://qiita.com/api/v2/items/' + translation_articleid

        params = {
            'body'     : body,
            'coediting' : False,
            'group_url_name' : None,
            'private' : private,
            'tags' : tags,
            'title' : title,
        }

        proxies = {
            "http": os.getenv('HTTP_PROXY'),
            "https": os.getenv('HTTPS_PROXY'),
        }

        headers = {
            'content-type'  : 'application/json',
            'charset'       : 'utf-8',
            'Authorization' : 'Bearer {0}'.format(token)
        }

        response = patch(url, params, proxies, headers)
        verify_response(response)
        updated_item = response.json()
        return updated_item
        # [END update_translation]
# [END QiitaArticle]


def get_args():
    """Get arguments."""
    parser = argparse.ArgumentParser(description="""
    This application translates your articles on Qiita into English ones with googletrans, and 
    upload them to Qiita automatically. 

    Requirements:
        googletrans, Qiita access token(Set as Environment variable QIITA_ACCESS_TOKEN)
    """)
    parser.add_argument('--gist', action = 'store_true', help = 'upload translated article to gist') 
    parser.add_argument('--tweet', action = 'store_true', help = 'tweet about translated article') 
    parser.add_argument('--private', action = 'store_true', help = 'set publish format to private') 
    parser.add_argument('--auto', action = 'store_true', help = 'execute translation and upload automatically') 
    parser.add_argument('--token', default = os.getenv('QIITA_ACCESS_TOKEN'), help = 'set Qiita\'s access token') 
    args = parser.parse_args()
    return args

def get(url, params, proxies, headers):
    """Send a request with the GET method."""
    response = requests.get(url, params=params, proxies=proxies, headers=headers)
    return response

def post(url, params, proxies, headers):
    """Send a request with the POST method."""
    response = requests.post(url, data=json.dumps(params),proxies=proxies, headers=headers)
    return response

def patch(url, params, proxies, headers):
    """Send a request with the PATCH method."""
    response = requests.patch(url, data=json.dumps(params),proxies=proxies, headers=headers)
    return response

def verify_response(response):
    status_code = response.status_code
    if status_code not in range(200,202):
        print("Error: Qiita APIへのリクエストに失敗しました。")
        sys.exit(1)

def divide_items_by_lang(items):
    """divide items of article on Qiita by language."""
    original_items = []
    translated_items = []
    for item in items:
        article = QiitaArticle(item)
        if article.detect_lang() == 'en':
            translated_items.append(item)
        else:
            original_items.append(item)
    return original_items,translated_items

def find_new_items(items):
    """find new or updated items of article on Qiita."""
    original_items,translated_items = divide_items_by_lang(items)
    new_items = {}
    for i,original_item in enumerate(original_items):
        origin = QiitaArticle(original_item)
        for translated_item in translated_items:
            translation = QiitaArticle(translated_item)
            if translation.has_banner(origin.get_articleid()):
                if translation.get_updated_at() < origin.get_updated_at():
                    new_items[translation.get_articleid()] = original_item
                    break
                else:
                    break
        else:
            new_items[i] = original_item
    return new_items

def get_items(token):
    """Get items of article on Qiita."""
    url = 'https://qiita.com/api/v2/authenticated_user/items'

    params = {
        'page'     : 1,
        'per_page' : 100,
    }

    proxies = {
        "http": os.getenv('HTTP_PROXY'),
        "https": os.getenv('HTTPS_PROXY'),
    }

    headers = {
        'content-type'  : 'application/json',
        'charset'       : 'utf-8',
        'Authorization' : 'Bearer {0}'.format(token)
    }

    response = get(url, params, proxies, headers)
    verify_response(response)
    items = response.json()
    return items

def program(args):
    # [START program]
    """Execute the process of translation and upload."""
    items = get_items(args.token)
    new_items = find_new_items(items)
    page_start = 0
    articles_per_page = 10

    program_banner = textwrap.dedent(r"""
    -----------------------------------------------
     _                        ____  _ _ _        
    | |                      / __ \(_|_) |       
    | |_ _ __ __ _ _ __  ___| |  | |_ _| |_ __ _ 
    | __| '__/ _` | '_ \/ __| |  | | | | __/ _` |
    | |_| | | (_| | | | \__ \ |__| | | | || (_| |
     \__|_|  \__,_|_| |_|___/\___\_\_|_|\__\__,_|
                                                
    -----------------------------------------------
    """)
    
    description = textwrap.dedent(r"""
    翻訳対象となる新着または更新された記事を以下に表示します。
    翻訳する記事の番号を入力してください。すべての記事を翻訳する場合は
    [a]を入力してください。
    （[n]：次へ、[b]：戻る）
    """)

    confirmation_to_upload = textwrap.dedent(r"""
    選択した次の記事を翻訳して、Qiitaへアップロードしますか？
    実行する場合は[y]、実行しない場合は[n]を入力してください。
    """)

    confirmation_to_uploadall = textwrap.dedent(r"""
    翻訳対象となるすべての記事を翻訳して、Qiitaへアップロードしますか？
    実行する場合は[y]、実行しない場合は[n]を入力してください。
    """)

    if not args.auto:
        while True:
            print(program_banner)

            if len(new_items) == 0:
                print('翻訳対象となる 新着/更新 記事がQiitaに存在しません。')
                break

            print(description)
            
            print('[記事番号]\t(新着/更新)\t記事タイトル')
            
            for i,key in enumerate(new_items):
                article = QiitaArticle(new_items[key])
                if i in range(page_start,page_start + articles_per_page):
                    if type(key) == int:
                        print('[{0:03d}]\t\t(NEW)\t\t{1}'.format(i, article.get_title()))
                    else:
                        print('[{0:03d}]\t\t(UPDATED)\t{1}'.format(i, article.get_title()))
                last_article_number = i

            
            key_input = input('\n[記事番号/a/n/b]：')

            if key_input.isdigit() and int(key_input) in range(0,len(new_items)):
                
                print(confirmation_to_upload)

                for i,key in enumerate(new_items):
                    if i == int(key_input):
                        article = QiitaArticle(new_items[key])
                        if type(key) == int:
                            article.set_update_status('NEW')
                            print('[{0:03d}]\t\t(NEW)\t\t{1}'.format(int(key_input), article.get_title()))
                        else:
                            article.set_update_status('UPDATE')
                            print('[{0:03d}]\t\t(UPDATED)\t{1}'.format(int(key_input), article.get_title()))
                        break
            elif key_input == 'a':
                print(confirmation_to_uploadall)
            elif key_input == 'n':
                if last_article_number >= page_start + articles_per_page:
                    page_start = page_start + articles_per_page
                else:
                    pass
                continue
            elif key_input == 'b':
                if page_start - articles_per_page >= 0:
                    page_start = page_start - articles_per_page
                else:
                    pass
                continue
            else:
                print('\n無効な記事番号が選択されました。入力をやり直してください。')
                continue

            answer = input('\n[y/n?]：')

            if key_input != 'a' and answer == 'y':
                print('\n翻訳/アップロードを開始します.....')
                if article.get_update_status() == 'NEW':
                    article.upload_translation(args.gist, args.tweet, args.private, args.token)
                else:
                    article.update_translation(key, args.private, args.token)
                print('\n(UPLOADED)\t\t{0}'.format(article._get_translated_title()))
                print('\n翻訳/アップロードが完了しました')
                break
            elif key_input == 'a' and answer == 'y':
                print('\n翻訳/アップロードを開始します.....')
                for i,key in enumerate(new_items):
                    article = QiitaArticle(new_items[key])
                    if type(key) == int:
                        article.upload_translation(args.gist, args.tweet, args.private, args.token)
                    else:
                        article.update_translation(key, args.private, args.token)
                    print('\n[{0}/{1}]\t(UPLOADED)\t\t{2}'.format(i + 1, len(new_items), article._get_translated_title()))
                print('\n翻訳/アップロードが完了しました')
                break
            elif answer == 'n':
                break
            else:
                print('\n無効な選択がされました。入力をやり直してください。')
                continue
    else:
        for i,key in enumerate(new_items):
            article = QiitaArticle(new_items[key])
            if type(key) == int:
                article.upload_translation(args.gist, args.tweet, args.private, args.token)
            else:
                article.update_translation(key, args.private, args.token)
    return 0
    # [END program]

def main():
    """Execute the main process of this application."""
    args = get_args()

    if args.token is None:
        print("\nError: アクセストークンが設定されていません。アクセストークンを設定して、再度実行してください。")
        sys.exit(1)
    else:
        regex = r"^[0-9a-f]{40}$"
        if not re.match(regex, args.token):
            print("\nError: アクセストークンが正しくありません。正しいアクセストークンを設定して、再度実行してください。")
            sys.exit(1)
    
    try:
        exit_status = program(args)
        print('\ntransQiita finished.')
        return sys.exit(exit_status)

    except Exception as e:
        error_type = type(e).__name__ 
        sys.stderr.write("{0}: {1}\n".format(error_type, str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
    