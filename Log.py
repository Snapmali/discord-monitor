import time
import traceback

log_path = 'discord_monitor.log'


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
