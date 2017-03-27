#!/usr/bin/env python
# coding: utf-8
from __future__ import absolute_import

import mock
import flask.ext.testing

from mention.app import app
from mention.mention_bot import BotConfig


class TestBot(flask.ext.testing.TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        return app

    @mock.patch('mention.app.get_repo_config')
    @mock.patch('mention.app.is_valid')
    @mock.patch('mention.app.add_comment')
    @mock.patch('mention.app.guess_owners_for_merge_reqeust')
    def test_webhook_invalid(self,
                             guess_owners_for_merge_reqeust,
                             add_comment,
                             is_valid,
                             get_repo_config):
        guess_owners_for_merge_reqeust.return_value = ['lfyzjck']
        is_valid.return_value = False
        headers = {
            'X-Gitlab-Event': 'Merge Request Hook'
        }
        with open('tests/data/merge_request_event.json') as f:
            data = f.read()
            response = self.client.post('/', data=data, headers=headers)
            self.assertEqual(response.status_code, 200)

    @mock.patch('mention.app.get_repo_config')
    @mock.patch('mention.app.is_valid')
    @mock.patch('mention.app.add_comment')
    @mock.patch('mention.app.guess_owners_for_merge_reqeust')
    def test_webhook_valid(self,
                           guess_owners_for_merge_reqeust,
                           add_comment,
                           is_valid,
                           get_repo_config):
        guess_owners_for_merge_reqeust.return_value = ['lfyzjck']
        get_repo_config.return_value = BotConfig.from_dict({})
        is_valid.return_value = True
        headers = {
            'X-Gitlab-Event': 'Merge Request Hook'
        }
        with open('tests/data/merge_request_event.json') as f:
            data = f.read()
            response = self.client.post('/', data=data, headers=headers)
            self.assertEqual(response.status_code, 200)
        add_comment.assert_called()
