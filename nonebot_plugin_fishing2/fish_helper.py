from typing import Literal, Optional, Union

from nonebot.adapters.onebot.v11 import MessageSegment

from .config import config


class Achievement:
    type: Literal["fishing_frequency", "fish_type"] = None
    name: str = None
    data: Union[str, int] = (None,)
    description: int = None

    def __init__(self, achievemrnt: dict):
        self.type = achievemrnt["type"]
        self.name = achievemrnt["name"]
        self.data = achievemrnt["data"]
        self.description = achievemrnt["description"]


class Property:
    type: Literal[
        "rare_fish", "normal_fish", "fish", "rm_fish", "special_fish", "no_fish"
    ] = None
    key: Optional[str] = None
    value: Optional[int] = None

    def __init__(self, property: dict):
        self.type = property["type"]
        self.key = property["key"] if property.get("key") else None
        self.value = property["value"] if property.get("value") else None

    # fmt:off
    def __str__(self) -> str:
        match self.type:
            case "normal_fish":
                result = f"普通鱼权重{'增加' if self.value > 0 else '减少'}{abs(self.value)}"
            case "rare_fish":
                result = f"稀有鱼权重{'增加' if self.value > 0 else '减少'}{abs(self.value)}"
            case "fish":
                result = f"{self.key}权重{'增加' if self.value > 0 else '减少'}{abs(self.value)}"
            case "rm_fish":
                result = f"不会钓到{self.key}\n"
            case "special_fish":
                result = f"特殊鱼概率{'增加' if self.value > 0 else '减少'}{abs(self.value)}"
            case "no_fish":
                result = f"空军概率{'增加' if self.value > 0 else '减少'}{abs(self.value)}"
            case _:
                pass
        return result
    # fmt:on


class Fish:
    type: Literal["fish", "item"] = "fish"
    name: str = ""
    price: int = 0
    props: list[Property] = []
    description: str = ""
    can_catch: bool = False
    sleep_time: Optional[int] = 0
    weight: Optional[int] = 0
    can_buy: bool = False
    buy_price: Optional[int] = 0
    amount: Optional[int] = 0
    can_sell: bool = False

    def __init__(self, fish_dict: dict):
        self.type = fish_dict["type"] if fish_dict.get("type") else "fish"
        self.name = fish_dict["name"]  # 鱼名字都不填，搁着虚空造鱼呢？
        self.price = fish_dict["price"] if fish_dict.get("price") else 15
        self.amount = fish_dict["amount"] if fish_dict.get("amount") else 1
        self.description = (
            fish_dict["description"]
            if fish_dict.get("description")
            else "没有人知道这条鱼的信息。"
        )
        self.can_catch = fish_dict["can_catch"]
        self.can_buy = fish_dict["can_buy"]
        self.can_sell = fish_dict["can_sell"]

        self.sleep_time = fish_dict["sleep_time"] if fish_dict.get("sleep_time") else 60
        self.weight = fish_dict["weight"] if fish_dict.get("weight") else 0

        self.buy_price = (
            fish_dict["buy_price"]
            if fish_dict.get("buy_price")
            else int(fish_dict["price"] * config.buy_rate)
        )

        self.props = []
        if fish_dict.get("props") and fish_dict["props"] != []:
            for property in fish_dict["props"]:
                self.props.append(Property(property))

    def print_info(self) -> list[MessageSegment]:
        message = []

        message1 = ""
        message1 += f"▶ 名称：{self.name}\n"
        message1 += f"▶ 基准价格：{self.price} {fishing_coin_name}\n"
        message1 += f"▶ 单份数量：{self.amount}\n"
        message1 += f"▶ 描述：{self.description}\n"
        message1 += f'▶ {"可钓鱼获取" if self.can_catch else "不可钓鱼获取"}，'
        message1 += f'{"可购买" if self.can_buy else "不可购买"}，'
        message1 += f'{"可出售" if self.can_sell else "不可出售"}'
        message.append(MessageSegment.text(message1))
        if self.can_catch:
            message2 = ""
            message2 += f"▶ 钓鱼信息：\n"
            message2 += f"  ▷ 基础权重：{self.weight}，"
            message2 += f"上钩时间：{self.sleep_time}s"
            message.append(MessageSegment.text(message2))
        if self.can_buy:
            message3 = ""
            message3 += f"▶ 商店信息：\n"
            message3 += f"  ▷ 购买价格：{self.buy_price}\n"
            message.append(MessageSegment.text(message3))
        if self.props != []:
            message4 = ""
            message4 += f"▶ 道具信息：\n"
            message4 += f'  ▷ 道具类型：{"鱼饵" if self.type == "fish" else "道具"}\n'
            message4 += self.print_props()
            message.append(MessageSegment.text(message4))
        return message

    def print_props(self) -> str:
        result = "  ▷ 道具效果：\n"
        for i in range(len(self.props)):
            prop = self.props[i]
            result += (
                f"    {i + 1}. {str(prop)}"
                if i == len(self.props) - 1
                else f"    {i + 1}. {str(prop)}\n"
            )
        return result


# Constants
fishing_coin_name = config.fishing_coin_name
config_fishes: list[Fish] = [Fish(fish_dict) for fish_dict in config.fishes]
config_achievements = [
    Achievement(achievement_dict) for achievement_dict in config.fishing_achievement
]

fish_list: list[str] = [fish.name for fish in config_fishes]
can_catch_fishes = {fish.name: fish.weight for fish in config_fishes if fish.can_catch}
can_buy_fishes = [fish.name for fish in config_fishes if fish.can_buy]
can_sell_fishes = [fish.name for fish in config_fishes if fish.can_sell]


def get_fish_by_name(fish_name: str) -> Fish | None:
    for fish in config_fishes:
        if fish.name == fish_name:
            return fish

    return None
