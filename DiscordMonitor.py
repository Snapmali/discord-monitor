#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import datetime
import discord
import json
import os
import platform
import re
import requests
import signal
import sys
import threading
import time
import traceback

from aiohttp import ClientConnectorError, ClientProxyConnectionError
from plyer import notification
from pytz import timezone as tz

# Log file path
log_path = 'discord_monitor.log'
# Timezone
timezone = tz('Asia/Shanghai')

lock = threading.Lock()

while True:
    config_file = 'config.json'
    try:
        config_file_temp = input('请输入配置文件路径，空输入则为默认(默认为config.json):\n')
        if config_file_temp != '':
            config_file = config_file_temp
        with open(config_file, 'r', encoding='utf8') as f:
            config = json.load(f)
            token = config['token']
            bot = config['is_bot']
            coolq_url = config['coolq_url'].rstrip('/')
            coolq_token = config['coolq_token']
            proxy = config['proxy']
            interval = config['interval']
            toast = config['toast']
            user_id = config['monitor']['user_id']
            channels = config['monitor']['channel']
            channel_name_list = config['monitor']['channel_name']
            servers = set(config['monitor']['server'])
            qq_group = config['push']['QQ_group']
            qq_user = config['push']['QQ_user']
            channel_name = dict()
            for guild_ in channel_name_list:
                for i in range(1, len(guild_)):
                    try:
                        channel_name[guild_[0]].add(guild_[i])
                    except KeyError:
                        channel_name[guild_[0]] = set()
                        channel_name[guild_[0]].add(guild_[i])
            break
    except FileNotFoundError:
        print('配置文件不存在')
    except Exception:
        print('配置文件读取出错，请检查配置文件各参数是否正确')
        if platform.system() == 'Windows':
            os.system('pause')
        sys.exit(1)


class DiscordMonitor(discord.Client):

    def __init__(self, monitoring_user, monitoring_channel, monitoring_channel_name, monitoring_server, do_toast,
                 query_interval=60, **kwargs):
        discord.Client.__init__(self, **kwargs)
        self.monitoring_user = monitoring_user
        self.monitoring_channel = monitoring_channel
        self.monitoring_server = monitoring_server
        self.monitoring_channel_name = monitoring_channel_name
        self.event_set = set()
        self.status_dict = {'online': '在线', 'offline': '离线', 'idle': '闲置', 'dnd': '请勿打扰'}
        self.username_dict = {}
        self.nick_dict = {}
        self.interval = query_interval
        self.connect_times = 0
        if platform.system() == 'Windows' and platform.release() == '10' and do_toast:
            self.do_toast = True
        else:
            self.do_toast = False
        self.message_monitoring = True
        self.user_monitoring = True
        if 0 in self.monitoring_channel and len(self.monitoring_channel_name) == 0:
            self.message_monitoring = False
        if 0 in self.monitoring_server or len(self.monitoring_user) == 0:
            self.user_monitoring = False

    def is_monitored_object(self, user, channel, server, member_update=False):
        """
        判断事件是否由被检测对象发出

        :param channel: 动态来源Channel
        :param member_update:是否为用户动态
        :param user:动态来源用户
        :param server:动态来源Server
        :return:
        """
        # 被检测用户列表为空
        if len(self.monitoring_user) == 0:
            # 用户动态
            if member_update:
                return False
            # 消息动态
            if len(self.monitoring_channel) == 0 or channel.id in self.monitoring_channel or \
                    (server.name in self.monitoring_channel_name and channel.name in self.monitoring_channel_name[server.name]):
                return True
        # 用户动态
        elif member_update and str(user.id) in self.monitoring_user and (server.id in self.monitoring_server or len(self.monitoring_server) == 0):
            return True
        # 消息动态
        elif str(user.id) in self.monitoring_user and \
                (len(self.monitoring_channel) == 0 or channel.id in self.monitoring_channel or
                 (server.name in self.monitoring_channel_name and channel.name in self.monitoring_channel_name[server.name])):
            return True
        return False

    async def process_message(self, message, status):
        """
        处理消息动态，并生成推送消息文本及log

        :param message: Message
        :param status: 消息动态
        :return:
        """
        attachment_urls = [attachment.url for attachment in message.attachments]
        attachment_str = '; '.join(attachment_urls)
        if self.do_toast:
            if status == '标注消息':
                toast_title = '%s #%s %s' % (message.guild.name, message.channel.name, status)
            elif len(self.monitoring_user) != 0:
                toast_title = '%s %s' % (self.monitoring_user[str(message.author.id)], status)
            else:
                toast_title = '%s %s' % (message.author.name, status)
            toast_text = message.content + attachment_str
            notification.notify(toast_title, toast_text, app_icon='icon.ico', app_name='Discord Monitor')
        if len(attachment_str) > 0:
            attachment_log = '. Attachment: ' + attachment_str
        else:
            attachment_log = ''
        if status == '发送消息':
            t = message.created_at.replace(tzinfo=datetime.timezone.utc).astimezone(timezone).strftime(
                '%Y/%m/%d %H:%M:%S')
        else:
            t = datetime.datetime.now(tz=timezone).strftime('%Y/%m/%d %H:%M:%S')
        log_text = '%s: ID: %d. Username: %s. Server: %s. Channel: %s. Content: %s%s' % \
                   (status, message.author.id,
                    message.author.name + '#' + message.author.discriminator,
                    message.guild.name, message.channel.name, message.content, attachment_log)
        add_log(0, 'Discord', log_text)
        if len(attachment_str) > 0:
            attachment_push = '\n附件：' + attachment_str
        else:
            attachment_push = ''
        if status == '标注消息':
            push_text = '【Discord %s】\n正文：%s%s\n频道：%s #%s\n作者：%s\n时间：%s %s' % \
                        (status,
                         message.content,
                         attachment_push,
                         message.guild.name,
                         message.channel.name,
                         message.author.name + '#' + message.author.discriminator,
                         t,
                         timezone.zone)
        elif len(self.monitoring_user) != 0:
            push_text = '【Discord %s %s】\n正文：%s%s\n频道：%s #%s\n时间：%s %s' % \
                        (self.monitoring_user[str(message.author.id)],
                         status,
                         message.content,
                         attachment_push,
                         message.guild.name,
                         message.channel.name,
                         t,
                         timezone.zone)
        else:
            push_text = '【Discord %s %s】\n正文：%s%s\n频道：%s #%s\n时间：%s %s' % \
                        (message.author.name,
                         status,
                         message.content,
                         attachment_push,
                         message.guild.name,
                         message.channel.name,
                         t,
                         timezone.zone)
        push_message(push_text, 1)

    async def process_user_update(self, before, after, user, status):
        """
        处理用户动态，并生成推送消息文本及log

        未指定被检测用户时应无法进入此方法

        :param before:
        :param after:
        :param user: Member或User
        :param status: 事件类型
        :return:
        """
        if self.do_toast:
            toast_title = '%s %s' % (self.monitoring_user[str(user.id)], status)
            toast_text = '变更后：%s' % after
            notification.notify(toast_title, toast_text, app_icon='icon.ico', app_name='Discord Monitor')
        t = datetime.datetime.now(tz=timezone).strftime('%Y/%m/%d %H:%M:%S')
        log_text = '%s: ID: %d. Username: %s. Server: %s. Before: %s. After: %s.' % \
                   (status, user.id,
                    user.name + '#' + user.discriminator,
                    user.guild.name, before, after)
        add_log(0, 'Discord', log_text)
        push_text = '【Discord %s %s】\n变更前：%s\n变更后：%s\n频道：%s\n时间：%s %s' % \
                    (self.monitoring_user[str(user.id)],
                     status,
                     before,
                     after,
                     user.guild.name,
                     t,
                     timezone.zone)
        push_message(push_text, 2)

    async def on_connect(self):
        """
        监听连接事件，每次连接会刷新所监视用户的用户名列表，使用非bot用户监视时会另外刷新昵称列表。若使用频道名监听消息则获取频道名对应ID。并启动轮询监视。重写自discord.Client

        ***眼来了***

        :return:
        """
        log_text = 'Logged in as %s, ID: %d.' % (self.user.name + '#' + self.user.discriminator, self.user.id)
        print(log_text + '\n')
        add_log(0, 'Discord', log_text)
        if self.user_monitoring:
            is_bot = self.user.bot
            for uid in self.monitoring_user:
                uid = int(uid)
                user = None
                for guild in self.guilds:
                    try:
                        user = await guild.fetch_member(uid)
                        if not is_bot:
                            try:
                                self.nick_dict[uid][guild.id] = user.nick
                            except:
                                self.nick_dict[uid] = {guild.id: user.nick}
                    except:
                        continue
                if user:
                    self.username_dict[uid] = [user.name, user.discriminator]
                else:
                    log_text = 'Fetch ID %s\'s username failed.' % uid
                    add_log(2, 'Discord', log_text)
        self.connect_times += 1
        if not self.user.bot and self.user_monitoring:
            await self.polling(self.connect_times)

    async def polling(self, times):
        """
        轮询监视

        :param times: 连接次数，发生变动终止本次轮询，防止重复监视
        :return:
        """
        while times == self.connect_times:
            await asyncio.sleep(self.interval)
            if not self.user.bot and self.user_monitoring:
                await self.watch_nick()

    async def watch_nick(self):
        """
        非bot用户轮询监视用户名变动及昵称变动

        :return:
        """
        for uid in self.monitoring_user:
            uid = int(uid)
            user = None
            for guild in self.guilds:
                try:
                    user = await guild.fetch_member(uid)
                    try:
                        self.nick_dict[uid][guild.id]
                    except KeyError:
                        try:
                            self.nick_dict[uid][guild.id] = user.nick
                        except KeyError:
                            self.nick_dict[uid] = {guild.id: user.nick}
                        continue
                    if self.nick_dict[uid][guild.id] != user.nick:
                        await self.process_user_update(self.nick_dict[uid][guild.id], user.nick, user, '昵称更新')
                        self.nick_dict[uid][guild.id] = user.nick
                except:
                    continue
            if user:
                try:
                    self.username_dict[uid]
                except KeyError:
                    self.username_dict[uid] = [user.name, user.discriminator]
                    continue
                if self.username_dict[uid][0] != user.name or self.username_dict[uid][1] != user.discriminator:
                    before_screenname = self.username_dict[uid][0] + '#' + self.username_dict[uid][1]
                    after_screenname = user.name + '#' + user.discriminator
                    await self.process_user_update(before_screenname, after_screenname, user, '用户名更新')
                    self.username_dict[uid][0] = user.name
                    self.username_dict[uid][1] = user.discriminator

    async def on_disconnect(self):
        """
        监听断开连接事件，重写自discord.Client

        :return:
        """
        log_text = 'Disconnected...'
        add_log(1, 'Discord', log_text)
        print()

    async def on_message(self, message):
        """
        监听消息发送事件，重写自discord.Client

        :param message: Message
        :return:
        """
        if not self.message_monitoring:
            return
        # 消息标注事件亦会被捕获，同时其content及attachments为空，需特判排除
        if self.is_monitored_object(message.author, message.channel, message.guild) and (message.content != '' or len(message.attachments) > 0):
            await self.process_message(message, '发送消息')

    async def on_message_delete(self, message):
        """
        监听消息删除事件，重写自discord.Client

        :param message: Message
        :return:
        """
        if not self.message_monitoring:
            return
        if self.is_monitored_object(message.author, message.channel, message.guild):
            await self.process_message(message, '删除消息')

    async def on_message_edit(self, before, after):
        """
        监听消息编辑事件，重写自discord.Client

        :param before: Message
        :param after: Message
        :return:
        """
        if not self.message_monitoring:
            return
        if self.is_monitored_object(after.author, after.channel, after.guild) and before.content != after.content:
            await self.process_message(after, '编辑消息')

    async def on_guild_channel_pins_update(self, channel, last_pin):
        """
        监听频道内标注消息更新事件，重写自discord.Client

        :param channel: 频道
        :param last_pin: datetime.datetime 最新标注消息的发送时间
        :return:
        """
        if not self.message_monitoring:
            return
        if channel.id in self.monitoring_channel or len(self.monitoring_channel) == 0 or \
                (channel.guild.name in self.monitoring_channel_name and channel.name in self.monitoring_channel_name[channel.guild.name]):
            pins = await channel.pins()
            if len(pins) > 0:
                await self.process_message(pins[0], '标注消息')

    async def on_member_update(self, before, after):
        """
        监听用户状态更新事件，重写自discord.Client

        :param before: Member
        :param after: Member
        :return:
        """
        if not self.user_monitoring:
            return
        if self.is_monitored_object(before, None, before.guild, member_update=True):
            # 昵称变更
            if before.nick != after.nick:
                event = str(before.nick) + str(after.nick)
                if self.check_event(event):
                    await self.process_user_update(before.nick, after.nick, before, '昵称更新')
                    self.delete_event(event)
            # 在线状态变更
            if before.status != after.status:
                event = str(before.id) + str(before.status) + str(after.status)
                if self.check_event(event):
                    await self.process_user_update(self.get_status(before.status), self.get_status(after.status),
                                                   before, '状态更新')
                    self.delete_event(event)
            # 用户名或Tag变更
            try:
                self.username_dict[before.id]
            except KeyError:
                self.username_dict[before.id] = [after.name, after.discriminator]
            if self.username_dict[before.id][0] != after.name or self.username_dict[before.id][
                1] != after.discriminator:
                before_screenname = self.username_dict[before.id][0] + '#' + self.username_dict[before.id][1]
                after_screenname = after.name + '#' + after.discriminator
                self.username_dict[before.id][0] = after.name
                self.username_dict[before.id][1] = after.discriminator
                event = before_screenname + after_screenname
                if self.check_event(event):
                    await self.process_user_update(before_screenname, after_screenname, before, '用户名更新')
                    self.delete_event(event)
            # 用户活动变更
            if before.activity != after.activity:
                if not before.activity:
                    event = after.activity.name
                    if self.check_event(event):
                        await self.process_user_update(None, after.activity.name, before, '活动更新')
                        self.delete_event(event)
                elif not after.activity:
                    event = before.activity.name
                    if self.check_event(event):
                        await self.process_user_update(before.activity.name, None, before, '活动更新')
                        self.delete_event(event)
                elif before.activity.name != after.activity.name:
                    event = before.activity.name + after.activity.name
                    if self.check_event(event):
                        await self.process_user_update(before.activity.name, after.activity.name, before, '活动更新')
                        self.delete_event(event)

    def get_status(self, status):
        """
        将api的用户在线状态转换为中文

        :param status: api中的用户在线状态
        :return: 中文在线状态
        """
        status = str(status)
        if status in self.status_dict:
            return self.status_dict[status]
        return status

    def check_event(self, event):
        """
        检查该事件是否已在用户动态事件set中，不在则将事件加入set，防止眼和监测用户同在多个Server中时重复推送用户动态

        :param event: event
        :return: True if yes, otherwise False
        """
        lock.acquire()
        if event in self.event_set:
            lock.release()
            return False
        else:
            self.event_set.add(event)
            lock.release()
            return True

    def delete_event(self, event):
        """
        设置线程延时删除set中的用户动态事件

        :param event: event
        :return:
        """
        t = threading.Thread(args=(event,), target=self.delete_thread)
        t.setDaemon(True)
        t.start()

    def delete_thread(self, event):
        """
        作为线程5秒后删除set中的用户动态事件

        :param event: event
        :return:
        """
        time.sleep(5)
        lock.acquire()
        self.event_set.remove(event)
        lock.release()


def push_message(message, permission):
    """
    建立线程并将消息推送至cooq-http-api

    :param message: message text
    :param permission: 1表示消息动态，2表示用户动态
    :return:
    """
    for group in qq_group:
        if group[permission]:
            t = threading.Thread(args=(message, group[0], 'group'), target=push_thread)
            t.setDaemon(True)
            t.start()
    for user in qq_user:
        if user[permission]:
            t = threading.Thread(args=(message, user[0], 'user'), target=push_thread)
            t.setDaemon(True)
            t.start()


def push_thread(message, qq_id, id_type):
    """
    作为线程将消息推送至cqhttp
    :param message: message text
    :param qq_id: QQ user ID or group ID
    :param id_type: 'group'表示群聊, 'user'私聊
    :return:
    """
    # message = pattern.sub(lambda m: rep[re.escape(m.group(0))], message)
    data = {'message': message, 'auto_escape': True}
    headers = {'Content-type': 'application/json'}
    url = '%s/send_msg' % coolq_url

    if id_type == 'group':
        data['message_type'] = 'group'
        data['group_id'] = qq_id
    elif id_type == 'user':
        data['message_type'] = 'private'
        data['user_id'] = qq_id

    # 判断是否设置cqhttp access token
    if coolq_token is not "":
        headers['Authorization'] = "Bearer " + coolq_token

    # 5次重试
    for i in range(5):
        try:
            response = requests.post(url=url, headers=headers, data=json.dumps(data), timeout=(3, 10)).status_code
        except:
            if i == 4:
                # 哦 5次全超时
                log = 'Timeout! Failed to send message to %s %d. Message: %s' % \
                      (id_type, qq_id, data)
                add_log(0, 'PUSH', log)
                break
            time.sleep(5)
            continue
        if response == 200:
            # cqhttp接受消息，但不知操作实际成功与否
            log = 'Message to %s %d is sent. Response:%d. Retries:%d. Message: %s' % \
                  (id_type, qq_id, response, i, data)
            add_log(0, 'PUSH', log)
            break
        if response == 401:
            # token needed
            log = 'Failed to send message to %s %d. Reason: Access token is not provided. ' \
                  'Response:%d. Retries:%d. Message: %s' % (id_type, qq_id, response, i, data)
            add_log(0, 'PUSH', log)
            break
        if response == 403:
            # token is wrong
            log = 'Failed to send message to %s %d. Reason: Access token is wrong. ' \
                  'Response:%d. Retries:%d. Message: %s' % (id_type, qq_id, response, i, data)
            add_log(0, 'PUSH', log)
            break
        if response == 404:
            # url is wrong
            log = 'Failed to send message to %s %d. Reason: Coolq URL is wrong. ' \
                  'Response:%d. Retries:%d. Message: %s' % (id_type, qq_id, response, i, data)
            add_log(0, 'PUSH', log)
            break
        elif i == 4:
            # 未超时但失败，还没出过这问题
            log = 'Failed to send message to %s %d. Response:%d. Message: %s' % \
                  (id_type, qq_id, response, data)
            add_log(0, 'PUSH', log)


def add_log(log_type, method, text):
    """
    将log打印并存储至文件

    :param log_type: 0: INFO, 1: WARN, 2: ERROR
    :param method: 产生log的模块
    :param text: log文本
    :return:
    """
    log_type_dict = {0: 'INFO', 1: 'WARN', 2: 'ERROR'}
    try:
        log_type = log_type_dict[log_type]
    except KeyError:
        traceback.print_exc()
        return
    text = text.replace('\n', '\\n')
    t = time.strftime('%Y/%m/%d %H:%M:%S')
    log_text = '[%s][%s][%s] %s' % (log_type, t, method, text)
    print(log_text)
    with open(log_path, 'a', encoding='utf8') as log:
        log.write(log_text)
        log.write('\n')


if __name__ == '__main__':
    intents = discord.Intents.all()
    if proxy != '':
        # 云插眼
        dc = DiscordMonitor(user_id, channels, channel_name, servers, toast,
                            query_interval=interval, proxy=proxy, intents=intents)
    else:
        # 直接插眼
        dc = DiscordMonitor(user_id, channels, channel_name, servers, toast,
                            query_interval=interval, intents=intents)
    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        print('Logging in...')
        dc.run(token, bot=bot)
    except ClientProxyConnectionError:
        print('代理错误，请检查代理设置')
    except (TimeoutError, ClientConnectorError):
        print('连接超时，请检查连接状态及代理设置')
    except discord.errors.LoginFailure:
        print('登录失败，请检查Token及bot设置是否正确，或更新Token')
    except Exception:
        print('登录失败，请检查配置文件中各参数是否正确')
        traceback.print_exc()

    if platform.system() == 'Windows':
        os.system('pause')
