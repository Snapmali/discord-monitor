# discord-monitor

[![GitHub release](https://img.shields.io/github/v/release/Snapmali/discord-monitor?include_prereleases)](https://github.com/Snapmali/discord-monitor/releases)
[![GitHub](https://img.shields.io/github/license/snapmali/discord-monitor)](https://github.com/Snapmali/discord-monitor/blob/master/LICENSE)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FSnapmali%2Fdiscord-monitor.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FSnapmali%2Fdiscord-monitor?ref=badge_shield)

## 功能介绍


通过监听discord.py事件监测Discord中的消息及用户动态。

* 消息动态：可监测消息发送、消息编辑、消息删除、频道内消息标注（pin），可监测频道中所有消息，亦可由频道名、频道ID、用户ID指定被监测的频道及用户
* 用户动态：在指定被监测用户时，可通过Bot监视时可监测用户的用户名及标签更新、Server内昵称更新、在线状态更新、游戏动态更新；使用用户（非Bot）监视时仅可监测用户的用户名及标签更新、Server内昵称更新。
* Windows 10系统下可将动态推送至通知中心
* 可将监测到的动态由[cqhttp-mirai](https://github.com/yyuueexxiinngg/cqhttp-mirai)、[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)等兼容[onebot]('https://github.com/howmanybots/onebot')接口标准的应用推送至QQ私聊及群聊，支持将本脚本与cqhttp应用异地部署。
* 可在配置文件中设置各QQ用户或群聊是否接受消息动态及用户动态推送

脚本的实现基于[discord.py库](https://pypi.org/project/discord.py/)，QQ推送部分代码参考了[lovezzzxxx](https://github.com/lovezzzxxx)大佬的[livemonitor](https://github.com/lovezzzxxx/livemonitor)脚本，在此感谢。

## 食用方法

### 环境依赖

<b>[Release](https://github.com/Snapmali/discord-monitor/releases)中发布了exe版本，配置过config.json后在Windows下可直接运行，仅需再下载[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)即可。</b>

基于python3.7版本编写，python3.8版本可正常运行，其他版本未测试。3.4及以下版本应无法运行。同时在Ubuntu 16.04上可正常运行。

外部依赖库：requests, discord.py, plyer, pytz。可分别在命令行中执行`pip install requests` `pip install discord.py` `pip install plyer` `pip install pytz`进行安装。

QQ推送部分依赖[cqhttp-mirai](https://github.com/yyuueexxiinngg/cqhttp-mirai)、[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)等应用实现。其中go-cqhttp的部署较为简单，在其[release](https://github.com/Mrs4s/go-cqhttp/releases)中下载系统对应版本后运行即可，具体使用方法请参阅其文档。


### 脚本运行

将`DiscordMonitor.py`和`config.json`放入同一文件夹下。运行前需要自定义`config.json`文件。

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

    //非Bot用户时的轮询间隔时间，单位为秒
    "interval": 60,

    //是否将动态推送至Windows 10系统通知中，非Windows 10系统下此选项失效
    "toast": true,

    //消息监听配置
    "message_monitor": {

        //监听的用户列表，其中key为用户ID，为字符串；value为在推送中显示的名称，为字符串。
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

    //推送文本格式自定义
    "push_text": {

        //自定义消息动态推送格式，为字符串，格式见下文。
        "message_format": "[Discord <user_display_name> <type>]\nContent: <content>\nAttachment: <attachment>\nChannel: <server_name> #<channel_name>\nTime: <time> <timezone>",

        //自定义用户动态推送格式，为字符串，格式见下文。
        "user_dynamic_format": "[Discord <user_display_name> <type>]\nBefore: <before>\nAfter: <after>\nServer: <server_name>\nTime: <time> <timezone>",

        //自定义消息动态正文字词替换，可用于替换discord服务器自定义表情等。
        //key为待替换字符串，支持正则表达式，value为替换字符串。
        //靠前的优先替换。
        //留空表示不进行字符串替换。
        "replace": {"Pattern 1": "Replace 1", "Pattern 2":  "Replace 2"}
    }
}
```

其中监测的Discord用户及Server的ID可在Discord UI中右键点击用户或Server中得到。

用于监测的Bot（电子眼）的Token可在Discord Developer中查看，非Bot用户（肉眼）的Token需在浏览器的开发者工具中获得，具体方法可观看视频[How to get your Discord Token(Youtube)](https://youtu.be/tI1lzqzLQCs)，不算复杂。

#### 推送文本自定义格式

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
|&lt;attachment&gt;|discord消息附件链接，中间用"; "隔开，若无附件则为空("")|消息动态|
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

```
John aa <user_name> bb \John cc <typo>
```

对于消息动态正文字词替换，仅作用于discord消息正文（即&lt;content&gt;部分），且替换正文中所有关键词，支持正则表达式，同时有先后顺序，靠前的优先替换。

#### 监测账户相关注意事项

<b>需要注意，通过用户Token使用本脚本可能违反Discord使用协议（请参阅[Automated user accounts (self-bots)](https://support.discord.com/hc/en-us/articles/115002192352)），并可能导致账号封停。有条件的话建议使用Bot，否则请谨慎使用或使用小号（义眼）。</b>

<b>同时，通过非Bot用户监视时，利用事件监测用户动态方法失效，仅可通过定时查询api方法监测用户用户名及标签更新、Server内昵称更新，此时动态将不会及时推送，同时无法监测在线状态更新及游戏动态更新。</b>

另外对于bot用户，由于Discord会对bot请求用户动态以及server内用户列表进行限制，若需使用本脚本的用户动态监控，则需要在[Discord Application](https://discord.com/developers/applications)的Bot设置页中启用"PRESENCE INTENT"及"SERVER MEMBERS INTENT"。若不启用则用户动态监视功能失效，无其他影响。


## 已知问题

#### 私聊推送失效

利用cqhttp应用向私聊中推送消息时，需要双方互为好友且对方已向己方发送过消息才可向对方发送消息。

#### 编辑消息及删除消息监视失灵

目前仅可捕获脚本启动后发送的最新的1000条消息的编辑及删除事件，启动前以及在启动后最新的1000条以外的消息暂时不能获知其编辑或删除。

#### 无征兆断连

若脚本出现断连且再未提示Logged in，但discord发送消息时脚本可正常反应，可能是由于未知原因脚本未捕获connect事件，实际对脚本运行无影响。

**↓此问题可能已修复**

如果在中国大陆运行脚本并使用代理，出现无法登录，或多次断连后脚本再无动态，且discord发送消息脚本也无反应的问题，可能是由于依赖库discord.py使用的Websockets库不支持代理连接，导致脚本配置的代理无法被正确使用，可参阅[#4204 Switching Websockets library to support proxy scenarios](https://github.com/Rapptz/discord.py/issues/4204)。实际上断连问题是否出现以及出现频率会受网络运营商、线路、地区等因素影响。暂无较完美的解决方案，可尝试在Windows端使用proxifier、或在Linux端使用netns，以避免在直接脚本中使用代理，从而绕开此问题，实际效果较为良好。

## License

This software is under the GPL-3.0 license.
