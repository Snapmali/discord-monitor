#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import discord
import json
import requests
import threading
import time

from aiohttp import ClientConnectorError, ClientProxyConnectionError
from dateutil import tz

# Config file path
config_file = 'config.json'
# Log file path
log_path = 'discord_monitor.log'
# Timezone
timezone_sh = tz.gettz('Asia/Shanghai')

with open(config_file, 'r', encoding='utf8') as f:
    config = json.load(f)
    token = config['token']
    bot = config['is_bot']
    coolq_port = config['coolq_port']
    proxy = config['proxy']

    user_id = config['monitor']['user_id']
    servers = set(config['monitor']['server'])
    qq_group = config['push']['QQ_group']
    qq_user = config['push']['QQ_user']

lock = threading.Lock()


class DiscordMonitor(discord.Client):
    def __init__(self, monitoring_id, monitoring_server, **kwargs):
        discord.Client.__init__(self, **kwargs)
        self.monitoring_id = monitoring_id
        self.monitoring_server = monitoring_server
        self.event_set = set()
        self.status_dict = {'online': '在线', 'offline': '离线', 'idle': '闲置', 'dnd': '请勿打扰'}

    def is_monitored_user(self, user, server):
        if str(user.id) in self.monitoring_id and (server in self.monitoring_server or True in self.monitoring_server):
            return True
        return False

    def process_message(self, message, status):
        t = message.created_at.replace(tzinfo=datetime.timezone.utc).astimezone(timezone_sh).__format__('%Y/%m/%d %H:%M:%S')
        log_text = '[INFO][%s][Discord][%s] ID: %d. Username: %s. Server: %s. Channel: %s. Content: %s' % \
                   (t, status, message.author.id,
                    message.author.name + '#' + message.author.discriminator,
                    message.guild.name, message.channel.name, message.content)
        add_log(log_text)
        push_text = '【Discord %s %s】\n正文：%s\n频道：%s #%s\n时间：%s UTC+8' % \
                    (self.monitoring_id[str(message.author.id)],
                     status,
                     message.content,
                     message.guild.name,
                     message.channel.name,
                     t)
        push_message(push_text, 1)

    def process_pin(self, message, status, last_pin):
        t = last_pin.replace(tzinfo=datetime.timezone.utc).astimezone(timezone_sh).__format__('%Y/%m/%d %H:%M:%S')
        log_text = '[INFO][%s][Discord][%s] ID: %d. Username: %s. Server: %s. Channel: %s. Content: %s' % \
                   (t, status, message.author.id,
                    message.author.name + '#' + message.author.discriminator,
                    message.guild.name, message.channel.name, message.content)
        add_log(log_text)
        push_text = '【Discord %s】\n正文：%s\n频道：%s #%s\n作者：%s\n时间：%s UTC+8' % \
                    (status,
                     message.content,
                     message.guild.name,
                     message.channel.name,
                     message.author.name + '#' + message.author.discriminator,
                     t)
        push_message(push_text, 1)

    def process_user_update(self, before, after, user, status):
        t = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())
        log_text = '[INFO][%s][Discord][%s] ID: %d. Username: %s. Server: %s. Before: %s. After: %s.' % \
                   (t, status, user.id,
                    user.name + '#' + user.discriminator,
                    user.guild.name, before, after)
        add_log(log_text)
        push_text = '【Discord %s %s】\n变更前：%s\n变更后：%s\n频道：%s\n时间：%s UTC+8' % \
                    (self.monitoring_id[str(user.id)],
                     status,
                     before,
                     after,
                     user.guild.name,
                     t)
        push_message(push_text, 2)

    async def on_connect(self):
        print('Logged in as %s, id: %d.' % (self.user.name + '#' + self.user.discriminator, self.user.id))

    async def on_message(self, message):
        if self.is_monitored_user(message.author, message.guild.id) and message.content != '':
            self.process_message(message, '发送消息')

    async def on_message_delete(self, message):
        if self.is_monitored_user(message.author, message.guild.id):
            self.process_message(message, '删除消息')

    async def on_message_edit(self, before, after):
        if self.is_monitored_user(after.author, after.guild.id):
            self.process_message(after, '编辑消息')

    async def on_guild_channel_pins_update(self, channel, last_pin):
        if channel.guild.id in self.monitoring_server or True in self.monitoring_server:
            pins = await channel.pins()
            self.process_pin(pins[0], '标注消息', last_pin)

    async def on_member_update(self, before, after):
        if self.is_monitored_user(before, before.guild.id):
            if before.nick != after.nick:
                event = str(before.nick) + str(after.nick)
                if self.check_event(event):
                    self.process_user_update(before.nick, after.nick, before, '昵称更新')
                    self.delete_event(event)
            if before.status != after.status:
                event = str(before.id) + str(before.status) + str(after.status)
                if self.check_event(event):
                    self.process_user_update(self.get_status(before.status), self.get_status(after.status), before, '状态更新')
                    self.delete_event(event)
            if before.name != after.name or before.discriminator != after.discriminator:
                before_screenname = before.name + '#' + before.discriminator
                after_screenname = after.name + '#' + after.discriminator
                event = before_screenname + after_screenname
                if self.check_event(event):
                    self.process_user_update(before_screenname, after_screenname, before, '用户名更新')
                    self.delete_event(event)
            if before.activity != after.activity:
                if not before.activity:
                    event = after.activity.name
                    if self.check_event(event):
                        self.process_user_update(None, after.activity.name, before, '活动更新')
                        self.delete_event(event)
                elif not after.activity:
                    event = before.activity.name
                    if self.check_event(event):
                        self.process_user_update(before.activity.name, None, before, '活动更新')
                        self.delete_event(event)
                elif before.activity.name != after.activity.name:
                    event = before.activity.name + after.activity.name
                    if self.check_event(event):
                        self.process_user_update(before.activity.name, after.activity.name, before, '活动更新')
                        self.delete_event(event)

    def get_status(self, status):
        status = str(status)
        if status in self.status_dict:
            return self.status_dict[status]
        return status

    def check_event(self, event):
        lock.acquire()
        if event in self.event_set:
            lock.release()
            return False
        else:
            self.event_set.add(event)
            lock.release()
            return True

    def delete_event(self, event):
        t = threading.Thread(args=(event,), target=self.delete_thread)
        t.start()

    def delete_thread(self, event):
        time.sleep(5)
        lock.acquire()
        self.event_set.remove(event)
        lock.release()


def push_message(message, permission):
    for group in qq_group:
        if group[permission]:
            t = threading.Thread(args=(message, group[0], 'group'), target=push_thread)
            t.start()
    for user in qq_user:
        if user[permission]:
            t = threading.Thread(args=(message, user[0], 'user'), target=push_thread)
            t.start()


def push_thread(message, qq_id, id_type):
    message = message.replace('%', '%25')
    message = message.replace('#', '%23')
    message = message.replace(' ', '%20')
    message = message.replace('/', '%2F')
    message = message.replace('+', '%2B')
    message = message.replace('?', '%3F')
    message = message.replace('&', '%26')
    message = message.replace('=', '%3D')
    if id_type == 'group':
        url = 'http://localhost:%d/send_group_msg?group_id=%d&message=%s' % \
              (coolq_port, qq_id, message)
    elif id_type == 'user':
        url = 'http://localhost:%d/send_private_msg?user_id=%d&message=%s' % \
              (coolq_port, qq_id, message)
    for i in range(5):
        try:
            response = requests.post(url, timeout=(3, 10)).status_code
        except:
            if i == 4:
                t = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())
                log = '[ERROR][%s][Push] Timeout! Failed to send message to %s %d. Message: %s' % \
                      (t, id_type, qq_id, message)
                add_log(log)
                break
            time.sleep(5)
            continue
        if response == 200:
            t = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())
            log = '[INFO][%s][Push] Message to %s %d is sent. Response:%d. Retries:%d. Message: %s' % \
                  (t, id_type, qq_id, response, i + 1, message)
            add_log(log)
            break
        elif i == 4:
            t = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())
            log = '[ERROR][%s][Push] Failed to send message to %s %d. Response:%d. Message: %s' % \
                  (t, id_type, qq_id, response, message)
            add_log(log)


def add_log(log_text):
    log_text = log_text.replace('\n', '\\n')
    print(log_text)
    with open(log_path, 'a', encoding='utf8') as f:
        f.write(log_text)
        f.write('\n')


if __name__ == '__main__':
    if proxy != '':
        dc = DiscordMonitor(user_id, servers, proxy=proxy)
    else:
        dc = DiscordMonitor(user_id, servers)
    try:
        print('Logging in...')
        dc.run(token, bot=bot)
    except ClientProxyConnectionError:
        print('代理错误，请检查代理设置')
    except (TimeoutError, ClientConnectorError):
        print('连接超时，请检查连接状态及代理设置')
    except discord.errors.LoginFailure:
        print('登录失败，请检查Token及bot设置是否正确，或更新Token')
