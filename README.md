Mention Bot for Gitlab
=====

See: https://github.com/facebook/mention-bot

Find potential reviewer for Merge Reqeust.

### How to use

Install buildout:

```
pip install zc.buildout

buildout bootstrap
bin/buildout
```

Set your gitlab environment variables

```
export GITLAB_URL=<gitlab_addr>
export GITLAB_USER=<gitlab_username>
export GITLAB_PASSWORD=<gitlab_password>
export GITLAB_TOKEN=<gitlab_token>
```

Run Server:

```
# debug mode
bin/mention_bot

# with gunicorn
bin/gunicorn mention.app:app -w 1 -b :8080 --log-file -

```

### Configuration

The bot can be configured by adding a .mention-bot file to the base directory of the repo. Here's a list of the possible options:

```
{
    "findPotentialReviewers": true,
    "fileBlacklist": [],
    "actions": [
        "open" // open, close, update
    ],
    "createComment": true,
    "numFilesToCheck": 5,
    "skipAlreadyAssignedMR": false,
    "skipWIP": true,
    "maxReviewers": 3,
    "userBlacklist": []
}
```

> Note: The .mention-bot file must be valid JSON.

### How Does It Work?

Every time there's a new Merge Request, Gitlab wakes up the mention bot using Webhooks. 

Once awakened, the bot will download the diff of the merge request and figure out which files and lines have been touched.

For these, it will download the associated blame to figure out who last touched that line, as they may be a good reviewer.

After running the algorithm described in the next section, it will comment on the pull request notifying those people and go back to sleep.
