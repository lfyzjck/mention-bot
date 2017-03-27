#!/usr/bin/env python
# coding: utf-8
import re
import json
import logging
from collections import defaultdict
from fnmatch import fnmatch

from .utils import fetch_blame, get_merge_request_diff
from .utils import add_comment_merge_request
from .utils import has_mention_comment
from .utils import get_project_file
from .utils import ConfigSyntaxError


logger = logging.getLogger(__name__)


RE_DIFF_LINE_NO = re.compile(r'\@\@ -(\d+),?(\d+)? \+(\d+),?(\d+)? \@\@')
RE_BLAME_OR_NO = re.compile(r'(<a href="\/([\w\-0-9]+)"><img class="avatar|<a class="diff-line-num")')


class BotConfig(object):
    default_config = {
        'userBlacklist': [],
        'fileBlacklist': [],
        'maxReviewers': 3,
        'findPotentialReviewers': True,
        'numFilesToCheck': 5,
        'createComment': True,
        'actions': ['open'],
        'skipWIP': True,
        'skipAlreadyAssignedMR': False,
        'skipAlreadyMentionedMR': True,
    }

    @classmethod
    def from_dict(cls, d):
        config = cls()
        attrs = dict(cls.default_config, **d)
        for k, v in attrs.iteritems():
            setattr(config, k, v)
        return config


def parse_diff_file(lines):
    deleted_lines = []
    current_from_line = 0
    lines = list(lines)
    while len(lines) > 0:
        line = lines.pop()
        if line.startswith('---') or line.startswith('+++'):
            continue
        if line.startswith('@@'):
            matched = RE_DIFF_LINE_NO.match(line)
            if matched is None:
                continue
            from_line = matched.group(1)
            # from_count = matched.group(2)
            # to_line = matched.group(3)
            # to_count = matched.group(4)
            current_from_line = int(from_line)
            continue
        if line.startswith('-'):
            deleted_lines.append(current_from_line)
        if not line.startswith('+'):
            current_from_line += 1
    return deleted_lines


def parse_diff(changes):
    files = []
    for diff in changes:
        from_file = diff['old_path']
        lines = diff['diff'].split('\n')
        deleted_lines = parse_diff_file(reversed(lines))
        files.append((from_file, deleted_lines))
    return files


def parse_blame(blame):
    lines = []
    current_author = 'none'
    result = RE_BLAME_OR_NO.finditer(blame)
    for matches in result:
        if matches.group(2):
            current_author = matches.group(2)
        else:
            lines.append(current_author)
    return lines


def get_deleted_owners(files, blames):
    owners = defaultdict(int)
    for file_path, deleted_lines in files:
        blame = blames.get(file_path)
        if not blame:
            continue
        for line in deleted_lines:
            author_name = blame[line - 1]
            if not author_name:
                continue
            owners[author_name] += 1
    return owners


def get_all_owners(files, blames):
    owners = defaultdict(int)
    for file_path, deleted_lines in files:
        blame = blames.get(file_path, None)
        if blame is None:
            continue
        for author_name in blame:
            owners[author_name] += 1
    return owners


def sort_owners(owners):
    owner_names = owners.keys()
    return sorted(owner_names,
                  key=lambda k: owners[k],
                  reverse=True)


def guess_owners(files, blames, creator, config):
    deleted_owners = get_deleted_owners(files, blames)
    all_owners = get_all_owners(files, blames)

    deleted_owners = sort_owners(deleted_owners)
    all_owners = sort_owners(all_owners)

    deleted_owners_set = set(deleted_owners)
    other_owners = [owner for owner in all_owners
                    if owner not in deleted_owners_set]

    owners = deleted_owners + other_owners

    def filter_owners(owner):
        return all([
            owner != creator,
            owner != 'none',
            owner not in config.userBlacklist
        ])

    return [u for u in owners if filter_owners(u)][:config.maxReviewers]


def filter_files(files, fileBlacklist, numFilesToCheck):
    def filter_file_black_list(files):
        new_files = []
        for filename, lines in files:
            flag = False
            for pattern in fileBlacklist:
                if fnmatch(filename, pattern):
                    flag = True
            if not flag:
                new_files.append((filename, lines))
        return new_files

    files = sorted(files, key=lambda f: len(f[1]), reverse=True)
    if len(fileBlacklist) > 0:
        files = filter_file_black_list(files)
    return files[:numFilesToCheck]


def get_files_blames(repo_namespace, target_branch, files):
    blames = {}
    for from_file, linenos in files:
        blame = fetch_blame(repo_namespace, target_branch, from_file)
        blames[from_file] = parse_blame(blame)
    return blames


def guess_owners_for_merge_reqeust(project_id,
                                   namespace,
                                   target_branch,
                                   merge_request_id,
                                   creator,
                                   config):
    if not config.findPotentialReviewers:
        return []
    changes = get_merge_request_diff(project_id, merge_request_id)
    files = parse_diff(changes)
    files = filter_files(files, config.fileBlacklist, config.numFilesToCheck)
    blames = get_files_blames(namespace, target_branch, files)
    return guess_owners(files, blames, creator, config)


def add_comment(project_id, merge_request_id, creator, reviewers, config):
    if not config.createComment:
        return
    msg = """{0}, thanks for your MR!
    By analyzing the history of the files in this pull request,
    we identified {1} to be potential reviewers."""
    reviewers_mentions = map(lambda r: '@' + str(r), reviewers)
    note = msg.format(creator, ' and '.join(reviewers_mentions))
    if config.skipAlreadyMentionedMR and\
       has_mention_comment(project_id, merge_request_id, note):
        return False
    return add_comment_merge_request(project_id, merge_request_id, note)


def get_repo_config(project_id, target_branch, config_path):
    filecontent = get_project_file(project_id, target_branch, config_path)
    if not filecontent:
        logger.warning("Unable to find config file, use default config instead.")
        return BotConfig.from_dict({})
    try:
        config = json.loads(filecontent)
        return BotConfig.from_dict(config)
    except Exception:
        logger.exception("Failed to parse config: %s" % filecontent)
        raise ConfigSyntaxError(
            "Unable to parse mention-bot custom configuration file due to a syntax error.")


def is_valid(config, data):
    if data['object_attributes']['action'] not in config.actions:
        return False

    if config.skipWIP and data['object_attributes']['work_in_progress']:
        return False

    if config.skipAlreadyAssignedMR and 'assignee' not in data['object_attributes']:
        return False
    return True
