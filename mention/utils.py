#!/usr/bin/env python
# coding: utf-8
from __future__ import absolute_import
import re
import logging

import requests
from gitlab import Gitlab

from mention.config import GITLAB_URL, GITLAB_TOKEN
from mention.config import GITLAB_USERNAME, GITLAB_PASSWORD


logger = logging.getLogger(__name__)


session = requests.Session()
_gitlab_client = None


class GitlabError(Exception):
    pass


class ConfigSyntaxError(Exception):
    pass


def get_gitlab_client():
    global _gitlab_client
    if _gitlab_client is None:
        _gitlan_client = Gitlab(GITLAB_URL, token=GITLAB_TOKEN)
    return _gitlan_client


def get_merge_request_diff(project_id, merge_request_id):
    client = get_gitlab_client()
    changes = client.getmergerequestchanges(project_id, merge_request_id)
    return changes['changes']


def has_mention_comment(project_id, merge_request_id, comment):
    client = get_gitlab_client()
    has_next = True
    page = 1
    per_page = 20
    while has_next:
        comments = client.getmergerequestcomments(project_id, merge_request_id,
                                                  page=page,
                                                  per_page=per_page)
        for item in comments:
            if item['note'] == comment:
                return True
        if len(comments) < per_page:
            has_next = False
    return False


def get_project_file(project_id, branch, path):
    client = get_gitlab_client()
    return client.getrawfile(project_id, branch, path)


def add_comment_merge_request(project_id, merge_request_id, note):
    client = Gitlab(GITLAB_URL, token=GITLAB_TOKEN)
    return client.addcommenttomergerequest(project_id, merge_request_id, note)


def _search_authenticity_token(html):
    matched = re.search(
        r'<input type="hidden" name="authenticity_token" value="(.*)" />',
        html
    )
    if not matched:
        raise GitlabError("Fetch login page failed.")
    return matched.group(1)


def login():
    login_url = GITLAB_URL + '/users/auth/ldapmain/callback'
    login_page = GITLAB_URL + '/users/sign_in'
    headers = {
        'Origin': GITLAB_URL,
        'Referer': login_page,
    }
    response = session.get(login_url, headers=headers)
    authenticity_token = _search_authenticity_token(response.text)
    data = {
        'username': GITLAB_USERNAME,
        'password': GITLAB_PASSWORD,
        'authenticity_token': authenticity_token,
        'utf8': u'√',
    }
    return session.post(login_url, headers=headers, data=data,
                        allow_redirects=False)


def setup_cookie():
    if session.cookies is None or len(session.cookies) == 0:
        login()


def fetch_blame(namespace, target_branch, path):
    setup_cookie()
    try:
        url = '%s/%s/blame/%s/%s' % (GITLAB_URL, namespace, target_branch, path)
        response = session.get(url)
        response.raise_for_status()
    except requests.HTTPError:
        logger.warning("Fetch %s blame failed." % url)
    return response.text
