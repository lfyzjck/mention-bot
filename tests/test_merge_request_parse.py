#!/usr/bin/env python
# coding: utf-8
import unittest
import mock
import json

from mention.utils import setup_cookie, fetch_blame
from mention.mention_bot import parse_diff_file
from mention.mention_bot import parse_blame, get_deleted_owners, get_all_owners
from mention.mention_bot import sort_owners, filter_files
from mention.mention_bot import guess_owners, BotConfig
from mention.mention_bot import get_repo_config
from mention.mention_bot import is_valid
from mention.mention_bot import add_comment


class TestMergeRequestParse(unittest.TestCase):

    @mock.patch('mention.mention_bot.has_mention_comment')
    def test_add_comment(self, has_mention_comment):
        has_mention_comment.return_value = True
        project_id = 1
        merge_request_id = 1
        config = BotConfig.from_dict({
            'skipAlreadyMentionedMR': True
        })
        self.assertFalse(
            add_comment(project_id, merge_request_id, 'ck', [], config)
        )

    def test_parse_diff_file(self):
        with open('tests/data/test.diff') as f:
            lines = f.read().split('\n')
            lines = list(reversed(lines))
            deleted_lines = parse_diff_file(lines)
            assert len(deleted_lines) > 0

    def test_parse_blame(self):
        with open('tests/data/test.blame') as f:
            blame = f.read()
            lines = parse_blame(blame)
            assert isinstance(lines, list)
            assert len(lines) > 0
            self.assertIn('DouweM', lines)
            self.assertIn('tnir', lines)

    def test_get_owners(self):
        files = [
            ('test.py', [1, 2, 3]),
        ]
        blames = {
            'test.py': ['ck', 'iven', 'ck', 'fsp']
        }
        owners = get_deleted_owners(files, blames)
        assert owners == {
            'ck': 2,
            'iven': 1
        }
        all_owners = get_all_owners(files, blames)
        assert all_owners == {
            'ck': 2,
            'iven': 1,
            'fsp': 1,
        }

    def test_sort_owners(self):
        owners = {
            'ck': 1,
            'fsp': 2,
            'iven': 3
        }
        self.assertEqual(sort_owners(owners), ['iven', 'fsp', 'ck'])

    @mock.patch('mention.mention_bot.get_deleted_owners')
    @mock.patch('mention.mention_bot.get_all_owners')
    def test_guess_owners(self, get_all_owners, get_deleted_owners):
        get_all_owners.return_value = {
            'ck': 5,
            'iven': 4,
            'xiaofeng': 8,
            'wen': 2,
            'amy': 4,
        }
        get_deleted_owners.return_value = {
            'xiaofeng': 1,
            'wen': 2,
            'none': 80,
        }
        creator = 'ck'
        config = BotConfig.from_dict({
            'userBlacklist': ['amy']
        })
        owners = guess_owners([], [], creator, config)
        self.assertEqual(owners, ['wen', 'xiaofeng', 'iven'])

    def test_filter_files(self):
        files = [
            ('a.py', [1, 2]),
            ('b.py', [1, 2, 3, 5, 6]),
            ('c.json', [1, 2, 3]),
            ('readme.md', [2]),
            ('xx.py', [234, 456, 789]),
        ]
        fileBlackList = ['*.md', '*.json']
        files = filter_files(files, fileBlackList, 2)
        self.assertEqual(files, [
            ('b.py', [1, 2, 3, 5, 6]),
            ('xx.py', [234, 456, 789])
        ])

    def test_config(self):
        config = BotConfig.from_dict({
            'maxReviewers': 10,
        })
        self.assertEqual(config.maxReviewers, 10)
        self.assertEqual(config.createComment, True)
        self.assertEqual(config.actions, ['open'])

    @unittest.skip
    def test_gitlab_login(self):
        setup_cookie()
        blame = fetch_blame('ep/nami', 'master', 'nami/const.py')
        authors = parse_blame(blame)
        self.fail(authors)

    @mock.patch('mention.mention_bot.get_project_file')
    def test_get_repo_config_default(self, get_project_file):
        get_project_file.return_value = False
        config = get_repo_config(90, 'master', '.mention_bot')
        self.assertEqual(config.maxReviewers, 3)
        get_project_file.return_value = '{"maxReviewers": 5}'
        config = get_repo_config(90, 'master', '.mention_bot')
        self.assertEqual(config.maxReviewers, 5)

    def test_is_valid(self):
        config = BotConfig.from_dict({
            'actions': ['open', 'merge']
        })
        with open('tests/data/merge_request_event.json') as f:
            data = json.loads(f.read())
        data['object_attributes']['action'] = 'open'
        self.assertTrue(is_valid(config, data))
        data['object_attributes']['action'] = 'merge'
        self.assertTrue(is_valid(config, data))
        data['object_attributes']['action'] = 'update'
        self.assertFalse(is_valid(config, data))
