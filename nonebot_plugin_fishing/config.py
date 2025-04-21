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
            "name": "小鱼",
            "frequency": 2,
            "weight": 100,
            "price": 10
        },
        {
            "name": "尚方宝剑",
            "frequency": 2,
            "weight": 50,
            "price": 20
        },
        {
            "name": "小杂鱼~♡",
            "frequency": 10,
            "weight": 10,
            "price": 100
        },
        {
            "name": "烤激光鱼",
            "frequency": 20,
            "weight": 1,
            "price": 1000
        },
        {
            "name": "大傻",
            "frequency": 30,
            "weight": 1,
            "price": 2000
        }
    ]

    fishing_limit: int = 30

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
        }
    ]


try:
    # pydantic v2
    config = get_plugin_config(Config)
except:
    # pydantic v1
    config = Config.parse_obj(get_driver().config)