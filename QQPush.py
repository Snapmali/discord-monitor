import json
import threading
import time
import requests

from Log import add_log


class QQPush(object):

    def __init__(self, qq_user, qq_group, coolq_url, coolq_token):
        self.qq_user = qq_user
        self.qq_group = qq_group
        self.coolq_url = coolq_url
        self.coolq_token = coolq_token

    def push_message(self, message, permission):
        """
        建立线程并将消息推送至coolq-http-api

        :param message: message text
        :param permission: 1表示消息动态，2表示用户动态
        :return:
        """
        for group in self.qq_group:
            if group[permission]:
                t = threading.Thread(args=(message, group[0], 'group'), target=self.push_thread)
                t.setDaemon(True)
                t.start()
        for user in self.qq_user:
            if user[permission]:
                t = threading.Thread(args=(message, user[0], 'user'), target=self.push_thread)
                t.setDaemon(True)
                t.start()

    def push_thread(self, message, qq_id, id_type):
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

