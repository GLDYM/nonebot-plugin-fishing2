from pydantic import BaseModel
from typing import List, Dict

from nonebot import get_plugin_config


# fmt:off
class Config(BaseModel):
    fishes: List[Dict] = [
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
        {
            "type": "item",
            "name": "尚方宝剑",
            "price": 20,
            "props": [],
            "description": "假的。",
            "can_catch": True,
            "sleep_time": 2,
            "weight": 500,
            "can_buy": False,
            "can_sell": True,
        },
        {
            "type": "fish",
            "name": "小杂鱼~♡",
            "price": 100,
            "props": [],
            "description": "杂鱼，杂鱼~",
            "can_catch": True,
            "sleep_time": 10,
            "weight": 100,
            "can_buy": False,
            "can_sell": True
        },
        {
            "type": "fish",
            "name": "烤激光鱼",
            "price": 1000,
            "props": [],
            "description": "河里为什么会有烤鱼？",
            "can_catch": True,
            "sleep_time": 20,
            "weight": 20,
            "can_buy": False,
            "can_sell": True
        },
        {
            "type": "fish",
            "name": "琪露诺",
            "price": 1000,
            "props": [],
            "description": "邪恶的冰之精灵，是个笨蛋。",
            "can_catch": True,
            "sleep_time": 60,
            "weight": 20,
            "can_buy": False,
            "can_sell": True
        },
        {
            "type": "fish",
            "name": "大傻",
            "price": 2000,
            "props": [],
            "description": "非常能吃大米。",
            "can_catch": True,
            "sleep_time": 30,
            "weight": 10,
            "can_buy": False,
            "can_sell": True
        },
        {
            "type": "fish",
            "name": "帕秋莉",
            "price": 8000,
            "props": [],
            "description": "Neet姬，非常难在图书馆外见到她。",
            "can_catch": True,
            "sleep_time": 120,
            "weight": 0,
            "can_buy": False,
            "can_sell": True
        },
        {
            "type": "item",
            "name": "钢制鱼竿",
            "price": 10,
            "amount": 30,
            "props": [
                {
                    "type": "rare_fish",
                    "value": 5
                },
                {
                    "type": "no_fish",
                    "value": 0.05
                }           
            ],
            "description": "升级的鱼竿，提升钓上大鱼的概率；但是因为偏重，容易空军。",
            "can_catch": False,
            "can_buy": True,
            "can_sell": False
        },
        {
            "type": "item",
            "name": "钛金鱼竿",
            "price": 40,
            "amount": 20,
            "props": [
                {
                    "type": "rare_fish",
                    "value": 10
                },
                {
                    "type": "no_fish",
                    "value": -0.05
                }           
            ],
            "description": "更坚韧的鱼竿，显著提升钓上大鱼的概率。",
            "can_catch": False,
            "can_buy": True,
            "buy_price": 40,
            "can_sell": False
        },
        {
            "type": "item",
            "name": "附魔鱼竿",
            "price": 20,
            "amount": 20,
            "props": [
                {
                    "type": "normal_fish",
                    "value": -250
                }      
            ],
            "description": "附魔的鱼竿，大幅减少钓上垃圾的概率。",
            "can_catch": True,
            "sleep_time": 30,
            "weight": 40,
            "can_buy": False,
            "can_sell": False
        },
        {
            "type": "fish",
            "name": "大米",
            "price": 700,
            "props": [
                {
                    "type": "fish",
                    "key": "大傻",
                    "value": 10000
                }    
            ],
            "description": "Fufu 最爱吃的大米！",
            "can_catch": False,
            "can_buy": True,
            "can_sell": False
        },
        {
            "type": "fish",
            "name": "棒棒糖",
            "price": 50,
            "props": [
                {
                    "type": "special_fish",
                    "value": 0.5
                },
                {
                    "type": "fish",
                    "key": "帕秋莉",
                    "value": 10
                }
            ],
            "description": "可以吸引到一些奇怪的鱼。",
            "can_catch": False,
            "can_buy": True,
            "can_sell": False
        },
        {
            "type": "fish",
            "name": "传奇棒棒糖",
            "price": 200,
            "props": [
                {
                    "type": "special_fish",
                    "value": 1
                },
                {
                    "type": "no_fish",
                    "value": -1
                }
            ],
            "description": "必定钓到特殊鱼。",
            "can_catch": False,
            "can_buy": False,
            "can_sell": False
        }
    ]
    
    fishing_achievement: List[Dict] = [
        {
            "type": "fishing_frequency",
            "name": "腥味十足的生意",
            "data": 1,
            "description": "钓到一条鱼。"
        },
        {
            "type": "fishing_frequency",
            "name": "还是钓鱼大佬",
            "data": 100,
            "description": "累计钓鱼一百次。"
        },
        {
            "type": "fish_type",
            "name": "那是鱼吗？",
            "data": "小杂鱼~♡",
            "description": "获得#####。[原文如此]"
        },
        {
            "type": "fish_type",
            "name": "那一晚, 激光鱼和便携式烤炉都喝醉了",
            "data": "烤激光鱼",
            "description": "获得烤激光鱼。"
        },
        {
            "type": "fish_type",
            "name": "你怎么把 Fufu 钓上来了",
            "data": "大傻",
            "description": "获得大傻"
        },
        {
            "type": "fish_type",
            "name": "⑨",
            "data": "琪露诺",
            "description": "发现了湖边的冰之精灵"
        },
        {
            "type": "fish_type",
            "name": "不动的大图书馆",
            "data": "帕秋莉",
            "description": "Neet 姬好不容易出门一次，就被你钓上来了？"
        },
        {
            "type": "fish_type",
            "name": "工欲善其事，必先利其器",
            "data": "钛金鱼竿",
            "description": "在钓鱼用具店购买钛金鱼竿"
        },
        {
            "type": "fish_type",
            "name": "为啥能钓上鱼竿？",
            "data": "附魔鱼竿",
            "description": "钓上附魔鱼竿"
        }
    ]

    fishing_coin_name: str = "绿宝石"  # 货币名称
    
    fishing_cooldown_time_min: int = 60 # 钓鱼冷却下限，单位为秒
    
    fishing_cooldown_time_max: int = 90 # 钓鱼冷却上限
    
    punish_limit: int = 3 # 短时间多次钓鱼后，禁言所需次数，防止刷屏

    special_fish_enabled: bool = False # 是否启用赛博放生 & 特殊鱼

    special_fish_price: int = 200 # 特殊鱼出售的价格

    special_fish_free_price: int = 100 # 特殊鱼放生的价格

    special_fish_probability: float = 0.01 # 钓上特殊鱼的概率，注意这个判定在空军判定之后

    no_fish_probability: float = 0.1 # 空军的概率
    
    rare_fish_weight: int = 500 # 稀有鱼权重分界线，影响 rare_fish 属性与 normal_fish 属性的区分
    
    buy_rate: float = 2.0 # 在不指定 buy_price 时，购买价格/基准价格比，应大于 1
    
    backpack_forward: bool = True # 背包是否使用聊天记录
# fmt:on

config = get_plugin_config(Config)

