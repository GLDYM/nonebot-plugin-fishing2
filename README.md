<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-fishing2

_✨ 更好的电子钓鱼 ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/FDCraft/nonebot-plugin-fishing2.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-fishing2">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-fishing2.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="python">

</div>

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行, 输入以下指令即可安装

    nb plugin install nonebot-plugin-fishing2

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下, 打开命令行, 根据你使用的包管理器, 输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-fishing2
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-fishing2
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-fishing2
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-fishing2
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件, 在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_fishing2"]

</details>

注意：安装过后，需在控制台输入 `nb orm upgrade` 指令以初始化数据库。本插件数据库与 [Nonebot-plugin-fishing](https://github.com/ALittleBot/nonebot-plugin-fishing) 通用，可以互换。

## ⚙️ 配置

在 nonebot2 项目的`.env`文件中添加下表中的配置

| 配置项                   | 必填 | 说明                                                           |
|:------------------------:|:----:|:--------------------------------------------------------------:|
| fishes                   | 否   | 配置鱼塘内的普通鱼（大概是鱼……）                               |
| fishing_achievement      | 否   | 配置钓鱼成就                                                   |
| fishing_coin_name        | 否   | 填入卖鱼获取的货币名称                                         |
| fishing_limit            | 否   | 填入每次钓鱼后，限制钓鱼的秒数                                 |
| punish_limit             | 否   | 短时间多次钓鱼后，禁言所需次数，防止刷屏                       |
| special_fish_enabled     | 否   | 是否启用赛博放生 & 特殊鱼（默认为否）                          |
| special_fish_price       | 否   | 特殊鱼出售的价格                                               |
| special_fish_free_price  | 否   | 特殊鱼放生的价格                                               |
| special_fish_probability | 否   | 钓上特殊鱼的概率，注意这个判定在空军判定之后                   |
| no_fish_probability      | 否   | 空军的概率                                                     |
| rare_fish_weight         | 否   | 稀有鱼权重分界线，影响 rare_fish 属性与 normal_fish 属性的区分 |
| buy_rate                 | 否   | 在不指定 buy_price 时，购买价格/基准价格比，应大于 1           |
| backpack_forward         | 否   | 背包是否使用聊天记录                                           |

其中 `fishes` 配置项说明如下。预设配置经过了计算以平衡，如果需要自行填表，请使用“钓鱼预测”命令进行预测。

```dotenv
FISHES='
    [
        {
            "type": "fish", # 类型，必填，可用值：fish, item，同类型物品不能同时作为鱼饵
            "name": "小鱼", # 名称，必填
            "price": 15, # 基准价格，必填
            "amount": 1, # 单份数量，模拟耐久
            "props": [ # 属性，选填，作为鱼饵时改变
                {
                    "type": "rm_fish", # 可用值: rare_fish, normal_fish, fish, rm_fish, special_fish, no_fish
                    "key": "小鱼", # 如果为 fish 或 rm_fish，需要填写鱼名
                    "value": 0 # 如果为 rare_fish, normal_fish, fish，填写权重；如果为 special_fish, no_fish，填写概率
                }
            ],
            "description": "一条小鱼。把它当做鱼饵可以防止钓到小鱼。", # 描述，必填
            "can_catch": True, # 是否可以抓取，必填
            "sleep_time": 2, # 钓上来需要的时间，默认 60
            "weight": 1000, # 权重
            "can_buy": True, # 是否可以购买，必填
            "buy_price": 50, # 购买价格
            "can_sell": True # 是否可以出售，必填
        },
    ]
'
```

## 🔨 更新

每一次更新后，需执行 `nb orm upgrade`。

## 🎉 使用

### 指令表

在群聊或私聊发送“钓鱼帮助”查看本插件的帮助，或者使用[NoneBot-Plugin-PicMenu-Next](https://github.com/lgc-NB2Dev/nonebot-plugin-picmenu-next)等帮助插件查看。

### 管理员指令表

| 指令     | 范围 | 说明                                           |
|:--------:|:----:|:----------------------------------------------:|
| 钓鱼预测 | 所有 | 对钓鱼进行模拟，查看各鱼的概率与期望，便于填表 |
| 鱼池     | 所有 | 查看数据库里面的所有特殊鱼                     |

### 赛博放生

当用户使用货币放生由自己取名的一条鱼后，每个用户在钓鱼时都有机会钓到那一条鱼。但此功能开关 `special_fish_enabled` 默认关闭，原因是用户生成内容如果不符合规范，可能导致出现不可预料的情况，请谨慎开启。

## 📝 Todo

- [x] 重写数据库逻辑（改为使用 [nonebot/plugin-orm](https://github.com/nonebot/plugin-orm)）
- [x] 增加系统商店，卖出钓到的鱼
- [x] 赛博放生 [#4](https://github.com/C14H22O/nonebot-plugin-fishing/issues/4) （已基本完成）
- [ ] ~~使用 [nonebot_plugin_chikari_economy](https://github.com/mrqx0195/nonebot_plugin_chikari_economy) 经济系统~~ 
- [x] 为鱼竿增加耐久度，耐久度为0时需重新购买鱼竿
- [x] 为钓鱼背包添加排序
- [x] 添加成就系统
- [x] 买装备！
- [ ] 支持卖与普通鱼同名的特殊鱼
- [ ] 管理员命令：捞鱼
- [ ] 屏蔽词库
