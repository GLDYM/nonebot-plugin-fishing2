import asyncio
import copy
import random
import time
import json

from collections.abc import Hashable
from sqlalchemy import select, update, delete
from sqlalchemy.sql.expression import func
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot_plugin_orm import get_session

from .config import config
from .model import FishingRecord, SpecialFishes
from .fish_helper import *


def get_key_by_index(
    dict: dict, index: int, default: Hashable | None = None
) -> Hashable | None:
    """Utils: get the key of OrderedDict by index.

    Args:
        dict (dict)
        index (int)
        default (Hashable | None, optional): default value. Defaults to None.

    Returns:
        Hashable | None: a key of dict.
    """
    key_list = list(dict.keys())
    return key_list[index] if index < len(key_list) else default


async def can_fishing(user_id: str) -> bool:
    time_now = int(time.time())
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        return True if not record else record.time < time_now


async def can_catch_special_fish(probability_add: int):
    session = get_session()
    async with session.begin():
        records = await session.execute(select(SpecialFishes))
        return (
            len(records.all()) != 0
            and random.random() <= config.special_fish_probability + probability_add
        )


async def check_tools(
    user_id: str, tools: list[str] = None, check_have: bool = True
) -> str | None:
    if not tools or tools == []:
        return None

    # 这是工具吗？
    for tool in tools:
        fish = get_fish_by_name(tool)
        if not fish:
            return f"你在用什么钓鱼……？{tool}？"

        props = fish.props
        if not props or props == []:
            return f"搞啥嘞！{tool}既不是工具也不是鱼饵！"

    # 如果有两个工具，是一个工具一个鱼饵吗？
    if len(tools) == 2:
        if get_fish_by_name(tools[0]).type == get_fish_by_name(tools[1]).type:
            return "你为啥要用两个类型一样的东西？"

    # 有吗？有吗？
    if check_have:
        session = get_session()
        async with session.begin():
            select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
            fishes_record = await session.scalar(select_user)
            if fishes_record:
                loads_fishes = json.loads(fishes_record.fishes)
                for tool in tools:
                    if tool not in loads_fishes:
                        return f"你哪来的{tool}？"

    return None


async def remove_tools(user_id: str, tools: list[str] = None) -> None:
    if not tools or tools == []:
        return None

    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            loads_fishes = json.loads(fishes_record.fishes)
            for tool_name in tools:
                loads_fishes[tool_name] -= 1
                if loads_fishes[tool_name] == 0:
                    del loads_fishes[tool_name]
            dump_fishes = json.dumps(loads_fishes)
            user_update = (
                update(FishingRecord)
                .where(FishingRecord.user_id == user_id)
                .values(fishes=dump_fishes)
            )
            await session.execute(user_update)
            await session.commit()
        else:
            pass
            # raise ValueError("？你的 Check 是怎么通过的？")


def get_adjusts_from_tools(tools: list = None) -> list:
    no_add = 0
    sp_add = 0
    adjusts: list[Property] = []

    if tools:
        for tool in tools:
            adjusts += get_fish_by_name(tool).props

    for adjust in adjusts:
        if adjust.type == "special_fish":
            sp_add += adjust.value
        if adjust.type == "no_fish":
            no_add += adjust.value

    return adjusts, no_add, sp_add


def adjusted(adjusts: list[Property] = None) -> tuple:
    adjusted_fishes = copy.deepcopy(can_catch_fishes)

    for adjust in adjusts:
        if adjust.key and adjust.key not in adjusted_fishes:
            continue
        match adjust.type:
            case "normal_fish":
                for key, weight in can_catch_fishes.items():
                    if weight >= config.rare_fish_weight and key in adjusted_fishes:
                        adjusted_fishes[key] += adjust.value
            case "rare_fish":
                for key, weight in can_catch_fishes.items():
                    if weight < config.rare_fish_weight and key in adjusted_fishes:
                        adjusted_fishes[key] += adjust.value
            case "fish":
                adjusted_fishes[adjust.key] += adjust.value
            case "rm_fish":
                adjusted_fishes.pop(adjust.key)
            case "special_fish" | "no_fish":
                pass
            case _:
                pass

    adjusted_fishes_list = list(adjusted_fishes.keys())
    adjusted_weights = list(adjusted_fishes.values())

    for i in range(len(adjusted_weights)):
        if adjusted_weights[i] < 0:
            adjusted_weights[i] = 0

    return adjusted_fishes_list, adjusted_weights


def choice(adjusts: list[Property] = None) -> str:
    adjusted_fishes_list, adjusted_weights = adjusted(adjusts)
    choices = random.choices(
        adjusted_fishes_list,
        weights=adjusted_weights,
    )
    return choices[0]


async def get_fish(user_id: int, tools: list = None) -> str:
    adjusts, no_add, sp_add = get_adjusts_from_tools(tools)

    if random.random() < config.no_fish_probability + no_add:
        await asyncio.sleep(random.randint(10, 20))
        return "QAQ你空军了，什么都没钓到"

    if await can_catch_special_fish(sp_add):
        special_fish_name = await random_get_a_special_fish()
        await asyncio.sleep(random.randint(10, 20))
        await save_special_fish(user_id, special_fish_name)
        result = f"你钓到了别人放生的 {special_fish_name}"
        return result

    fish = choice(adjusts)
    sleep_time = get_fish_by_name(fish).sleep_time
    result = f"钓到了一条{fish}, 你把它收进了背包里"
    await asyncio.sleep(sleep_time)
    await save_fish(user_id, fish)
    return result


def predict(tools: list = None) -> str:
    no = config.no_fish_probability
    sp = config.special_fish_probability
    sp_price = config.special_fish_price
    result = ""

    adjusts, no_add, sp_add = get_adjusts_from_tools(tools)
    sp_t = min(max(sp + sp_add, 0), 1)
    no_t = min(max(no + no_add, 0), 1)

    # 拉取矫正权重
    adjusted_fishes_list, adjusted_weights = adjusted(adjusts)

    adjusted_fishes_value = []
    for fish_name in adjusted_fishes_list:
        fish = get_fish_by_name(fish_name)
        adjusted_fishes_value.append(int(fish.price * fish.amount))

    # 归一化
    total_weight = sum(adjusted_weights)
    probabilities = [w / total_weight for w in adjusted_weights]
    expected_value = sum(v * p for v, p in zip(adjusted_fishes_value, probabilities))

    result += f"鱼列表：[{', '.join(adjusted_fishes_list)}]\n"
    result += f'''概率列表: [{', '.join([str(round(w * 100, 2)) + "%" for w in probabilities])}]\n'''
    result += f"特殊鱼概率：{round(sp_t * (1 - no_t), 6)}\n"
    result += f"空军概率：{round(no_t, 6)}\n"

    # 无特殊鱼
    expected_value = expected_value * (1 - no_t)
    result += f"无特殊鱼时期望为：{expected_value:.3f}\n"

    # 有特殊鱼
    expected_value = expected_value * (1 - sp_t) + sp_price * sp_t * (1 - no_t)
    result += f"有特殊鱼期望为：{expected_value:.3f}"

    return result


async def random_get_a_special_fish() -> str:
    session = get_session()
    async with session.begin():
        random_select = select(SpecialFishes).order_by(func.random())
        data = await session.scalar(random_select)
        return data.fish


async def check_achievement(user_id: str) -> str | None:
    session = get_session()
    async with session.begin():
        record = await session.scalar(
            select(FishingRecord).where(FishingRecord.user_id == user_id)
        )
        if not record:
            return None
        fishing_frequency = record.frequency
        user_fishes = json.loads(record.fishes)
        achievements = config_achievements
        result_list = []
        for achievement in achievements:
            achievement_name = achievement.name
            if await is_exists_achievement(user_id, achievement_name):
                continue
            if (
                achievement.type == "fishing_frequency"
                and achievement.data <= fishing_frequency
            ) or (achievement.type == "fish_type" and achievement.data in user_fishes):
                await save_achievement(user_id, achievement_name)
                result_list.append(
                    f"""达成成就: {achievement_name}\n{achievement.description}"""
                )
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
            user_update = (
                update(FishingRecord)
                .where(FishingRecord.user_id == user_id)
                .values(achievements=dump_achievements)
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
            achievements=dump_achievements,
        )
        session.add(new_record)
        await session.commit()


async def save_fish(user_id: str, fish_name: str) -> None:
    time_now = int(time.time())
    fishing_cooldown = random.randint(
        config.fishing_cooldown_time_min, config.fishing_cooldown_time_max
    )
    amount = get_fish_by_name(fish_name).amount
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        if record:
            loads_fishes = json.loads(record.fishes)
            try:
                loads_fishes[fish_name] += amount
            except KeyError:
                loads_fishes[fish_name] = amount
            dump_fishes = json.dumps(loads_fishes)
            new_frequency = record.frequency + 1
            user_update = (
                update(FishingRecord)
                .where(FishingRecord.user_id == user_id)
                .values(
                    time=time_now + fishing_cooldown,
                    frequency=new_frequency,
                    fishes=dump_fishes,
                )
            )
            await session.execute(user_update)
            await session.commit()
            return
        data = {fish_name: amount}
        dump_fishes = json.dumps(data)
        new_record = FishingRecord(
            user_id=user_id,
            time=time_now + fishing_cooldown,
            frequency=1,
            fishes=dump_fishes,
            special_fishes="{}",
            coin=0,
            achievements="[]",
        )
        session.add(new_record)
        await session.commit()


async def save_special_fish(user_id: str, fish_name: str) -> None:
    time_now = int(time.time())
    fishing_cooldown = random.randint(
        config.fishing_cooldown_time_min, config.fishing_cooldown_time_max
    )
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
            user_update = (
                update(FishingRecord)
                .where(FishingRecord.user_id == user_id)
                .values(
                    time=time_now + fishing_cooldown,
                    frequency=record.frequency + 1,
                    special_fishes=dump_fishes,
                )
            )
            await session.execute(user_update)
        else:
            data = {fish_name: 1}
            dump_fishes = json.dumps(data)
            new_record = FishingRecord(
                user_id=user_id,
                time=time_now + fishing_cooldown,
                frequency=1,
                fishes="{}",
                special_fishes=dump_fishes,
                coin=0,
                achievements=[],
            )
            session.add(new_record)
        select_fish = (
            select(SpecialFishes)
            .where(SpecialFishes.fish == fish_name)
            .order_by(SpecialFishes.id)
            .limit(1)
        )
        record = await session.scalar(select_fish)
        fish_id = record.id
        delete_fishes = delete(SpecialFishes).where(SpecialFishes.id == fish_id)
        await session.execute(delete_fishes)
        await session.commit()


async def sell_fish(
    user_id: str,
    name_or_index: str,
    quantity: int = 1,
    as_index: bool = False,
    as_special: bool = False,
) -> str:
    if quantity <= 0:
        return "你在卖什么 w(ﾟДﾟ)w"

    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record := fishes_record:
            loads_fishes = json.loads(fishes_record.fishes)
            loads_fishes = {
                key: loads_fishes[key] for key in fish_list if key in loads_fishes
            }

            spec_fishes = json.loads(fishes_record.special_fishes)
            spec_fishes = dict(sorted(spec_fishes.items()))

            if as_index:
                if not name_or_index.isdigit():
                    return "你完全不看帮助是吗 ￣へ￣"
                load_dict = loads_fishes if not as_special else spec_fishes
                fish_name = get_key_by_index(load_dict, int(name_or_index))
                if not fish_name:
                    return "查无此鱼"
            else:
                fish_name = name_or_index

            if (
                not as_special
                and fish_name in loads_fishes
                and loads_fishes[fish_name] > 0
            ):
                if fish_name not in can_sell_fishes:
                    return f"这个 {fish_name} 不可以卖哦~"
                if loads_fishes[fish_name] < quantity:
                    return f"你没有那么多 {fish_name}"
                fish_price = get_fish_by_name(fish_name).price
                loads_fishes[fish_name] -= quantity
                if loads_fishes[fish_name] == 0:
                    del loads_fishes[fish_name]
                dump_fishes = json.dumps(loads_fishes)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(
                        coin=fishes_record.coin + fish_price * quantity,
                        fishes=dump_fishes,
                    )
                )
                await session.execute(user_update)
                await session.commit()

                return (
                    f"你以 {fish_price} {fishing_coin_name} / 条的价格卖出了 {quantity} 条 {fish_name}, "
                    f"你获得了 {fish_price * quantity} {fishing_coin_name}"
                )
            elif fish_name in spec_fishes and spec_fishes[fish_name] > 0:
                fish_price = config.special_fish_price
                if spec_fishes[fish_name] < quantity:
                    return f"你没有那么多 {fish_name}"
                spec_fishes[fish_name] -= quantity
                if spec_fishes[fish_name] == 0:
                    del spec_fishes[fish_name]
                dump_fishes = json.dumps(spec_fishes)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(
                        coin=fishes_record.coin + fish_price * quantity,
                        special_fishes=dump_fishes,
                    )
                )
                await session.execute(user_update)
                await session.commit()
                return (
                    f"你以 {fish_price} {fishing_coin_name} / 条的价格卖出了 {quantity} 条 {fish_name}, "
                    f"获得了 {fish_price * quantity} {fishing_coin_name}"
                )
            else:
                return "查无此鱼"
        else:
            return "还没钓鱼就想卖鱼?"


async def buy_fish(user_id: str, fish_name: str, quantity: int = 1) -> str:
    if quantity <= 0:
        return "别在渔具店老板面前炫耀自己的鱼 (..-˘ ˘-.#)"
    if fish_name not in can_buy_fishes:
        return "商店不卖这个！"

    fish = get_fish_by_name(fish_name)
    total_price = int(fish.buy_price * fish.amount * quantity)

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
                loads_fishes[fish_name] += fish.amount * quantity
            except KeyError:
                loads_fishes[fish_name] = fish.amount * quantity
            dump_fishes = json.dumps(loads_fishes)
            user_update = (
                update(FishingRecord)
                .where(FishingRecord.user_id == user_id)
                .values(coin=user_coin, fishes=dump_fishes)
            )
            await session.execute(user_update)
            await session.commit()
            return f"你用 {total_price} {fishing_coin_name} 买入了 {quantity} 份 {fish_name}"
        else:
            return "不想钓鱼的人就别在渔具店逛了~"


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
                new_record = SpecialFishes(user_id=user_id, fish=fish_name)
                session.add(new_record)
                dump_fishes = json.dumps(spec_fishes)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(special_fishes=dump_fishes)
                )
                await session.execute(user_update)
                await session.commit()
                return f"你再次放生了 {fish_name}, 未来或许会被有缘人钓到呢"
            else:
                if fish_name in fish_list:
                    return "普通鱼不能放生哦~"

                if user_coin < config.special_fish_free_price:
                    special_fish_coin_less = str(
                        config.special_fish_free_price - fishes_record.coin
                    )
                    return f"你没有足够的 {fishing_coin_name}, 还需 {special_fish_coin_less} {fishing_coin_name}"
                user_coin -= config.special_fish_free_price
                new_record = SpecialFishes(user_id=user_id, fish=fish_name)
                session.add(new_record)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(coin=user_coin)
                )
                await session.execute(user_update)
                await session.commit()
                return f"你花费 {config.special_fish_free_price} {fishing_coin_name} 放生了 {fish_name}, 未来或许会被有缘人钓到呢"
        return "你甚至还没钓过鱼"


async def lottery(user_id: str) -> str:
    """算法来自于 https://github.com/fossifer/minesweeperbot/blob/master/cards.py"""
    session = get_session()
    time_now = int(time.time())
    fishing_cooldown = random.randint(
        config.fishing_cooldown_time_min, config.fishing_cooldown_time_max
    )
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            user_coin = fishes_record.coin
            if user_coin < 0:
                new_coin = random.randrange(1, 50)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(
                        time=time_now + fishing_cooldown,
                        coin=0 + new_coin,
                    )
                )
                await session.execute(user_update)
                await session.commit()
                return f"你是不是被哪个坏心眼的神惩罚了……河神帮你还完了欠款"
            if user_coin <= 30:
                new_coin = random.randrange(1, 50)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(
                        time=time_now + fishing_cooldown,
                        coin=fishes_record.coin + new_coin,
                    )
                )
                await session.execute(user_update)
                await session.commit()
                return f"你穷得连河神都看不下去了，给了你 {new_coin} {fishing_coin_name} w(ﾟДﾟ)w"
            new_coin = abs(user_coin) / 3
            new_coin = random.randrange(5000, 15000) / 10000 * new_coin
            new_coin = int(new_coin) if new_coin > 1 else 1
            new_coin *= random.randrange(-1, 2, 2)
            user_update = (
                update(FishingRecord)
                .where(FishingRecord.user_id == user_id)
                .values(
                    time=time_now + fishing_cooldown,
                    coin=fishes_record.coin + new_coin,
                )
            )
            await session.execute(user_update)
            await session.commit()
            return f'你{"获得" if new_coin >= 0 else "血亏"}了 {abs(new_coin)} {fishing_coin_name}'
        else:
            return "河神没有回应你……"


async def give(
    user_id: str,
    name_or_index: str,
    quantity: int = 1,
    as_index: bool = False,
    as_special: bool = False,
) -> str:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        if record:

            if name_or_index == "coin" or name_or_index == fishing_coin_name:
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(
                        coin=record.coin + quantity,
                    )
                )
                await session.execute(user_update)
                await session.commit()
                return f"使用滥权之力成功为 {user_id} {"增加" if quantity >= 0 else "减少"} {abs(quantity)} {fishing_coin_name} ヾ(≧▽≦*)o"

            loads_fishes = json.loads(record.fishes)
            spec_fishes = json.loads(record.special_fishes)

            if as_index:
                if not name_or_index.isdigit():
                    return "你完全不看帮助是吗 ￣へ￣"
                load_dict = loads_fishes if not as_special else spec_fishes
                fish_name = get_key_by_index(load_dict, int(name_or_index))
                if not fish_name:
                    return "查无此鱼，你再看看这人背包呢？"
            else:
                fish_name = name_or_index

            if not as_special and fish_name in fish_list:
                try:
                    loads_fishes[fish_name] += quantity
                except KeyError:
                    loads_fishes[fish_name] = quantity
                if loads_fishes[fish_name] <= 0:
                    del loads_fishes[fish_name]
                dump_fishes = json.dumps(loads_fishes)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(fishes=dump_fishes)
                )
                await session.execute(user_update)
                await session.commit()
            else:
                try:
                    spec_fishes[fish_name] += quantity
                except KeyError:
                    spec_fishes[fish_name] = quantity
                if spec_fishes[fish_name] <= 0:
                    del spec_fishes[fish_name]
                dump_fishes = json.dumps(spec_fishes)
                user_update = (
                    update(FishingRecord)
                    .where(FishingRecord.user_id == user_id)
                    .values(special_fishes=dump_fishes)
                )
                await session.execute(user_update)
                await session.commit()

            fish_name = (
                fish_name[:20] + "..." + str(len(fish_name) - 20)
                if len(fish_name) > 20
                else fish_name
            )
            return f"使用滥权之力成功为 {user_id} {"增加" if quantity >= 0 else "减少"} {abs(quantity)} 条 {fish_name} ヾ(≧▽≦*)o"
        return "未查找到用户信息, 无法执行滥权操作 w(ﾟДﾟ)w"


async def get_all_special_fish() -> dict[str, int]:
    session = get_session()
    async with session.begin():
        random_select = select(SpecialFishes.fish).order_by(SpecialFishes.fish.asc())
        data = await session.scalars(random_select)
        pool = data.all()

    result = dict()
    for fish in pool:
        try:
            result[fish] += 1
        except KeyError:
            result[fish] = 1

    return result


async def remove_special_fish(name_or_index: str, as_index: bool = False) -> str | None:
    pool = await get_all_special_fish()

    if as_index:
        if not name_or_index.isdigit():
            return "你完全不看帮助是吗 ￣へ￣"
        fish_name = get_key_by_index(pool, int(name_or_index))
        if not fish_name:
            return "查无此鱼"
    else:
        fish_name = name_or_index
        if fish_name not in pool:
            return "查无此鱼"

    session = get_session()
    async with session.begin():
        delete_fishes = delete(SpecialFishes).where(SpecialFishes.fish == fish_name)
        await session.execute(delete_fishes)
        await session.commit()

    fish_name = (
        fish_name[:20] + "..." + str(len(fish_name) - 20)
        if len(fish_name) > 20
        else fish_name
    )

    return f"已成功捞出 {fish_name}"


async def get_pool(name_limit: int = 30, page_limit: int = 200) -> list[MessageSegment]:
    messages: list[MessageSegment] = []
    pool = await get_all_special_fish()
    messages.append(
        MessageSegment.text(f"现在鱼池里面有 {sum(list(pool.values()))} 条鱼。")
    )

    msg = "鱼池列表：\n"
    i = 0
    j = 1
    for fish, num in pool.items():
        if len(msg) > page_limit:
            fish = (
                fish[:name_limit] + "..." + str(len(fish) - name_limit)
                if len(fish) > name_limit
                else fish
            )
            msg += f"{i}. {fish} x {num}\n"
            msg += f"【第 {j} 页结束】"
            messages.append(MessageSegment.text(msg))
            msg = ""
            i += 1
            j += 1
        else:
            fish = (
                fish[:name_limit] + "..." + str(len(fish) - name_limit)
                if len(fish) > name_limit
                else fish
            )
            msg += f"{i}. {fish} x {num}\n"
            i += 1
    else:
        messages.append(MessageSegment.text(msg))

    return messages


async def get_stats(user_id: str) -> str:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishing_record = await session.scalar(select_user)
        if fishing_record:
            return f"🐟你钓上了 {fishing_record.frequency} 条鱼"
        return "🐟你还没有钓过鱼，快去钓鱼吧"


async def get_balance(user_id: str) -> str:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            return f"🪙你有 {fishes_record.coin} {fishing_coin_name}"
        return "🪙你什么也没有 :)"


async def get_backpack(user_id: str, limit: int | None = None) -> list[str]:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        fishes_record = await session.scalar(select_user)
        if fishes_record:
            loads_fishes = json.loads(fishes_record.fishes)
            loads_fishes = {
                key: loads_fishes[key] for key in fish_list if key in loads_fishes
            }
            spec_fishes: dict = json.loads(fishes_record.special_fishes)
            if spec_fishes:
                spec_fishes = dict(sorted(spec_fishes.items()))
                if limit:
                    return print_backpack(loads_fishes, spec_fishes, limit)
                else:
                    return print_backpack(loads_fishes, spec_fishes)
            return (
                ["🎒你的背包里空无一物"]
                if loads_fishes == {}
                else print_backpack(loads_fishes)
            )
        return ["🎒你的背包里空无一物"]


def print_backpack(
    backpack: dict, special_backpack: dict = None, limit: int | None = None
) -> list[str]:
    i = 0
    result = []
    for fish_name, quantity in backpack.items():
        result.append(f"{i}. {fish_name}×{str(quantity)}")
        i += 1

    if special_backpack:
        i = 0
        special_result: list[str] = []
        for fish_name, quantity in special_backpack.items():
            if limit:
                special_result.append(
                    f"{i}. {fish_name[:limit] + '...' + str(len(fish_name) - limit) if len(fish_name) > limit else fish_name}×{str(quantity)}"
                )
            else:
                special_result.append(f"{i}. {fish_name}×{str(quantity)}")
            i += 1
        return [
            "🎒普通鱼:\n" + "\n".join(result),
            "🎒特殊鱼:\n" + "\n".join(special_result),
        ]
    return ["🎒普通鱼:\n" + "\n".join(result)]


async def get_achievements(user_id: str) -> str:
    session = get_session()
    async with session.begin():
        select_user = select(FishingRecord).where(FishingRecord.user_id == user_id)
        record = await session.scalar(select_user)
        if record:
            achievements = json.loads(record.achievements)
            return "已完成成就:\n" + "\n".join(achievements)
        return "你甚至还没钓过鱼 (╬▔皿▔)╯"


async def get_board() -> list[tuple]:
    session = get_session()
    async with session.begin():
        select_users = (
            select(FishingRecord).order_by(FishingRecord.coin.desc()).limit(10)
        )
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

    messages.append(MessageSegment.text("===== 钓鱼用具店 ====="))

    for fish in config_fishes:
        if fish.can_buy:
            total_price = int(fish.buy_price * fish.amount)
            messages.append(
                MessageSegment.text(
                    f"商品名：{fish.name} \n单份数量：{fish.amount}\n单价：{fish.buy_price} {fishing_coin_name}\n"
                    f"单份总价：{total_price} {fishing_coin_name}\n描述：{fish.description}"
                )
            )

    return messages
