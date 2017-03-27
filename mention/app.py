#!/usr/bin/env python
# coding: utf-8
import json
import logging

from flask import Flask, request

from mention.config import check_config
from mention.config import CONFIG_PATH
from mention.utils import ConfigSyntaxError
from mention.utils import has_mention_comment
from mention.mention_bot import guess_owners_for_merge_reqeust
from mention.mention_bot import add_comment, get_repo_config
from mention.mention_bot import add_comment_merge_request
from mention.mention_bot import is_valid

app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.route('/check_health', methods=['GET'])
def check_health():
    return "mention-bot"


@app.route('/', methods=['GET'])
def mentionbot():
    return "Gitlab Mention Bot avtive"


@app.route('/', methods=['POST'])
def webhook():
    event = request.headers.get('X-Gitlab-Event')
    if not event:
        return '', 400
    if event != 'Merge Request Hook':
        return '', 200
    payload = json.loads(request.data)
    logger.info('received webhook: %s' % request.data)
    username = payload['user']['username']
    project_id = payload['object_attributes']['target_project_id']
    target_branch = payload['object_attributes']['target_branch']
    namespace = payload['object_attributes']['target']['path_with_namespace']
    merge_request_id = payload['object_attributes']['id']
    # loading config
    try:
        config = get_repo_config(project_id, target_branch, CONFIG_PATH)
        if not is_valid(config, payload):
            # skip
            return "", 200
        owners = guess_owners_for_merge_reqeust(project_id,
                                                namespace,
                                                target_branch,
                                                merge_request_id,
                                                username,
                                                config)
        add_comment(
            project_id,
            merge_request_id,
            username,
            owners,
            config
        )
    except ConfigSyntaxError as e:
        add_comment_merge_request(project_id, merge_request_id, e.message)
    return "", 200


def main():
    check_config()
    app.run()


if __name__ == '__main__':
    main()
