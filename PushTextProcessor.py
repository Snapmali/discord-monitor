import re
from typing import Dict, Pattern


class PushTextProcessor(object):

    def __init__(self, message_format, user_dynamic_format, replace_dict):
        self.keyword2num = {"type": 1,
                            "user_id": 2,
                            "user_name": 3,
                            "user_discriminator": 4,
                            "user_display_name": 5,
                            "channel_id:": 6,
                            "channel_name": 7,
                            "server_id": 8,
                            "server_name": 9,
                            "attachment": 10,
                            "before": 11,
                            "after": 12,
                            "time": 13,
                            "timezone": 14,
                            "content": 15}
        self.num2keyword = {1: "type",
                            2: "user_id",
                            3: "user_name",
                            4: "user_discriminator",
                            5: "user_display_name",
                            6: "channel_id",
                            7: "channel_name",
                            8: "server_id",
                            9: "server_name",
                            10: "attachment",
                            11: "before",
                            12: "after",
                            13: "time",
                            14: "timezone",
                            15: "content"}
        self.message_blocks = self.format_preprocess(message_format)
        self.user_dynamic_blocks = self.format_preprocess(user_dynamic_format)
        self.pattern_dict = self.pattern_dict_preprocess(replace_dict)

    def format_preprocess(self, message_format: str):
        """
        预处理用户自定义推送消息格式

        :param message_format: config中推送消息格式
        :return:
        """
        backslash_count = 0
        is_keyword = False
        candi_keyword = ""
        block_begin = 0
        block_end = 0
        blocks = []
        for i in range(len(message_format)):
            s = message_format[i]
            if backslash_count == 0 and s == '<':
                is_keyword = True
                if i > 1 and message_format[i - 1] == '\\':
                    block_end = i - 1
                else:
                    block_end = i
                candi_keyword = ""
            elif is_keyword:
                if s != '>':
                    candi_keyword += s
                else:
                    is_keyword = False
                    if candi_keyword in self.keyword2num:
                        if block_begin != block_end:
                            blocks.append(message_format[block_begin: block_end])
                        blocks.append(self.keyword2num[candi_keyword])
                        block_begin = i + 1
            elif s == '\\':
                backslash_count += 1
                block_end = i
                if backslash_count == 2:
                    backslash_count = 0
            elif backslash_count == 1 and s == '<':
                backslash_count = 0
                if block_begin != block_end:
                    blocks.append(message_format[block_begin: block_end])
                block_begin = i
            else:
                backslash_count = 0
        if block_begin != len(message_format):
            blocks.append(message_format[block_begin:])
        return blocks

    def pattern_dict_preprocess(self, replace_dict: Dict[str, str]) -> Dict[Pattern, str]:
        """
        预处理用户自定义的用于替换discord消息正文的正则表达式

        :param replace_dict: config中用户自定义正则表达式字典
        :return:
        """
        pattern_dict = dict()
        for k in replace_dict:
            pattern = re.compile(k)
            pattern_dict[pattern] = replace_dict[k]
        return pattern_dict

    def sub(self, content: str):
        """
        正则表达式替换消息正文内容

        :param content: discord消息正文
        :return:
        """
        for pattern in self.pattern_dict:
            content = re.sub(pattern, self.pattern_dict[pattern], content)
        return content

    def push_text_process(self, keywords: Dict[str, str], user_dynamic=True):
        """
        处理推送消息

        :param keywords: 消息中各信息的字典
        :param user_dynamic: 是否为用户动态推送
        :return:
        """
        if user_dynamic:
            blocks = self.user_dynamic_blocks.copy()
        else:
            blocks = self.message_blocks.copy()
        for i in range(len(blocks)):
            block = blocks[i]
            if type(block) == int:
                v = keywords[self.num2keyword[block]]
                if not v:
                    v = "None"
                blocks[i] = v
        return "".join(blocks)
