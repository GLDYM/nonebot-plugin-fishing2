import asyncio
import copy
import random
import time
import json

from typing import Union
from sqlalchemy import select, update, delete
from sqlalchemy.sql.expression import func
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot_plugin_orm import get_session

from .config import config
from .model import FishingRecord, SpecialFishes

fishing_coin_name = config.fishing_coin_name
fish_list = [fish["name"] for fish in config.fishes]
can_catch_fishes = {fish["name"]: fish["weight"] for fish in config.fishes if fish["can_catch"]}
can_buy_fishes = [fish["name"] for fish in config.fishes if fish["can_buy"]]
can_sell_fishes = [fish["name"] for fish in config.fishes if fish["can_sell"]]

def get_info(fish_name: str) -> list[MessageSegment]:
    message = []
    for fish in config.fishes:
        if fish.get("name") == fish_name:
            message1 = ""
            message1 += f'▶ 名称：{fish_name}\n'
            message1 += f'▶ 基准价格：{fish["price"]} {fishing_coin_name}\n'
            message1 += f'▶ 描述：{fish["description"]}\n'
            message1 += f'▶ {"可钓鱼获取" if fish["can_catch"] else "不可钓鱼获取"}，'
            message1 += f'{"可购买" if fish["can_buy"] else "不可购买"}，'
            message1 += f'{"可出售" if fish["can_sell"] else "不可出售"}'
            message.append(MessageSegment.text(message1))
            if fish["can_catch"]:
                message2 = ""
                message2 += f'▶ 钓鱼信息：\n'              
                message2 += f'  ▷ 基础权重：{fish["weight"]}，'
                message2 += f'上钩时间：{fish["frequency"]}s'
                message.append(MessageSegment.text(message2))
            if fish["can_buy"]:
                message3 = ""
                message3 += f'▶ 商店信息：\n'
                message3 += f'  ▷ 出售价格：{fish["price"] * 2}，'
                message3 += f'单份数量：{fish.get("amount") if fish.get("amount") else 1}'
                message.append(MessageSegment.text(message3))
            if fish.get("props") and fish["props"] != []:
                message4 = ""
                message4 += f'▶ 道具信息：\n'
                message4 += f'  ▷ 道具类型：{"鱼饵" if fish["type"] == "fish" else "道具"}\n'
                message4 += print_props(fish["props"])
                message.append(MessageSegment.text(message4))
            return message

def adjusted_choice(adjusts: list[dict[str, Union[str, int]]] = None) -> str:

    adjusted_fishes = copy.deepcopy(can_catch_fishes)
    
    if adjusts:
        for adjust in adjusts:
            if adjust.get("key") and adjust["key"] not in adjusted_fishes:
                continue
            match adjust["type"]:
                case "normal_fish":
                    for key, weight in can_catch_fishes.items():
                        if weight >= 500 and key in adjusted_fishes:
                            adjusted_fishes[key] += adjust["value"]
                case "rare_fish":
                    for key, weight in can_catch_fishes.items():
                        if weight < 500 and key in adjusted_fishes:
                            adjusted_fishes[key] += adjust["value"]
                case "fish":
                    adjusted_fishes[adjust["key"]] += adjust["value"]
                case "rm_fish":
                    adjusted_fishes.pop(adjust["key"])
                case "special_fish":
                    pass
                case _:
                    pass
    
    adjusted_fishes_list = list(adjusted_fishes.keys())
    adjusted_weights = list(adjusted_fishes.values())
    
    for i in range(len(adjusted_weights)):
        if adjusted_weights[i] < 0:
            adjusted_weights[i] = 0
    
    choices = random.choices(
        adjusted_fishes_list,
        weights=adjusted_weights,
    )
    return choices[0]


async def get_fish(user_id: int, tools: list = None) -> str:
    probability_add = 0
    adjusts: list[dict[str, Union[str, int]]] = []
    
    if tools:
        for tool in tools:
            adjusts += get_props(tool)

    for adjust in adjusts:
        if adjust["type"] == "special_fish":
            probability_add += adjust["value"]
            
    if await can_catch_special_fish(probability_add):
        special_fish_name = await random_get_a_special_fish()
        await save_special_fish(user_id, special_fish_name)
        result = f"你钓到了别人放生的 {special_fish_name}"
        return result
    fish = adjusted_choice(adjusts)
    sleep_time = get_frequency(fish)
    result = f"钓到了一条{fish}, 你把它收进了背包里"
    await asyncio.sleep(sleep_time)
    await save_fish(user_id, fish)
    return result


def get_type(fish_name: str) -> list:
    """获取鱼的类型"""
    config_fishes = config.fishes
    return next(
        (
            fish["type"]
            for fish in config_fishes
            if fish["name"] == fish_name
        ),
        "fish"
    )

def get_props(fish_name: str) -> list:
    """获取鱼的属性"""
    config_fishes = config.fishes
    return next(
        (
            fish["props"]
            for fish in config_fishes
            if fish["name"] == fish_name
        ),
        []
    )
def get_price(fish_name: str) -> int:
    """获取鱼的价格"""
    config_fishes = config.fishes
    return next(
        (
            fish["price"]
            for fish in config_fishes
            if fish["name"] == fish_name
        ),
        0
    )
    
def get_frequency(fish_name: str) -> int:
    """获取鱼的冷却"""
    config_fishes = config.fishes
    return next(
        (
            fish["frequency"]
            for fish in config_fishes
            if fish["name"] == fish_name
        ),
        60
    )

def print_props(props: list) -> str:
    """打印鱼的属性"""
    result = "  ▷ 道具效果：\n"
    for i in range(len(props)):
        prop = props[i]
        match prop["type"]:
            case "normal_fish":
                result += f"    {i + 1}. 普通鱼权重{'增加' if prop['value'] > 0 else '减少'}{prop['value']}\n"
            case "rare_fish":
                result += f"    {i + 1}. 稀有鱼权重{'增加' if prop['value'] > 0 else '减少'}{prop['value']}\n"
            case "fish":
                result += f"    {i + 1}. {prop['key']}权重{'增加' if prop['value'] > 0 else '减少'}{prop['value']}\n"
            case "rm_fish":
                result += f"    {i + 1}. 不会钓到{prop['key']}\n"
            case "special_fish":
                result += f"    {i + 1}. 特殊鱼概率{'增加' if prop['value'] > 0 else '减少'}{prop['value']}\n"
            case _:
                pass
    return result

async def random_get_a_special_fish() -> str:
    """随机返回一条别人放生的鱼"""
    session = get_session()
    async with session.begin():
        random_select = select(SpecialFishes).order_by(func.random())
        data = await session.scalar(random_select)
        return data.fish


async def can_fishing(user_id: str) -> bool:
    """判断是否可以钓鱼"""
    time_now = int(time.time())
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        return True if not record else record.time < time_now


def can_free_fish() -> bool:
    return config.special_fish_enabled


async def check_achievement(user_id: str) -> str | None:
    session = get_session()
    async with session.begin():
        record = await session.scalar(select(FishingRecord).where(FishingRecord.user_id == user_id))
        if not record:
            return None
        fishing_frequency = record.frequency
        user_fishes = json.loads(record.fishes)
        achievements = config.fishing_achievement
        result_list = []
        for achievement in achievements:
            achievement_name = achievement["name"]
            if await is_exists_achievement(user_id, achievement_name):
                continue
            if (achievement["type"] == "fishing_frequency" and achievement["data"] <= fishing_frequency) or \
                    (achievement["type"] == "fish_type" and achievement["data"] in user_fishes):
                await save_achievement(user_id, achievement_name)
                result_list.append(f"""达成成就: {achievement_name}\n{achievement["description"]}""")
        return result_list if result_list != [] else None


async def is_exists_achievement(user_id: str, achievement_name: str) -> bool:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        if record:
            loads_achievements = json.loads(record.achievements)
            return achievement_name in loads_achievements
        return False


async def save_achievement(user_id: str, achievement_name: str):
    time_now = int(time.time())
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        if record:
            loads_achievements = json.loads(record.achievements)
            loads_achievements.append(achievement_name)
            dump_achievements = json.dumps(loads_achievements)
            user_update = update(FishingRecord).where(
                FishingRecord.user_id == user_id
            ).values(
                achievements=dump_achievements
            )
            await session.execute(user_update)
            await session.commit()
            return
        data = []
        dump_achievements = json.dumps(data)
        new_record = FishingRecord(
            user_id=user_id,
            time=time_now,
            frequency=0,
            fishes="{}",
            special_fishes="{}",
            coin=0,
            achievements=dump_achievements
        )
        session.add(new_record)
        await session.commit()


async def save_fish(user_id: str, fish_name: str) -> None:
    """向数据库写入鱼以持久化保存"""
    time_now = int(time.time())
    fishing_limit = config.fishing_limit
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        if record:
            loads_fishes = json.loads(record.fishes)
            try:
                loads_fishes[fish_name] += 1
            except KeyError:
                loads_fishes[fish_name] = 1
            dump_fishes = json.dumps(loads_fishes)
            new_frequency = record.frequency + 1
            user_update = update(FishingRecord).where(
                FishingRecord.user_id == user_id
            ).values(
                time=time_now + fishing_limit,
                frequency=new_frequency,
                fishes=dump_fishes
            )
            await session.execute(user_update)
            await session.commit()
            return
        data = {
            fish_name: 1
        }
        dump_fishes = json.dumps(data)
        new_record = FishingRecord(
            user_id=user_id,
            time=time_now + fishing_limit,
            frequency=1,
            fishes=dump_fishes,
            special_fishes="{}",
            coin=0,
            achievements="[]"
        )
        session.add(new_record)
        await session.commit()


async def can_catch_special_fish(probability_add: int):
    session = get_session()
    async with session.begin():
        records = await session.execute(select(SpecialFishes))
        return len(records.all()) != 0 and random.random() <= config.special_fish_probability + probability_add


async def save_special_fish(user_id: str, fish_name: str) -> None:
    time_now = int(time.time())
    fishing_limit = config.fishing_limit
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        if record:
            loads_fishes = json.loads(record.special_fishes)
            try:
                loads_fishes[fish_name] += 1
            except KeyError:
                loads_fishes[fish_name] = 1
            dump_fishes = json.dumps(loads_fishes)
            user_update = update(FishingRecord).where(
                FishingRecord.user_id == user_id
            ).values(
                time=time_now + fishing_limit,
                frequency=record.frequency + 1,
                special_fishes=dump_fishes
            )
            await session.execute(user_update)
        else:
            data = {
                fish_name: 1
            }
            dump_fishes = json.dumps(data)
            new_record = FishingRecord(
                user_id=user_id,
                time=time_now + fishing_limit,
                frequency=1,
                fishes="{}",
                special_fishes=dump_fishes,
                coin=0,
                achievements=[]
            )
            session.add(new_record)
        select_fish = select(SpecialFishes).where(
            SpecialFishes.fish == fish_name
        ).order_by(SpecialFishes.id).limit(1)
        record = await session.scalar(select_fish)
        fish_id = record.id
        delete_fishes = delete(SpecialFishes).where(SpecialFishes.id == fish_id)
        await session.execute(delete_fishes)
        await session.commit()


async def get_stats(user_id: str) -> str:
    """获取钓鱼统计信息"""
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishing_record = await session.scalar(select_user)
        if fishing_record:
            return f"🐟你钓鱼了 {fishing_record.frequency} 次"
        return "🐟你还没有钓过鱼，快去钓鱼吧"


def print_backpack(backpack: dict, special_backpack=None) -> str:
    """输出背包内容"""
    result = [
        f"{fish_name}×{str(quantity)}"
        for fish_name, quantity in backpack.items()
    ]
    if special_backpack:
        special_result = [
            f"{fish_name}×{str(quantity)}"
            for fish_name, quantity in special_backpack.items()
        ]
        return "🎒背包:\n" + "\n".join(result) + "\n\n特殊鱼:\n" + "\n".join(special_result)
    return "🎒背包:\n" + "\n".join(result)


async def get_backpack(user_id: str) -> str:
    """从数据库查询背包内容"""
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            load_fishes = json.loads(fishes_record.fishes)
            sorted_fishes = {key: load_fishes[key] for key in fish_list if key in load_fishes}
            load_special_fishes = json.loads(fishes_record.special_fishes)
            if load_special_fishes:
                sorted_special_fishes = {key: load_special_fishes[key] for key in sorted(load_special_fishes)}
                return print_backpack(sorted_fishes, sorted_special_fishes)
            return "🎒你的背包里空无一物" if sorted_fishes == {} else print_backpack(sorted_fishes)
        return "🎒你的背包里空无一物"


async def sell_fish(user_id: str, fish_name: str, quantity: int = 1) -> str:
    """
    卖鱼

    参数：
      - user_id: 用户标识符
      - fish_name: 将要卖鱼的鱼名称
      - quantity: 卖出鱼的数量

    返回：
      - (str): 回复的文本
    """
    if quantity <= 0:
        return "你在卖什么 w(ﾟДﾟ)w"
    if fish_name not in can_sell_fishes:
        return f"这个 {fish_name} 不可以卖哦~"
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record := fishes_record:
            loads_fishes = json.loads(fishes_record.fishes)
            spec_fishes = json.loads(fishes_record.special_fishes)
            if fish_name in loads_fishes and loads_fishes[fish_name] > 0:
                fish_price = get_price(fish_name)
                if loads_fishes[fish_name] < quantity:
                    return f"你没有那么多 {fish_name}"
                loads_fishes[fish_name] -= quantity
                if loads_fishes[fish_name] == 0:
                    del loads_fishes[fish_name]
                dump_fishes = json.dumps(loads_fishes)
                user_update = update(FishingRecord).where(
                    FishingRecord.user_id == user_id
                ).values(
                    coin=fishes_record.coin + fish_price * quantity,
                    fishes=dump_fishes
                )
                await session.execute(user_update)
                await session.commit()
                return (f"你以 {fish_price} {fishing_coin_name} / 条的价格卖出了 {quantity} 条 {fish_name}, "
                        f"你获得了 {fish_price * quantity} {fishing_coin_name}")
            elif fish_name in spec_fishes and spec_fishes[fish_name] > 0:
                fish_price = config.special_fish_price
                if spec_fishes[fish_name] < quantity:
                    return f"你没有那么多 {fish_name}"
                spec_fishes[fish_name] -= quantity
                if spec_fishes[fish_name] == 0:
                    del spec_fishes[fish_name]
                dump_fishes = json.dumps(spec_fishes)
                user_update = update(FishingRecord).where(
                    FishingRecord.user_id == user_id
                ).values(
                    coin=fishes_record.coin + fish_price * quantity,
                    special_fishes=dump_fishes
                )
                await session.execute(user_update)
                await session.commit()
                return (f"你以 {fish_price} {fishing_coin_name} / 条的价格卖出了 {quantity} 条 {fish_name}, "
                        f"获得了 {fish_price * quantity} {fishing_coin_name}")
            else:         
                return "查无此鱼"
        else:
            return "还没钓鱼就想卖鱼?"
        

async def buy_fish(user_id: str, fish_name: str, quantity: int = 1) -> str:
    if quantity <= 0:
        return "别在渔具店老板面前炫耀自己的鱼 (..-˘ ˘-.#)"
    if fish_name not in can_buy_fishes:
        return "商店不卖这个！"
    
    for fish in config.fishes:
        if fish["name"] == fish_name:
            price = fish["price"] * 2
            amount = fish["amount"] if fish.get("amount") else 1
            total_price = price * amount * quantity
            break
    
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record := fishes_record:
            loads_fishes = json.loads(fishes_record.fishes)
            user_coin = fishes_record.coin
            if user_coin < total_price:
                coin_less = str(total_price - fishes_record.coin)
                return f"你没有足够的 {fishing_coin_name}, 还需 {coin_less} {fishing_coin_name}"
            user_coin -= total_price
            try:
                loads_fishes[fish_name] += amount * quantity
            except KeyError:
                loads_fishes[fish_name] = amount * quantity
            dump_fishes = json.dumps(loads_fishes)
            user_update = update(FishingRecord).where(
                FishingRecord.user_id == user_id
            ).values(
                coin=user_coin,
                fishes=dump_fishes
            )
            await session.execute(user_update)
            await session.commit()
            return (f"你用 {total_price} {fishing_coin_name} 买入了 {quantity * amount} {fish_name}")
        else:
            return "不想钓鱼的人就别在渔具店逛了~"


async def get_balance(user_id: str) -> str:
    """获取余额"""
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            return f"🪙你有 {fishes_record.coin} {fishing_coin_name}"
        return "🪙你什么也没有 :)"


async def free_fish(user_id: str, fish_name: str) -> str:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            user_coin = fishes_record.coin
            spec_fishes = json.loads(fishes_record.special_fishes)
            if fish_name in spec_fishes and spec_fishes[fish_name] > 0:
                spec_fishes[fish_name] -= 1
                if spec_fishes[fish_name] == 0:
                    del spec_fishes[fish_name]
                new_record = SpecialFishes(
                    user_id=user_id,
                    fish=fish_name
                )
                session.add(new_record)
                dump_fishes = json.dumps(spec_fishes)
                user_update = update(FishingRecord).where(
                    FishingRecord.user_id == user_id
                ).values(
                    special_fishes=dump_fishes
                )
                await session.execute(user_update)
                await session.commit()
                return f"你再次放生了 {fish_name}, 未来或许会被有缘人钓到呢"
            else:
                if fish_name in fish_list:
                    return "普通鱼不能放生哦~"
                
                if user_coin < config.special_fish_price // 2:
                    special_fish_coin_less = str(config.special_fish_price // 2 - fishes_record.coin)
                    return f"你没有足够的 {fishing_coin_name}, 还需 {special_fish_coin_less} {fishing_coin_name}"
                user_coin -= config.special_fish_price // 2
                new_record = SpecialFishes(
                    user_id=user_id,
                    fish=fish_name
                )
                session.add(new_record)
                user_update = update(FishingRecord).where(
                    FishingRecord.user_id == user_id
                ).values(
                    coin=user_coin
                )
                await session.execute(user_update)
                await session.commit()
                return f"你花费 {config.special_fish_price // 2} {fishing_coin_name} 放生了 {fish_name}, 未来或许会被有缘人钓到呢"
        return "你甚至还没钓过鱼"


async def lottery(user_id: str) -> str:
    """算法来自于 https://github.com/fossifer/minesweeperbot/blob/master/cards.py"""
    session = get_session()
    time_now = int(time.time())
    fishing_limit = config.fishing_limit
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            user_coin = fishes_record.coin
            if user_coin <= 30:
                new_coin = random.randrange(1, 50)
                user_update = update(FishingRecord).where(
                    FishingRecord.user_id == user_id
                ).values(
                    time=time_now + fishing_limit,
                    coin=fishes_record.coin + new_coin,
                )
                await session.execute(user_update)
                await session.commit()            
                return f"你穷得连河神都看不下去了，给了你 {new_coin} {fishing_coin_name} w(ﾟДﾟ)w"
            new_coin = abs(user_coin) / 3
            new_coin = random.randrange(5000, 15000) / 10000 * new_coin
            new_coin = int(new_coin) if new_coin > 1 else 1
            new_coin *= random.randrange(-1, 2, 2)
            user_update = update(FishingRecord).where(
                FishingRecord.user_id == user_id
            ).values(
                time=time_now + fishing_limit,
                coin=fishes_record.coin + new_coin,
            )
            await session.execute(user_update)
            await session.commit()
            return f'你{"获得" if new_coin >= 0 else "血亏"}了 {abs(new_coin)} {fishing_coin_name}'
        else:
            return "河神没有回应你……"


async def give(user_id: str, fish_name: str, quantity: int = 1) -> str:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        if record:
            if fish_name == 'coin' or fish_name == fishing_coin_name:
                user_update = update(FishingRecord).where(
                    FishingRecord.user_id == user_id
                ).values(
                    coin=record.coin + quantity,
                )
                await session.execute(user_update)
                await session.commit()
                return f"使用滥权之力成功为 {user_id} {"增加" if quantity >= 0 else "减少"} {abs(quantity)} {fishing_coin_name} ヾ(≧▽≦*)o"                
            loads_fishes = json.loads(record.fishes)
            spec_fishes = json.loads(record.special_fishes)
            if fish_name in fish_list:
                try:
                    loads_fishes[fish_name] += quantity
                except KeyError:
                    loads_fishes[fish_name] = quantity
                dump_fishes = json.dumps(loads_fishes)
                user_update = update(FishingRecord).where(
                    FishingRecord.user_id == user_id
                ).values(
                    fishes=dump_fishes
                )
                await session.execute(user_update)
                await session.commit()
            else:
                try:
                    spec_fishes[fish_name] += quantity
                except KeyError:
                    spec_fishes[fish_name] = quantity
                dump_fishes = json.dumps(spec_fishes)
                user_update = update(FishingRecord).where(
                    FishingRecord.user_id == user_id
                ).values(
                    special_fishes=dump_fishes
                )
                await session.execute(user_update)
                await session.commit()
            return f"使用滥权之力成功将 {fish_name} 添加到 {user_id} 的背包之中 ヾ(≧▽≦*)o"
        return "未查找到用户信息, 无法执行滥权操作 w(ﾟДﾟ)w"


async def get_achievements(user_id: str) -> str:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        if record:
            achievements = json.loads(record.achievements)
            return "已完成成就:\n" + "\n".join(achievements)
        return "你甚至还没钓过鱼 (╬▔皿▔)╯"

async def get_board() -> list:
    session = get_session()
    async with session.begin():
        select_users = select(FishingRecord).order_by(FishingRecord.coin.desc()).limit(10)
        record = await session.scalars(select_users)
        if record:
            top_users_list = []
            for user in record:
                top_users_list.append((user.user_id, user.coin))
            top_users_list.sort(key=lambda user: user[1], reverse=True)
            return top_users_list
        return []

def get_shop() -> list[MessageSegment]:
    messages: list[MessageSegment] = []
    
    messages.append(MessageSegment.text("===== 渔具店 ====="))
    
    for fish in config.fishes:
        if fish.get("can_buy"):
            name = fish["name"]
            price = fish["price"] * 2
            amount = fish["amount"] if fish.get("amount") else 1
            total_price = price * amount
            desc = fish["description"] if fish.get("description") else ""
            messages.append(MessageSegment.text(f"商品名：{name} \n单份数量：{amount}\n单价：{price} {fishing_coin_name}\n单份总价：{total_price} {fishing_coin_name}\n描述：{desc}"))
    
    return messages
    

async def check_tools(user_id: str, tools: list) -> str | None:
    # 这是工具吗？
    for tool in tools:
        props = get_props(tool)
        if not props or props == []:
            return f"搞啥嘞！{tool}既不是工具也不是鱼饵！"

    # 如果有两个工具，是一个工具一个鱼饵吗？
    if len(tools) == 2:
        if get_type(tools[0]) == get_type(tools[1]):
            return "你为啥要用两个类型一样的东西？"
        
    # 有吗？有吗？
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            loads_fishes = json.loads(fishes_record.fishes)
            for tool in tools: 
                if tool not in loads_fishes:
                    return f"你哪来的 {tool}？"
        
    return None

async def remove_tools(user_id: str, tools: list[str]) -> None:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            loads_fishes = json.loads(fishes_record.fishes)
            for tool in tools:
                loads_fishes[tool] -= 1
                if loads_fishes[tool] == 0:
                    del loads_fishes[tool]
            dump_fishes = json.dumps(loads_fishes)
            user_update = update(FishingRecord).where(
                FishingRecord.user_id == user_id
            ).values(
                fishes=dump_fishes
            )
            await session.execute(user_update)
            await session.commit()
        else:
            pass
            # raise ValueError("？你的 Check 是怎么通过的？")