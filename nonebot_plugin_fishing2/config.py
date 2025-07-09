from pydantic import BaseModel
from typing import List, Dict

try:
    # pydantic v2
    from nonebot import get_plugin_config
except ImportError:
    # pydantic v1
    from nonebot import get_driver


class Config(BaseModel):
    fishes: List[Dict] = [
        {
            "type": "fish",
            "name": "小鱼",
            "price": 10,
            "props": [
                {
                    "type": "rm_fish",
                    "key": "小鱼"
                }
            ],
            "description": "一条小鱼。把它当做鱼饵可以防止钓到小鱼。",
            "can_catch": True,
            "frequency": 2,
            "weight": 1000,
            "can_buy": True,
            "amount": 1,
            "can_sell": True
        },
        {
            "type": "item",
            "name": "尚方宝剑",
            "price": 20,
            "props": [],
            "description": "假的。",
            "can_catch": True,
            "frequency": 2,
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
            "frequency": 10,
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
            "frequency": 20,
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
            "frequency": 60,
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
            "frequency": 30,
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
            "frequency": 120,
            "weight": 0,
            "can_buy": False,
            "can_sell": True
        },
        {
            "type": "item",
            "name": "钛金鱼竿",
            "price": 5,
            "props": [
                {
                    "type": "rare_fish",
                    "value": 10
                }    
            ],
            "description": "更坚韧的鱼竿，显著提升钓上大鱼的概率。",
            "can_catch": False,
            "can_buy": True,
            "amount": 30,
            "can_sell": False
        },
        {
            "type": "fish",
            "name": "大米",
            "price": 2000,
            "props": [
                {
                    "type": "fish",
                    "key": "大傻",
                    "value": 10000
                }    
            ],
            "description": "Fufu 最爱吃的大米！这是管理员物品。",
            "can_catch": False,
            "can_buy": False,
            "can_sell": False
        }
    ]

    punish_limit: int = 3 

    fishing_limit: int = 60

    fishing_coin_name: str = "绿宝石"  # It means Fishing Coin.

    special_fish_enabled: bool = True

    special_fish_price: int = 200

    special_fish_probability: float = 0.01

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
        }
    ]


try:
    # pydantic v2
    config = get_plugin_config(Config)
except:
    # pydantic v1
    config = Config.parse_obj(get_driver().config)