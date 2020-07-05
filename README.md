# 功能介绍

通过监听discord.py事件监测Discord中的消息及用户动态。

* 消息动态：可监测消息发送、消息编辑、消息删除、频道内消息标注（pin）
* 用户动态：可监测用户用户名及标签更新、Server内昵称更新、在线状态更新、游戏动态更新
* 可将监测到的动态由[酷Q](https://cqp.cc/)推送至QQ私聊及群聊
* 由Server及用户ID指定监测的Server及用户
* 可在配置文件中设置各QQ用户或群聊是否接受消息动态及用户动态推送

脚本的实现基于[discord.py库](https://pypi.org/project/discord.py/)，QQ推送部分代码参考了[lovezzzxxx](https://github.com/lovezzzxxx)大佬的[livemonitor](https://github.com/lovezzzxxx/livemonitor)脚本，在此感谢。

# 食用方法

## 环境依赖

<b>[Release](https://github.com/Snapmali/discord-monitor/releases)中发布了exe版本，在Windows下可直接运行，且包含酷Q及coolq-http-api，无需再安装依赖。</b>

基于python3.7版本编写，其他版本未测试。3.4及以下版本应无法运行。同时未在Linux上进行测试。

外部依赖库：requests, discord.py。可分别在命令行中执行`pip install requests`和`pip install discord.py`进行安装。

QQ推送部分采用[酷Q](https://cqp.cc/)及[coolq-http-api](https://github.com/richardchien/coolq-http-api/releases)插件实现。

* 在Windows下，直接下载安装酷Q软件，并在安装目录下新建`app`文件夹，将cool-http-api插件的`io.github.richardchien.coolqhttpapi.cpk`文件放入其中。运行并登录QQ小号后，右键点击悬浮窗，在应用->应用管理中启用cool-http-api插件即可。其默认监听端口为5700。
* 由于未在Linux上测试，建议查阅[lovezzzxxx](https://github.com/lovezzzxxx)的[livemonitor](https://github.com/lovezzzxxx/livemonitor#qq%E6%8E%A8%E9%80%81%E5%8F%AF%E9%80%89)脚本的Readme进行安装。

## 脚本运行

将`DiscordMonitor.py`和`config.json`放入同一文件夹下。运行前需要自定义`config.json`文件：

```
{
    //Discord用户或Bot的Token字段（你插的眼）
    "token": "User Token or Bot Token", 

    //上述Token是否属于Bot，是则为true，否则为false
    "is_bot": true, 

    //coolq-http-api插件的监听端口，默认为5700
    "coolq_port": 5700, 
    
    //网络代理的http地址，留空（即"proxy": ""）表示不设置代理
    "proxy": "Proxy URL, leave blank for no proxy, e.g. http://localhost:1080", 

    "monitor": {
        //监听的用户列表，其中key为用户ID，为字符串；value为在推送中显示的名称，为字符串
        "user_id": {"User ID": "Display name", "123456789": "John Smith"},

        //监听的server列表，列表中值为服务器ID，为整型数。特别的，列表为[true]时表示监听所有Server
        "server": [1234567890, 9876543210]
        //"server: [true]"
    },
    "push": {
        //推送的QQ用户或群聊，为嵌套列表。底层列表第一个值为QQ号或群号；
        //第二个值为布尔型，表示是否推送消息动态；第三个值为布尔型，表示是否推送用户动态
        "QQ_group": [[1234567890, true, false], [9876543210, true, true]],
        "QQ_user": [[1234567890, true, false], [9876543210, true, true]]
    }
}
```

其中监测的Discord用户及Server的ID可在Discord UI中右键点击用户或Server中得到。

用于监测的Bot（电子眼）的Token可在Discord Developer中查看，用户（肉眼）的Token需在浏览器的开发者工具中获得，具体方法可观看视频[How to get your Discord Token(Youtube)](https://youtu.be/tI1lzqzLQCs)，不算复杂。

<b>需要注意，通过用户（肉眼）Token使用本脚本可能违反Discord使用协议（请参阅[Automated user accounts (self-bots)](https://support.discord.com/hc/en-us/articles/115002192352)），并可能导致账号封停。有条件的话建议使用Bot，否则</b>~~比如fanbox server啥的~~<b>请谨慎使用或使用小号（义眼）。</b>

配置文件修改完毕后，在命令行中运行`python DiscordMonitor.py`即可。推送消息中默认时区为东八区。

# 已知问题

#### 私聊推送失效

利用酷Q向私聊中推送消息时，需要双方互为好友且对方已向己方发送过消息。

#### 无征兆断连

初步判断是使用用户Token登录后4-5小时会出现无征兆断连情况，Bot登录暂时未发现问题，正在尝试修复中。
