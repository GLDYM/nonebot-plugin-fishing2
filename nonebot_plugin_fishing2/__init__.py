from nonebot import require

require("nonebot_plugin_orm")  # noqa

import shlex
from typing import Union

from nonebot import on_command, logger
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg
from nonebot.matcher import Matcher

from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    PrivateMessageEvent,
    Message,
    MessageSegment,
    ActionFailed,
)

from .config import Config, config
from .data_source import (
    can_fishing,
    get_fish,
    get_stats,
    get_backpack,
    sell_fish,
    get_balance,
    free_fish,
    lottery,
    give,
    check_achievement,
    get_achievements,
    get_board,
    check_tools,
    remove_tools,
    get_shop,
    buy_fish,
    predict,
    get_all_special_fish,
)
from .fish_helper import fish_list, get_fish_by_name

fishing_coin_name = config.fishing_coin_name

__plugin_meta__ = PluginMetadata(
    name="更好的电子钓鱼",
    description="赛博钓鱼……但是加强版本",
    usage=f"""▶ 查询 [物品]：查询某个物品的信息
▶ 钓鱼 [鱼竿] [鱼饵]：
  ▷ 有 {config.fishing_limit}s 的冷却
  ▷ {config.no_fish_probability} 概率空军，{config.special_fish_probability} 概率掉到特殊鱼
  ▷ 加参数可以使用鱼饵或鱼竿，同类物品同时只能使用一种 
  ▷ 频繁钓鱼会触怒河神
▶ 出售 <物品> <数量>：出售物品获得{fishing_coin_name}
  ▷ 如果卖不出去，尝试用英文双引号框住鱼名
▶ 购买 <物品> <份数>：购买渔具店的物品
▶ 放生 <鱼名>：给一条鱼取名并放生
  ▷ 不要放生奇怪名字的鱼
▶ 商店：看看渔具店都有些啥
▶ 祈愿：向神祈愿，随机获取/损失{fishing_coin_name}
▶ 背包：查看背包中的{fishing_coin_name}与物品
▶ 成就：查看拥有的成就
▶ 钓鱼排行榜：查看{fishing_coin_name}排行榜
""",
    type="application",
    homepage="https://github.com/FDCraft/nonebot-plugin-fishing2",
    config=Config,
    supported_adapters={"~onebot.v11"},
    extra={"author": "Polaris_Light", "version": "0.0.4", "priority": 5},
)


block_user_list = []
punish_user_dict = {}

# fmt:off
fishing_help = on_command("fishing_help", aliases={"钓鱼帮助"}, force_whitespace=True, priority=3, block=True)
fishing_lookup = on_command("fishing_lookup",aliases={"查看", "查询"},force_whitespace=True,priority=3,block=True,)
fishing = on_command("fishing", aliases={"钓鱼"}, force_whitespace=True, priority=5)
backpack = on_command("backpack", aliases={"背包", "钓鱼背包"}, force_whitespace=True, priority=5)
shop = on_command("shop", aliases={"商店"}, force_whitespace=True, priority=5)
buy = on_command("buy", aliases={"购买"}, force_whitespace=True, priority=5)
sell = on_command("sell", aliases={"卖鱼", "出售", "售卖"}, force_whitespace=True, priority=5)
free_fish_cmd = on_command("free_fish", aliases={"放生", "钓鱼放生"}, force_whitespace=True, priority=5)
lottery_cmd = on_command("lottery", aliases={"祈愿"}, force_whitespace=True, priority=5)
achievement_cmd = on_command("achievement", aliases={"成就", "钓鱼成就"}, force_whitespace=True, priority=5)
give_cmd = on_command("give", aliases={"赐予"}, force_whitespace=True, priority=5)
board_cmd = on_command("board", aliases={"排行榜", "钓鱼排行榜"}, force_whitespace=True, priority=5)

# hidden cmd
predict_cmd = on_command("predict", aliases={"钓鱼预测"}, force_whitespace=True, priority=5)
pool_cmd = on_command("pool", aliases={"鱼池"}, force_whitespace=True, priority=5)
# fmt:on


@fishing_help.handle()
async def _():
    await fishing_help.finish(__plugin_meta__.usage)


@shop.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    messages = get_shop()
    await forward_send(bot, event, messages)
    return None


@fishing_lookup.handle()
async def _(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    arg: Message = CommandArg(),
):
    user_id = event.get_user_id()
    arg = arg.extract_plain_text()
    if not arg or arg == "":
        await fishing_lookup.finish(
            "请输入要查询的物品\n可查询物品：" + "、".join(fish_list)
        )
    if arg == "空军":
        await fishing_lookup.finish(
            MessageSegment.at(user_id)
            + " 在钓鱼活动中，空军指钓鱼者一无所获，没有钓到任何鱼，空手而归。"
        )
    elif arg not in fish_list:
        await fishing_lookup.finish(MessageSegment.at(user_id) + " 查无此鱼。")
    await forward_send(bot, event, get_fish_by_name(arg).print_info())
    return None


@fishing.handle()
async def _(bot: Bot, event: Event, matcher: Matcher, arg: Message = CommandArg()):
    user_id = event.get_user_id()
    if user_id in block_user_list:
        await fishing.finish()

    tools = shlex.split((arg.extract_plain_text()))[:2]

    logger.debug(f"Fishing: {user_id} try to use {tools}")

    check_result = await check_tools(user_id, tools)
    if check_result:
        await fishing.finish(MessageSegment.at(user_id) + " " + check_result)

    await punish(bot, event, matcher, user_id)
    block_user_list.append(user_id)
    try:
        await remove_tools(user_id, tools)
        await fishing.send(
            MessageSegment.at(user_id) + f'\n你使用了{"、".join(tools)}\n'
            if tools != []
            else "" + "正在钓鱼…"
        )
        result = await get_fish(user_id, tools)
        achievements = await check_achievement(user_id)
        if achievements is not None:
            for achievement in achievements:
                await fishing.send(achievement)
    except Exception as e:
        logger.error(e)
    finally:
        block_user_list.remove(user_id)
        punish_user_dict.pop(user_id, None)
    await fishing.finish(MessageSegment.at(user_id) + " " + result)


@predict_cmd.handle()
async def _(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    arg: Message = CommandArg(),
):
    user_id = event.get_user_id()

    is_superuser = str(user_id) in bot.config.superusers
    is_self = event.self_id == user_id
    if not is_superuser and not is_self:
        return None

    tools = shlex.split(arg.extract_plain_text())[:2]

    tools = [x for x in tools if x != ""]

    check_result = await check_tools(user_id, tools, check_have=False)
    if check_result:
        await predict_cmd.finish(MessageSegment.at(user_id) + " " + check_result)
    result = predict(tools)
    await predict_cmd.finish(result)


@pool_cmd.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    user_id = event.get_user_id()
    is_superuser = str(user_id) in bot.config.superusers
    is_self = event.self_id == user_id
    if not is_superuser and not is_self:
        return None

    message: list[MessageSegment] = []
    pool = await get_all_special_fish()
    message.append(MessageSegment.text(f"现在鱼池里面有 {len(pool)} 条鱼。"))

    result = dict()
    for fish in pool:
        try:
            result[fish] += 1
        except KeyError:
            result[fish] = 1

    msg = "鱼池列表：\n"
    for fish, num in result.items():
        if len(msg) > 300:
            msg += f"{fish} x {num}"
            message.append(MessageSegment.text(msg))
            msg = ""
        else:
            msg += f"{fish} x {num}\n"
    else:
        message.append(MessageSegment.text(msg))

    await forward_send(bot, event, message)
    return None


@backpack.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    user_id = event.get_user_id()
    if not config.backpack_forward:
        await backpack.finish(
            MessageSegment.at(user_id)
            + " \n"
            + await get_stats(user_id)
            + "\n"
            + await get_balance(user_id)
            + "\n"
            + "\n\n".join(await get_backpack(user_id))
        )
    else:
        message: list[MessageSegment] = []
        message.append(MessageSegment.at(user_id))
        message.append(await get_stats(user_id))
        message.append(await get_balance(user_id))
        backpacks = await get_backpack(user_id)
        message += [MessageSegment.text(msg) for msg in backpacks]
        await forward_send(bot, event, message)


@buy.handle()
async def _(event: Event, arg: Message = CommandArg()):
    args = arg.extract_plain_text().split(" ")
    args = [x for x in args if x != ""]

    user_id = event.get_user_id()
    if args == []:
        await buy.finish(
            MessageSegment.at(user_id)
            + " "
            + "请输入要买入物品的名字和份数 (份数为1时可省略), 如 /购买 钛金鱼竿 1"
        )
    if len(args) == 1:
        fish_name = args[0]
        result = await buy_fish(user_id, fish_name)
    else:
        fish_name, fish_quantity = args[0], args[1]
        result = await buy_fish(user_id, fish_name, int(fish_quantity))
    achievements = await check_achievement(user_id)
    if achievements is not None:
        for achievement in achievements:
            await fishing.send(achievement)
    await buy.finish(MessageSegment.at(user_id) + " " + result)


@sell.handle()
async def _(event: Event, arg: Message = CommandArg()):
    args = shlex.split(arg.extract_plain_text())

    user_id = event.get_user_id()
    if args == []:
        await sell.finish(
            MessageSegment.at(user_id)
            + " "
            + "请输入要卖出的鱼的名字和数量 (数量为1时可省略), 如 /卖鱼 小鱼 1"
        )
    if len(args) == 1:
        fish_name = args[0]
        await sell.finish(
            MessageSegment.at(user_id) + " " + await sell_fish(user_id, fish_name)
        )
    else:
        fish_name, fish_quantity = args[0], args[1]
        result = await sell_fish(user_id, fish_name, int(fish_quantity))
        await sell.finish(MessageSegment.at(user_id) + " " + result)


@free_fish_cmd.handle()
async def _(bot: Bot, event: Event, arg: Message = CommandArg()):
    if not config.special_fish_enabled:
        await free_fish_cmd.finish("未开启此功能, 请联系机器人管理员")

    fish_name = arg.extract_plain_text()
    user_id = event.get_user_id()

    if '"' in fish_name:
        if isinstance(event, GroupMessageEvent):
            group_id = event.group_id
            await bot.set_group_ban(group_id=group_id, user_id=user_id, duration=1800)
        await free_fish_cmd.finish(
            MessageSegment.at(user_id) + " " + "你 TM 在放生什么？滚滚滚"
        )

    if fish_name == "":
        await free_fish_cmd.finish(
            MessageSegment.at(user_id) + " " + "请输入要放生的鱼的名字, 如 /放生 测试鱼"
        )
    await free_fish_cmd.finish(
        MessageSegment.at(user_id) + " " + await free_fish(user_id, fish_name)
    )


@lottery_cmd.handle()
async def _(bot: Bot, event: Event, matcher: Matcher):
    user_id = event.get_user_id()
    try:
        await punish(bot, event, matcher, user_id)
        result = await lottery(user_id)
    except:
        pass
    finally:
        punish_user_dict.pop(user_id, None)
    await lottery_cmd.finish(MessageSegment.at(user_id) + " " + result)


@achievement_cmd.handle()
async def _(event: Event):
    user_id = event.get_user_id()
    await achievement_cmd.finish(
        MessageSegment.at(user_id) + " " + await get_achievements(user_id)
    )


@give_cmd.handle()
async def _(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    arg: Message = CommandArg(),
):
    is_superuser = str(event.user_id) in bot.config.superusers
    is_self = event.self_id == event.user_id
    if not is_superuser and not is_self:
        return None

    target = await get_at(event)
    args = shlex.split(arg.extract_plain_text())
    if target:
        args.insert(0, target)
    if len(args) < 2 or len(args) > 3:
        await give_cmd.finish(
            "请输入用户的 id 和鱼的名字和数量 (数量为1时可省略), 如 /give 114514 开发鱼 1"
        )
    else:
        quantity = int(args[2]) if len(args) == 3 else 1
        result = await give(args[0], args[1], quantity)
        achievements = await check_achievement(args[0])
        if achievements is not None:
            for achievement in achievements:
                await fishing.send(achievement)
        await give_cmd.finish(result)


@board_cmd.handle()
async def _(bot: Bot, event: Union[GroupMessageEvent, PrivateMessageEvent]):
    top_users_list = await get_board()
    msg = "钓鱼富豪排行榜："
    for index, user in enumerate(top_users_list):
        try:
            if isinstance(event, GroupMessageEvent):
                group_id = event.group_id
                user_info = await bot.get_group_member_info(
                    group_id=group_id, user_id=user[0]
                )
                username = (
                    user_info["card"]
                    if user_info["card"] is not None and user_info["card"] != ""
                    else user_info["nickname"]
                )
            elif isinstance(event, PrivateMessageEvent):
                user_info = await bot.get_stranger_info(user_id=user[0])
                username = user_info["nickname"]
        except ActionFailed:
            username = "[神秘富豪]"

        msg += f"\n{index + 1}. {username}: {user[1]} {fishing_coin_name}"

    await board_cmd.finish(msg)


async def punish(bot: Bot, event: Event, matcher: Matcher, user_id: int):
    global punish_user_dict

    if not await can_fishing(user_id):
        try:
            punish_user_dict[user_id] += 1
        except KeyError:
            punish_user_dict[user_id] = 1

        if punish_user_dict[user_id] < config.punish_limit - 1:
            await matcher.finish(
                MessageSegment.at(user_id) + " " + "河累了，休息一下吧"
            )
        elif punish_user_dict[user_id] == config.punish_limit - 1:
            await matcher.finish(MessageSegment.at(user_id) + " " + "河神快要不耐烦了")
        elif punish_user_dict[user_id] == config.punish_limit:
            groud_id = event.group_id if isinstance(event, GroupMessageEvent) else None
            try:
                await bot.set_group_ban(
                    group_id=groud_id, user_id=user_id, duration=1800
                )
            except ActionFailed:
                pass
            await matcher.finish(
                MessageSegment.at(user_id) + " " + "河神生气了，降下了惩罚"
            )
        else:
            await matcher.finish()


async def forward_send(
    bot: Bot,
    event: Union[GroupMessageEvent, PrivateMessageEvent],
    messages: list[MessageSegment],
) -> None:
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(
            group_id=event.group_id,
            messages=[
                {
                    "type": "node",
                    "data": {
                        "name": "花花",
                        "uin": bot.self_id,
                        "content": msg,
                    },
                }
                for msg in messages
            ],
        )
    else:
        await bot.send_private_forward_msg(
            user_id=event.user_id,
            messages=[
                {
                    "type": "node",
                    "data": {
                        "name": "花花",
                        "uin": bot.self_id,
                        "content": msg,
                    },
                }
                for msg in messages
            ],
        )


async def get_at(event: Union[GroupMessageEvent, PrivateMessageEvent]) -> int:
    if isinstance(event, GroupMessageEvent):
        msg = event.get_message()
        for msg_seg in msg:
            if msg_seg.type == "at":
                return msg_seg.data["qq"]
    return None
