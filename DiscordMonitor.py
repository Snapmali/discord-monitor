#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import datetime
import os
import platform
import traceback

import discord
from aiohttp import ClientConnectorError, ClientProxyConnectionError, InvalidURL
from plyer import notification
from pytz import timezone as tz

from Config import config
from Log import add_log
from PushTextProcessor import PushTextProcessor
from QQPush import QQPush

# Log file path
log_path = 'discord_monitor.log'
# Timezone
timezone = tz('Asia/Shanghai')

img_MIME = ["image/png", "image/jpeg", "image/gif"]


class DiscordMonitor(discord.Client):

    def __init__(self, **kwargs):
        if config.proxy:
            discord.Client.__init__(self, proxy=config.proxy, **kwargs)
        else:
            discord.Client.__init__(self, **kwargs)
        self.message_user = config.message_monitor.users
        self.message_channel = config.message_monitor.channel_ids
        self.message_channel_name = config.message_monitor.channel_names
        self.user_dynamic_user = config.user_dynamic_monitor.users
        self.user_dynamic_server = config.user_dynamic_monitor.servers
        self.qq_push = QQPush()
        self.push_text_processor = PushTextProcessor()
        self.event_set = set()
        self.status_dict = {'online': '在线', 'offline': '离线', 'idle': '闲置', 'dnd': '请勿打扰'}
        self.username_dict = {}
        if platform.system() == 'Windows' and platform.release() == '10' and config.toast:
            self.do_toast = True
        else:
            self.do_toast = False
        self.message_monitoring = True
        self.user_monitoring = True
        if 0 in self.message_channel and len(self.message_channel_name) == 0:
            self.message_monitoring = False
        if 0 in self.user_dynamic_server or len(self.user_dynamic_user) == 0:
            self.user_monitoring = False

    def is_monitored_object(self, user, channel, server, user_dynamic=False):
        """
        判断事件是否由被检测对象发出

        :param channel: 动态来源Channel
        :param user_dynamic:是否为用户动态
        :param user:动态来源用户
        :param server:动态来源Server
        :return:
        """
        # 用户动态
        if user_dynamic:
            # 被检测用户列表为空
            if len(self.user_dynamic_user) == 0:
                return False
            # 用户id在列表中 且 server在列表中或列表为空
            elif str(user.id) in self.user_dynamic_user and \
                    (server.id in self.user_dynamic_server or len(self.user_dynamic_server) == 0):
                return True
        # 消息动态
        else:
            # 被检测用户列表为空 或 用户id在列表中
            if len(self.message_user) == 0 or str(user.id) in self.message_user:
                # 被检测频道列表为空 或 频道在列表中 或 频道名称在列表中
                if (len(self.message_channel) == 0 or channel.id in self.message_channel or
                        (server.name in self.message_channel_name and channel.name in self.message_channel_name[server.name])):
                    return True
        return False

    async def process_message(self, message: discord.Message, status):
        """
        处理消息动态，并生成推送消息文本及log

        :param message: Message
        :param status: 消息动态
        :return:
        """
        content_cat = self.push_text_processor.get_content_cat(message.content)
        if not content_cat and content_cat != "":
            return
        attachment_urls = list()
        image_cqcodes = list()
        for attachment in message.attachments:
            attachment_urls.append(attachment.url)
            if attachment.content_type in img_MIME:
                # 尝试利用discord.py加载图片为base64，使用代理情况下会无法连接
                #image = await attachment.read(use_cached=False)
                #image_base64 = base64.b64encode(image).decode("utf8")
                #image_cqcodes.append(f"[CQ:image,file=base64://{image_base64}==,timeout=5]")
                image_cqcodes.append(f"[CQ:image,file={attachment.url},timeout=5]")
        for embed in message.embeds:
            if embed.image.proxy_url:
                image_cqcodes.append(f"[CQ:image,file={embed.image.proxy_url},timeout=5]")
                attachment_urls.append(embed.image.proxy_url)
        attachment_str = ' ; '.join(attachment_urls)
        image_str = "".join(image_cqcodes)
        content = self.push_text_processor.sub(message.content)
        if self.do_toast:
            if status == '标注消息':
                toast_title = '%s #%s %s' % (message.guild.name, message.channel.name, status)
            elif len(self.message_user) != 0:
                toast_title = '%s %s' % (self.message_user[str(message.author.id)], status)
            else:
                toast_title = '%s %s' % (message.author.name, status)
            if len(content) >= 240:
                toast_text = content[:240] + "..." if len(message.attachments) == 0 else content + "..." + "[附件]"
            else:
                toast_text = content if len(message.attachments) == 0 else content + "[附件]"
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
        keywords = {"type": status,
                    "user_id": str(message.author.id),
                    "user_name": message.author.name,
                    "user_discriminator": message.author.discriminator,
                    "channel_id:": str(message.channel.id),
                    "channel_name": message.channel.name,
                    "server_id": str(message.guild.id),
                    "server_name": message.guild.name,
                    "content": self.push_text_processor.escape_cqcode(content),
                    "content_cat": content_cat,
                    "attachment": attachment_str,
                    "image": image_str,
                    "time": t,
                    "timezone": timezone.zone}
        if len(self.message_user) != 0:
            keywords["user_display_name"] = self.message_user[str(message.author.id)]
        else:
            keywords["user_display_name"] = message.author.name + '#' + message.author.discriminator
        push_text = self.push_text_processor.push_text_process(keywords, is_user_dynamic=False)
        asyncio.create_task(self.qq_push.push_message(push_text, 1))

    async def process_user_update(self, before, after, user: discord.Member, status):
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
            toast_title = '%s %s' % (self.user_dynamic_user[str(user.id)], status)
            toast_text = '变更后：%s' % after
            notification.notify(toast_title, toast_text[:250], app_icon='icon.ico', app_name='Discord Monitor')
        t = datetime.datetime.now(tz=timezone).strftime('%Y/%m/%d %H:%M:%S')
        log_text = '%s: ID: %d. Username: %s. Server: %s. Before: %s. After: %s.' % \
                   (status, user.id,
                    user.name + '#' + user.discriminator,
                    user.guild.name, before, after)
        add_log(0, 'Discord', log_text)
        keywords = {"type": status,
                    "user_id": user.id,
                    "user_name": user.name,
                    "user_discriminator": user.discriminator,
                    "user_display_name": self.user_dynamic_user[str(user.id)],
                    "server_id": str(user.guild.id),
                    "server_name": user.guild.name,
                    "before": before,
                    "after": after,
                    "time": t,
                    "timezone": timezone.zone}
        push_text = self.push_text_processor.push_text_process(keywords, is_user_dynamic=True)
        asyncio.create_task(self.qq_push.push_message(push_text, 2))

    async def on_ready(self, *args, **kwargs):
        """
        完全准备好时触发，暂时用于处理大型服务器中无法接收消息的问题，随时可能被依赖库修复

        :param args:
        :param kwargs:
        :return:
        """
        if not self.user.bot:
            for guild in self.guilds:
                payload = {
                    "op": 14,
                    "d": {
                        "guild_id": str(guild.id),
                        "typing": True,
                        "threads": False,
                        "activities": True,
                        "members": [],
                        "channels": {
                            str(guild.channels[0].id): [
                                [
                                    0,
                                    99
                                ]
                            ]
                        }
                    }
                }
                asyncio.ensure_future(self.ws.send_as_json(payload), loop=self.loop)

    async def on_connect(self):
        """
        监听连接事件，每次连接会刷新所监视用户的用户名列表。

        重写自discord.Client

        ***眼来了***

        :return:
        """
        log_text = 'Logged in as %s, ID: %d.' % (self.user.name + '#' + self.user.discriminator, self.user.id)
        print(log_text + '\n')
        add_log(0, 'Discord', log_text)
        if self.user_monitoring:
            for uid in self.user_dynamic_user:
                uid = int(uid)
                user = None
                for guild in self.guilds:
                    try:
                        user = await guild.fetch_member(uid)
                    except:
                        continue
                if user:
                    self.username_dict[uid] = [user.name, user.discriminator]
                else:
                    log_text = 'Fetching ID %s\'s username failed.' % uid
                    add_log(2, 'Discord', log_text)

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
        if channel.id in self.message_channel or len(self.message_channel) == 0 or \
                (channel.guild.name in self.message_channel_name and channel.name in self.message_channel_name[channel.guild.name]):
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
        if self.is_monitored_object(before, None, before.guild, user_dynamic=True):
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
            if self.username_dict[before.id][0] != after.name or self.username_dict[before.id][1] != after.discriminator:
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
        if event in self.event_set:
            return False
        else:
            self.event_set.add(event)
            return True

    def delete_event(self, event):
        """
        延时删除set中的用户动态事件

        :param event: event
        :return:
        """
        asyncio.get_event_loop().call_later(5, self.event_set.remove, event)

    async def close(self):
        """
        关闭至discord的连接，以及QQPush模块的连接

        :return:
        """
        await asyncio.gather(
            super(DiscordMonitor, self).close(),
            self.qq_push.close()
        )


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if config.bot:
        intents = discord.Intents.default()
        dc = DiscordMonitor(loop=loop, intents=intents)
    else:
        dc = DiscordMonitor(loop=loop)
    try:
        print('Logging in...')
        loop.run_until_complete(dc.start(config.token))
    except (ClientProxyConnectionError, InvalidURL):
        print('代理错误，请检查代理设置')
    except (TimeoutError, ClientConnectorError):
        print('连接超时，请检查连接状态及代理设置')
    except discord.errors.LoginFailure:
        print('登录失败，请检查Token及bot设置是否正确，或更新Token，或检查是否使用了正确的discord.py依赖库')
    except KeyboardInterrupt:
        print("用户退出")
    except Exception:
        print('登录失败，请检查配置文件中各参数是否正确')
        traceback.print_exc()
    finally:
        loop.run_until_complete(dc.close())
        # 2022.5.8：
        # Windows环境下aiohttp似乎会在程序退出释放内存时自动调用方法关闭事件循环导致报错，在此对平台进行特判
        # 暂未测试在Linux下的表现
        if platform.system() != 'Windows':
            loop.close()


if __name__ == '__main__':
    main()
    if platform.system() == 'Windows':
        os.system('pause')
