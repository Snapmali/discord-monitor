import asyncio
import json
import time
import traceback

import aiohttp

from Config import config
from Log import add_log


class QQPush:

    def __init__(self):
        self.qq_user = config.push.users
        self.qq_group = config.push.groups
        self.coolq_url = config.cqhttp_url
        self.coolq_token = config.cqhttp_token
        self.session = aiohttp.ClientSession()
        self.is_closed = False

    async def close(self):
        """
        关闭连接，释放资源

        :return:
        """
        self.is_closed = True
        await self.session.close()

    async def push_message(self, message, permission):
        """
        将消息按配置文件推送至QQ私聊或群聊

        :param message: message text
        :param permission: 1表示消息动态，2表示用户动态
        :return:
        """
        for group in self.qq_group:
            if group[permission]:
                await self._push(message, group[0], 'group')
        for user in self.qq_user:
            if user[permission]:
                await self._push(message, user[0], 'user')

    async def _push(self, message, qq_id, id_type):
        """
        将消息推送至cqhttp
        :param message: message text
        :param qq_id: QQ user ID or group ID
        :param id_type: "group"表示群聊, "user"私聊
        :return:
        """
        # message = pattern.sub(lambda m: rep[re.escape(m.group(0))], message)
        data = {'message': message, 'auto_escape': False}
        headers = {'Content-type': 'application/json'}
        url = '%s/send_msg' % self.coolq_url

        if id_type == 'group':
            data['message_type'] = 'group'
            data['group_id'] = qq_id
        elif id_type == 'user':
            data['message_type'] = 'private'
            data['user_id'] = qq_id

        # 判断是否设置cqhttp access token
        if self.coolq_token != "":
            headers['Authorization'] = "Bearer " + self.coolq_token

        # 5次重试
        for i in range(5):
            try:
                async with self.session.post(url, headers=headers, data=json.dumps(data), timeout=10) as response:
                    if response is not None:
                        if response.status == 200:
                            # cqhttp接受消息，但不知操作实际成功与否
                            log = 'Message to %s %d is sent. Response:%d. Retries:%d. Message: %s' % \
                                  (id_type, qq_id, response.status, i, data)
                            add_log(0, 'PUSH', log)
                            break
                        if response.status == 401:
                            # token needed
                            log = 'Failed to send message to %s %d. Reason: Access token is not provided. ' \
                                  'Response:%d. Retries:%d. Message: %s' % (id_type, qq_id, response.status, i, data)
                            add_log(0, 'PUSH', log)
                            break
                        if response.status == 403:
                            # token is wrong
                            log = 'Failed to send message to %s %d. Reason: Access token is wrong. ' \
                                  'Response:%d. Retries:%d. Message: %s' % (id_type, qq_id, response.status, i, data)
                            add_log(0, 'PUSH', log)
                            break
                        if response.status == 404:
                            # url is wrong
                            log = 'Failed to send message to %s %d. Reason: Coolq URL is wrong. ' \
                                  'Response:%d. Retries:%d. Message: %s' % (id_type, qq_id, response.status, i, data)
                            add_log(0, 'PUSH', log)
                            break
                    if i == 4:
                        # 未超时但失败，还没出过这问题
                        log = 'Failed to send message to %s %d. Response:%d. Message: %s' % \
                              (id_type, qq_id, response.status, data)
                        add_log(0, 'PUSH', log)
            except:
                traceback.print_exc()
                if i == 4:
                    # 哦 5次全超时
                    log = 'Timeout! Failed to send message to %s %d. Message: %s' % \
                          (id_type, qq_id, data)
                    add_log(0, 'PUSH', log)
                    break
                await asyncio.sleep(5)
                if self.is_closed:
                    break
                continue

