import re
from typing import Dict, Pattern

from Config import push_content

keys = ["type", "user_id", "user_name", "user_discriminator", "user_display_name", "channel_id", "channel_name",
        "server_id", "server_name", "attachment", "image", "before", "after", "time", "timezone", "content", "content_cat"]
escape_character = {"&": "&amp;", "[": "&#91;", "]": "&#93;"}


class PushTextProcessor:

    def __init__(self):
        self.keyword2num = dict()
        self.num2keyword = dict()
        for i in range(len(keys)):
            self.keyword2num[keys[i]] = i
            self.num2keyword[i] = keys[i]
        self.message_blocks = self.format_preprocess(push_content.message_format)
        self.user_dynamic_blocks = self.format_preprocess(push_content.user_dynamic_format)
        self.replace_dict = self.pattern_dict_preprocess(push_content.replace)
        self.content_cat_dict = self.pattern_dict_preprocess(push_content.categories)

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

    def pattern_dict_preprocess(self, pattern_dict: Dict[str, str]) -> Dict[Pattern, str]:
        """
        预处理用户自定义的用于替换discord消息正文的正则表达式

        :param pattern_dict: config中用户自定义正则表达式字典
        :return:
        """
        pattern_dict_compiled = dict()
        for k in pattern_dict:
            pattern = re.compile(k)
            pattern_dict_compiled[pattern] = pattern_dict[k]
        return pattern_dict_compiled

    def get_content_cat(self, content: str):
        """
        匹配消息动态正文类别

        :param content: 消息正文
        :return:
        """
        if len(self.content_cat_dict) == 0:
            return ""
        for pattern in self.content_cat_dict:
            if re.search(pattern, content):
                return self.content_cat_dict[pattern]
        return None

    def sub(self, content: str):
        """
        正则表达式替换消息正文内容

        :param content: discord消息正文
        :return:
        """
        for pattern in self.replace_dict:
            content = re.sub(pattern, self.replace_dict[pattern], content)
        return content

    def push_text_process(self, keywords: Dict[str, str], is_user_dynamic: bool):
        """
        处理推送消息

        :param keywords: 消息中各信息的字典
        :param is_user_dynamic: 是否为用户动态推送
        :return:
        """
        if is_user_dynamic:
            blocks = self.user_dynamic_blocks.copy()
        else:
            blocks = self.message_blocks.copy()
        for i in range(len(blocks)):
            block = blocks[i]
            if type(block) == int:
                keyword = self.num2keyword[block]
                v = keywords[keyword]
                if not v:
                    v = "None"
                blocks[i] = v
        return "".join(blocks)

    def escape_cqcode(self, text: str):
        escaped_text = ""
        for c in text:
            if c in escape_character:
                escaped_text += escape_character[c]
            else:
                escaped_text += c
        return escaped_text
