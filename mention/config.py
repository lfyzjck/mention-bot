#!/usr/bin/env python
# coding: utf-8
import os
import logging
import logging.config

logger = logging.getLogger(__name__)

GITLAB_URL = os.getenv('GITLAB_URL')
GITLAB_TOKEN = os.getenv('GITLAB_TOKEN')
GITLAB_USERNAME = os.getenv('GITLAB_USERNAME')
GITLAB_PASSWORD = os.getenv('GITLAB_PASSWORD')
CONFIG_PATH = '.mention-bot'


logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'basic': {
            'format': '%(levelname)s %(asctime)s %(module)s '
            '%(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'basic'
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console']
    }
})


def check_config():
    if not GITLAB_URL:
        logger.error("No Gitlab address detected, please expose GITLAB_URL as environment variables.")
        exit(1)
    if not GITLAB_USERNAME or not GITLAB_PASSWORD:
        logger.error("No Gitlab account detected, please expose GITLAB_USERNAME and GITLAB_PASSWORD as environment variables.")
        exit(1)
    if not GITLAB_TOKEN:
        logger.error("goto Profile Settings -> Access Token -> Create Personal Access Token")
        logger.error("append GITLAB_TOKEN= before start command.")
        exit(1)
