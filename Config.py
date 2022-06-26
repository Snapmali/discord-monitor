import json
import os
import platform
import sys


class Config:
    def __init__(self, data: dict):
        self.token = data['token']
        self.bot = data['is_bot']
        self.cqhttp_url = data['coolq_url'].rstrip('/')
        self.cqhttp_token = data['coolq_token']
        self.proxy = data['proxy']
        self.toast = data['toast']
        self.message_monitor = Config.MessageMonitor(data['message_monitor'])
        self.user_dynamic_monitor = Config.UserDynamicMonitor(data['user_dynamic_monitor'])
        self.push = Config.Push(data['push'])
        self.push_content = Config.PushContent(data['push_text'])

    class MessageMonitor:
        def __init__(self, data: dict):
            self.users = data['user_id']
            self.channel_ids = data['channel']
            self.channel_names = dict()
            for guilds in data['channel_name']:
                channels = self.channel_names.get(guilds[0])
                if channels is None:
                    channels = set()
                    self.channel_names[guilds[0]] = channels
                for i in range(1, len(guilds)):
                    channels.add(guilds[i])

    class UserDynamicMonitor:
        def __init__(self, data: dict):
            self.users = data['user_id']
            self.servers = set(data['server'])

    class Push:
        def __init__(self, data: dict):
            self.groups = data['QQ_group']
            self.users = data['QQ_user']

    class PushContent:
        def __init__(self, data: dict):
            self.categories = data["category"]
            self.message_format = data["message_format"]
            self.user_dynamic_format = data["user_dynamic_format"]
            self.replace = data["replace"]


def read_config() -> Config:
    while True:
        config_path = 'config.json'
        try:
            config_path_temp = input('请输入配置文件路径，空输入则为默认(默认为config.json):\n')
            if config_path_temp != '':
                config_path = config_path_temp
            with open(config_path, 'r', encoding='utf8') as f:
                return Config(json.load(f))
        except FileNotFoundError:
            print('配置文件不存在')
        except KeyboardInterrupt:
            sys.exit(1)
        except Exception:
            print('配置文件读取出错，请检查配置文件各参数是否正确')
            if platform.system() == 'Windows':
                os.system('pause')
            sys.exit(1)


config = read_config()
message_monitor = config.message_monitor
user_dynamic_monitor = config.user_dynamic_monitor
push = config.push
push_content = config.push_content
