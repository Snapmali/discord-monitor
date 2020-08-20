# discord-monitor

[![GitHub release](https://img.shields.io/github/v/release/Snapmali/discord-monitor?include_prereleases)](https://github.com/Snapmali/discord-monitor/releases)
[![GitHub](https://img.shields.io/github/license/snapmali/discord-monitor)](https://github.com/Snapmali/discord-monitor/blob/master/LICENSE)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FSnapmali%2Fdiscord-monitor.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FSnapmali%2Fdiscord-monitor?ref=badge_shield)

## 功能介绍

<b>由于酷Q等机器人平台停运，为使QQ推送功能在此风波期间正常运转，可暂时使用[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)作为替代，本脚本利用的go-cqhttp API实现与原本使用的[coolq-http-api](https://github.com/richardchien/coolq-http-api/releases)基本相同，无需对***本脚本***配置文件进行修改。go-cqhttp详细用法请参见其文档。</b>

<b>但本脚本视情况仍不排除使用其他平台，或转用钉钉等IM软件，甚至彻底放弃此功能的可能性，敬请谅解。</b>

通过监听discord.py事件监测Discord中的消息及用户动态。

* 消息动态：可监测消息发送、消息编辑、消息删除、频道内消息标注（pin），可监测频道中所有消息，亦可由频道及用户ID指定被监测的频道及用户
* 用户动态：在指定被监测用户时，可通过Bot监视时可监测用户的用户名及标签更新、Server内昵称更新、在线状态更新、游戏动态更新；使用用户（非Bot）监视时仅可监测用户的用户名及标签更新、Server内昵称更新。
* Windows 10系统下可将动态推送至通知中心
* 可将监测到的动态由~~酷Q~~ [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)推送至QQ私聊及群聊
* 可在配置文件中设置各QQ用户或群聊是否接受消息动态及用户动态推送

脚本的实现基于[discord.py库](https://pypi.org/project/discord.py/)，QQ推送部分代码参考了[lovezzzxxx](https://github.com/lovezzzxxx)大佬的[livemonitor](https://github.com/lovezzzxxx/livemonitor)脚本，在此感谢。

## 食用方法

### 环境依赖

<b>[Release](https://github.com/Snapmali/discord-monitor/releases)中发布了exe版本，配置过config.json后在Windows下可直接运行，仅需再下载[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)即可。</b>

基于python3.7版本编写，python3.8版本可正常运行，其他版本未测试。3.4及以下版本应无法运行。同时在Ubuntu 16.04上可正常运行。

外部依赖库：requests, discord.py, plyer, pytz。可分别在命令行中执行`pip install requests` `pip install discord.py` `pip install plyer` `pip install pytz`进行安装。

QQ推送部分***暂时***依赖[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)实现。其部署较为简单，在其[release](https://github.com/Mrs4s/go-cqhttp/releases)中下载系统对应版本后运行即可，具体使用方法请参阅其文档。


### 脚本运行

将`DiscordMonitor.py`和`config.json`放入同一文件夹下。运行前需要自定义`config.json`文件：

```
{
    //Discord用户或Bot的Token字段（你插的眼）
    "token": "User Token or Bot Token", 

    //上述Token是否属于Bot，是则为true，否则为false
    "is_bot": true, 

    //go-cqhttp的监听端口，默认为5700
    "coolq_port": 5700, 

    //go-cqhttp的access token，若未设置access token请留空（即"coolq_token": ""）
    "coolq_token": "Coolq-http-api access token, leave blank for no token",
    
    //网络代理的http地址，留空（即"proxy": ""）表示不设置代理
    "proxy": "Proxy URL, leave blank for no proxy, e.g. http://localhost:1080", 

    //非Bot用户时的轮询间隔时间，单位为秒
    "interval": 60,

    //是否将动态推送至Windows 10系统通知中，非Windows 10系统下此选项失效
    "toast": true

    "monitor": {

        //监听的用户列表，其中key为用户ID，为字符串；value为在推送中显示的名称，为字符串。
        //特别的，列表为空时表示监听频道中所有消息
        "user_id": {"User ID": "Display name", "123456789": "John Smith"},
        //"user_id": {},
        
        //监听的频道列表，列表中值为频道ID，为整型数。特别的，列表为空时表示监听所有频道
        //仅作用于消息动态监听
        "channel": [1234567890],

        //监听的server列表，列表中值为服务器ID，为整型数。特别的，列表为空时表示监听所有Server
        //仅作用于用户动态监听
        "server": [1234567890, 9876543210]
        //"server: []"
    },
    "push": {
        //推送的QQ用户或群聊，为嵌套列表。底层列表第一个值为QQ号或群号；
        //第二个值为布尔型，表示是否推送消息动态；第三个值为布尔型，表示是否推送用户动态
        //列表可留空，表示不推送给私聊或群聊
        "QQ_group": [[1234567890, true, false], [9876543210, true, true]],
        "QQ_user": [[1234567890, true, false], [9876543210, true, true]]
        //"QQ_group": [],
        //"QQ_user": []
    }
}
```

其中监测的Discord用户及Server的ID可在Discord UI中右键点击用户或Server中得到。

用于监测的Bot（电子眼）的Token可在Discord Developer中查看，非Bot用户（肉眼）的Token需在浏览器的开发者工具中获得，具体方法可观看视频[How to get your Discord Token(Youtube)](https://youtu.be/tI1lzqzLQCs)，不算复杂。

<b>需要注意，通过用户Token使用本脚本可能违反Discord使用协议（请参阅[Automated user accounts (self-bots)](https://support.discord.com/hc/en-us/articles/115002192352)），并可能导致账号封停。有条件的话建议使用Bot，否则</b>~~比如某fanbox server~~<b>请谨慎使用或使用小号（义眼）。</b>

<b>同时，通过非Bot用户监视时，利用事件监测用户动态方法失效，仅可通过定时查询api方法监测用户用户名及标签更新、Server内昵称更新，此时动态将不会及时推送，同时无法监测在线状态更新及游戏动态更新。</b>

配置文件修改完毕后，在命令行中运行`python DiscordMonitor.py`即可。推送消息中默认时区为东八区。

## 已知问题

#### 私聊推送失效

原来使用酷Q过程中出现的问题，go-cqhttp也有可能出现。

利用酷Q向私聊中推送消息时，需要双方互为好友且对方已向己方发送过消息才可向对方发送消息。

#### 编辑消息及删除消息监视失灵

目前仅可捕获脚本启动后发送的最新的1000条消息的编辑及删除事件，启动前以及在启动后最新的1000条以外的消息暂时不能获知其编辑或删除。

#### 无征兆断连

若脚本出现断连且再未提示Logged in，但discord发送消息时脚本可正常反应，可能是由于未知原因脚本未捕获connect事件，实际对脚本运行无影响。

**↓此问题可能已修复**

如果在中国大陆运行脚本并使用代理，出现无法登录，或多次断连后脚本再无动态，且discord发送消息脚本也无反应的问题，可能是由于依赖库discord.py使用的Websockets库不支持代理连接，导致脚本配置的代理无法被正确使用，可参阅[#4204 Switching Websockets library to support proxy scenarios](https://github.com/Rapptz/discord.py/issues/4204)。实际上断连问题是否出现以及出现频率会受网络运营商、线路、地区等因素影响。暂无较完美的解决方案，可尝试在Windows端使用proxifier、或在Linux端使用netns，以避免在直接脚本中使用代理，从而绕开此问题，实际效果较为良好。

## License

This software is under the GPL-3.0 license.
