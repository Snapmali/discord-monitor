# discord-monitor

[![GitHub release](https://img.shields.io/github/v/release/Snapmali/discord-monitor?include_prereleases)](https://github.com/Snapmali/discord-monitor/releases)
[![GitHub](https://img.shields.io/github/license/snapmali/discord-monitor)](https://github.com/Snapmali/discord-monitor/blob/master/LICENSE)

## 功能介绍

通过监听discord.py事件监测Discord中的消息及用户动态。

* 消息动态：可监测消息发送、消息编辑、消息删除、频道内消息标注（pin）；可选择监测频道中所有消息动态，亦可由频道名、频道ID、用户ID指定被监测的频道及用户。
* 用户动态：可指定被监测用户，并监测其用户名及标签更新、Server内昵称更新、在线状态更新、活动状态更新。
* Windows 10系统下可将动态推送至通知中心。
* 可分别自定义消息动态与用户动态推送消息格式。其中对消息动态可通过关键词进行类别匹配与字符替换，支持正则表达式。
* 可将监测到的动态由[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)等兼容[onebot]('https://github.com/howmanybots/onebot')接口标准的应用推送至QQ私聊及群聊，支持将本脚本与cqhttp应用异地部署。
* 可在配置文件中设置各QQ用户或群聊是否接受消息动态及用户动态推送

脚本的实现基于[discord.py](https://pypi.org/project/discord.py/)，[discord.py-self](https://github.com/dolfies/discord.py-self)，QQ推送部分代码参考了[lovezzzxxx](https://github.com/lovezzzxxx)大佬的[livemonitor](https://github.com/lovezzzxxx/livemonitor)脚本，在此感谢。

## 食用方法

### 环境依赖

**[Release](https://github.com/Snapmali/discord-monitor/releases)中发布了exe版本，配置过config.json后在Windows下可直接运行，仅需再下载[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)即可。**

基于python3.8版本编写，其他版本未测试。3.4及以下版本应无法运行。同时在Ubuntu 16.04上可正常运行。

#### 外部依赖库

##### discord.py相关

* 若使用Bot进行监视，可正常使用[discord.py](https://pypi.org/project/discord.py/) 1.7.\*版本<b>（2.\*版本暂不支持）</b>。
* 若使用用户（非Bot）进行监视，需使用其分支[discord.py-self](https://github.com/dolfies/discord.py-self)，具体原因可见[此issue](https://github.com/Snapmali/discord-monitor/issues/10)。

由于二者包名相同，建议仅下载安装所需的库，或使用虚拟环境。

2022.5.8：discord.py-self仅声明兼容aiohttp<3.8.0,>=3.6.0，**因此pip安装discord.py-self时会自动卸载aiohttp 3.8.0及以上版本**，请务必注意。

若需要同时使用discord.py-self及代理，则aiohttp版本需要为3.8.0以上，请在安装完discord.py-self后强制升级aiohttp，pip会报兼容性问题，但脚本实际运行时并未发现错误。

```shell
# discord.py
pip install -U discord.py

# discord.py-self
pip install -U discord.py-self
# 强制升级aiohttp至3.8.0以上
pip install -U aiohttp
```

##### 其他依赖库

```shell
pip install -U aiohttp plyer datetime pytz
```

QQ推送依赖cqhttp应用实现。其中[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)的部署较为简单，在其[release](https://github.com/Mrs4s/go-cqhttp/releases)中下载系统对应版本后运行即可，具体使用方法请参阅其文档。

### 脚本运行

运行前需要自定义`config.json`文件。

配置文件修改完毕后，在命令行中运行`python DiscordMonitor.py`即可。推送消息中默认时区为东八区。

#### config.json 格式说明

```json5
{
    //Discord用户或Bot的Token字段（你插的眼）
    "token": "User Token or Bot Token", 

    //上述Token是否属于Bot，是则为true，否则为false
    "is_bot": true, 

    //cqhttp应用的URL，若在本机部署则默认为"http://localhost:5700"
    "coolq_url": "http://localhost:5700", 

    //cqhttp应用的access token，若未设置access token请留空（即"coolq_token": ""）
    "coolq_token": "Coolq-http-api access token, leave blank for no token",
    
    //网络代理的http地址，留空（即"proxy": ""）表示不设置代理
    "proxy": "Proxy URL, leave blank for no proxy, e.g. http://localhost:1080", 

    //是否将动态推送至Windows 10系统通知中，非Windows 10系统下此选项失效
    "toast": true,

    //消息监听配置
    "message_monitor": {

        //监听的用户列表，其中key为用户ID，为字符串；value为在推送中显示的名称，为字符串。
        //value将体现在<user_display_name>关键词中。
        //列表为空时表示监听被监听频道中的所有消息。
        "user_id": {"User ID": "Display name", "123456789": "John Smith"},
        //"user_id": {},

        //通过频道ID监听消息的频道列表，列表中值为频道ID，为整型数。
        //列表为空时表示监听所有频道。
        //填0时表示不通过频道ID监听消息动态。
        "channel": [1234567890],
        //"channel": [],

        //通过频道名监听消息的频道列表，为嵌套列表。底层列表第一个值为Server名，其余值为频道名
        //留空时表示不通过频道名监听消息动态。
        "channel_name": [["Server 1 name", "Channel 1 name", "Channel 2 name", "Channel 3 name"],
                            ["Server 2 name", "Channel 4 name"]]
        //"channel_name": []
    },

    //用户动态监视配置
    "user_dynamic_monitor": {

        //监听的用户列表，其中key为用户ID，为字符串；value为在推送中显示的名称，为字符串。
        //列表为空时表示不监听用户动态。
        "user_id": {"User ID": "Display name", "987654321": "Sophia Smith"},

        //监听的server列表，列表中值为服务器ID，为整型数。
        //列表为空时表示监听所有Server。
        //填0时表示不监听用户动态。
        "server": [1234567890, 9876543210]
        //"server": []
    },

    //推送设置
    "push": {
        //推送的QQ用户或群聊，为嵌套列表。底层列表第一个值为QQ号或群号；
        //第二个值为布尔型，表示是否推送消息动态；第三个值为布尔型，表示是否推送用户动态。
        //列表可留空，表示不推送给私聊或群聊。
        "QQ_group": [[1234567890, true, false], [9876543210, true, true]],
        "QQ_user": [[1234567890, true, false], [9876543210, true, true]]
        //"QQ_group": [],
        //"QQ_user": []
    },

    //推送文本格式自定义，此部分建议参阅下文“推送文本自定义”部分
    "push_text": {

        //自定义消息动态推送格式，为字符串，格式见下文。
        "message_format": "[Discord <user_display_name> <type>]\nContent: <content>\nAttachment: <attachment>\nChannel: <server_name> #<channel_name>\nTime: <time> <timezone>",

        //自定义用户动态推送格式，为字符串，格式见下文。
        "user_dynamic_format": "[Discord <user_display_name> <type>]\nBefore: <before>\nAfter: <after>\nServer: <server_name>\nTime: <time> <timezone>",

        //自定义消息动态正文类别，若消息中出现匹配字符则将其视作指定类别的消息。
        //key为匹配字符串，支持正则表达式，value为指定消息类别。
        //value将体现在<content_cat>关键词中。不会替换原文字符。
        //靠前的优先匹配。没有可匹配类别的消息将不进行推送。
        //特别的，""可匹配所有消息，留空表示不进行类别匹配。
        "category": {"Pattern 1": "Category 1", "As Long As You Love Me": "Music", "": "Others"},

        //自定义消息动态正文字词替换，可用于替换discord服务器自定义表情等。
        //key为待替换字符串，支持正则表达式，value为替换的字符串。
        //靠前的优先替换。
        //留空表示不进行字符串替换。
        "replace": {"Pattern 1": "Replace 1", "Pattern 2":  "Replace 2"}
    }
}
```

其中监测的Discord用户及Server的ID可在Discord UI中右键点击用户或Server中得到。

用于监测的Bot（电子眼）的Token可在Discord Developer中查看，非Bot用户（肉眼）的Token需在浏览器的开发者工具中获得，具体方法可观看视频[How to get your Discord Token(Youtube)](https://youtu.be/tI1lzqzLQCs)，不算复杂。

#### 推送文本自定义

##### 1. 通过关键词自定义推送消息格式

v0.8.0版本后允许自定义推送消息文本，且消息动态推送与用户动态推送可分别设置格式。功能通过关键词替换方法实现，可用关键词如下：

|关键词|含义|可用推送范围|
|-----|---|---|
|&lt;type&gt;|消息类别，如“发送消息”、“编辑消息”、“昵称更新”等|消息动态，用户动态|
|&lt;user_id&gt;|用户ID|消息动态，用户动态|
|&lt;user_name&gt;|用户名|消息动态，用户动态|
|&lt;user_discriminator&gt;|用户标签(例：#2587)|消息动态，用户动态|
|&lt;user_display_name&gt;|在config.json中自定义的用户别名，若未设置则为"用户名#标签"|消息动态，用户动态|
|&lt;channel_id&gt;|频道ID|消息动态|
|&lt;channel_name&gt;|频道名|消息动态|
|&lt;server_id&gt;|服务器ID|消息动态，用户动态|
|&lt;server_name&gt;|服务器名|消息动态，用户动态|
|&lt;content&gt;|discord消息正文|消息动态|
|&lt;content_cat&gt;|discord消息正文类别，在config.json中自定义|消息动态|
|&lt;attachment&gt;|discord消息附件链接，中间用"; "隔开，若无附件则为空("")|消息动态|
|&lt;image&gt;|discord消息图片，直接在QQ消息中显示|消息动态|
|&lt;before&gt;|用户动态变化前的项|用户动态|
|&lt;after&gt;|用户动态变化后的项|用户动态|
|&lt;time&gt;|时间，默认格式为"2021/01/30 00:00:00"|消息动态，用户动态|
|&lt;timezone&gt;|时区，默认为"Asia/Shanghai"|消息动态，用户动态|

同时，可对关键词进行转义，如：

```json
{
    "message_format": "<user_name> aa \\<user_name> bb \\\\<user_name> cc <typo>"
}
```

输出格式为：

```plain
John aa <user_name> bb \John cc <typo>
```

请注意，在QQ消息中显示discord消息图片功能需通过cqhttp应用连接至discord CDN服务器实现，**如有必要请在cqhttp应用的配置文件中添加代理设置。**

##### 2.消息动态正文类别匹配与字符替换

消息动态正文类别匹配仅作用于discord消息正文（即&lt;content&gt;部分），且不会替换原文字符。先于正文字词替换，不受替换影响，支持正则表达式，同时有先后顺序，靠前的优先匹配。无匹配类别的消息将不会被推送。`""`会匹配所有消息，可在最后用`"": "Others"`兜底未匹配类别的消息。

对于消息动态正文字词替换，仅作用于discord消息正文（即&lt;content&gt;部分），且替换正文中所有关键词，支持正则表达式，同时有先后顺序，靠前的优先替换。常用`"<.*?>"`匹配服务器自定义表情(在推送消息中其格式为&lt;:Sadge:733427917308166177&gt;)。

#### 监测账户相关注意事项

**需要注意，通过用户Token使用本脚本可能违反Discord使用协议（请参阅[Automated user accounts (self-bots)](https://support.discord.com/hc/en-us/articles/115002192352)），并可能导致账号封停。有条件的话建议使用Bot，否则请谨慎使用或使用小号（义眼）。**

另外对于bot用户，由于Discord会对bot请求用户动态以及server内用户列表进行限制，若需使用本脚本的用户动态监控，则需要在[Discord Application](https://discord.com/developers/applications)的Bot设置页中启用"PRESENCE INTENT"及"SERVER MEMBERS INTENT"。若不启用则用户动态监视功能失效，无其他影响。

## 已知问题

### 私聊推送失效

利用cqhttp应用向私聊中推送消息时，需要双方互为好友且对方已向己方发送过消息才可向对方发送消息。

### 编辑消息及删除消息监视失灵

目前仅可捕获脚本启动后发送的最新的1000条消息的编辑及删除事件，启动前以及在启动后最新的1000条以外的消息暂时不能获知其编辑或删除。

### 无征兆断连

若脚本出现断连且再未提示Logged in，但discord发送消息时脚本可正常反应，可能是由于未知原因脚本未捕获connect事件，实际对脚本运行无影响。

### 非Bot监视时推送消息中无消息正文

非Bot监视请使用discord.py-self依赖库。详情参见[用户bot (user-bot / self-bot) 无法获取消息的content](https://github.com/Snapmali/discord-monitor/issues/10)。

## License

This software is under the GPL-3.0 license.
