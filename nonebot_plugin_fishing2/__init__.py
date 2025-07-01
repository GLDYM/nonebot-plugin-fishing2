from nonebot import on_command, require

require("nonebot_plugin_orm")  # noqa

from nonebot import logger
from nonebot.plugin import PluginMetadata
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.matcher import Matcher

from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Message, MessageSegment, ActionFailed

import asyncio

from typing import Union

from .config import Config, config
from .data_source import (
    can_fishing,
    can_free_fish,
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
    remove_tools
)

fishing_coin_name = config.fishing_coin_name

__plugin_meta__ = PluginMetadata(
    name="赛博钓鱼",
    description="你甚至可以电子钓鱼",
    usage=f'''钓鱼帮助
▶ 查询 [物品]：
▶ 钓鱼 [鱼竿] [鱼饵]：
  ▷ 有 {config.fishing_limit}s 的冷却，时间随上一条鱼稀有度而增加
  ▷ 加参数可以使用鱼饵或鱼竿，同时只能使用一种 
  ▷ 频繁钓鱼会触怒河神
▶ 出售 <物品> <数量>：出售物品获得{fishing_coin_name}
▶ 购买 <鱼名> <数量>：【尚未实现】
▶ 放生 <鱼名>：给一条鱼取名并放生
▶ 祈愿：向神祈愿，随机获取/损失{fishing_coin_name}
▶ 背包：查看背包中的{fishing_coin_name}与物品
▶ 成就：查看拥有的成就
▶ 钓鱼排行榜：查看{fishing_coin_name}排行榜
''',
    type="application",
    homepage="https://github.com/FDCraft/nonebot-plugin-fishing2",
    config=Config,
    supported_adapters=None,
)



block_user_list = []
punish_user_dict = {}

fishing_help = on_command("fishing_help", aliases={"钓鱼帮助"}, priority=3,block=True)
fishing_lookup = on_command("fishing_lookup", aliases={"查看", "查询"}, priority=3,block=True)
fishing = on_command("fishing", aliases={"钓鱼"}, priority=5)
backpack = on_command("backpack", aliases={"背包", "钓鱼背包"}, priority=5)
buy = on_command("buy", aliases={"购买", "商店"}, priority=5)
sell = on_command("sell", aliases={"卖鱼", "出售", "售卖"}, priority=5)
free_fish_cmd = on_command("free_fish", aliases={"放生", "钓鱼放生"}, priority=5)
lottery_cmd = on_command("lottery", aliases={"祈愿"}, priority=5)
achievement_cmd = on_command("achievement", aliases={"成就", "钓鱼成就"}, priority=5)
give_cmd = on_command("give", aliases={"赐予"}, permission=SUPERUSER, priority=5)
board_cmd = on_command("board", aliases={"排行榜", "钓鱼排行榜"}, priority=5)


@fishing_help.handle()
async def _():
    await fishing_help.finish(__plugin_meta__.usage)


async def punish(bot: Bot, event: Event, matcher: Matcher, user_id: int):
    global punish_user_dict
    
    if not await can_fishing(user_id):
        try:
            punish_user_dict[user_id] += 1
        except KeyError:
            punish_user_dict[user_id] = 1

        if punish_user_dict[user_id] < config.punish_limit - 1 :
            await matcher.finish(MessageSegment.at(user_id) + " " + "河累了，休息一下吧")
        elif punish_user_dict[user_id] == config.punish_limit - 1:
            await matcher.finish(MessageSegment.at(user_id) + " " + "河神快要不耐烦了")
        elif punish_user_dict[user_id] == config.punish_limit:
            groud_id = event.group_id if isinstance(event, GroupMessageEvent) else None
            try:
                await bot.set_group_ban(group_id=groud_id, user_id=user_id, duration=1800)
            except ActionFailed:
                pass
            await matcher.finish(MessageSegment.at(user_id) + " " + "河神生气了，降下了惩罚")
        else:
            await matcher.finish()


@fishing.handle()
async def _(bot:Bot, event: Event, matcher: Matcher, arg: Message = CommandArg()):
    user_id = event.get_user_id()
    if user_id in block_user_list:
        await fishing.finish()
    
    use_tools = False
    tools = arg.extract_plain_text().split()[:2]
    logger.debug(f"PLDEBUG0: {tools}")
    if tools and tools != [] and tools != [""]:
        use_tools = True
        check_result = await check_tools(user_id, tools)
        if check_result:
            await fishing.finish(MessageSegment.at(user_id) + " " + check_result)
    
    await punish(bot, event, matcher, user_id)
    block_user_list.append(user_id)
    try:
        if use_tools:
            await remove_tools(user_id, tools)
            await fishing.send(MessageSegment.at(user_id) + "\n你使用了" + "、".join(tools) + "\n正在钓鱼…")
            result = await get_fish(user_id, tools)
        else:
            await fishing.send(MessageSegment.at(user_id) + " 正在钓鱼…")
            result = await get_fish(user_id)
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


@backpack.handle()
async def _(event: Event):
    user_id = event.get_user_id()
    await backpack.finish(MessageSegment.at(user_id) + " \n" + await get_stats(user_id) + "\n" + await get_balance(user_id) + "\n" + await get_backpack(user_id))

@buy.handle()
async def _(event: Event, arg: Message = CommandArg()):
    fish_info = arg.extract_plain_text()
    user_id = event.get_user_id()
    if fish_info == "":
        await buy.finish(MessageSegment.at(user_id) + " " + "请输入要买入的鱼的名字和数量 (数量为1时可省略), 如 /购买 鱼竿 1")
    if len(fish_info.split()) == 1:
        await buy.finish(MessageSegment.at(user_id) + " " + await sell_fish(user_id, fish_info))
    else:
        fish_name, fish_quantity = fish_info.split()
        await buy.finish(MessageSegment.at(user_id) + " " + await sell_fish(user_id, fish_name, int(fish_quantity)))


@sell.handle()
async def _(event: Event, arg: Message = CommandArg()):
    fish_info = arg.extract_plain_text()
    user_id = event.get_user_id()
    if fish_info == "":
        await sell.finish(MessageSegment.at(user_id) + " " + "请输入要卖出的鱼的名字和数量 (数量为1时可省略), 如 /卖鱼 小鱼 1")
    if len(fish_info.split()) == 1:
        await sell.finish(MessageSegment.at(user_id) + " " + await sell_fish(user_id, fish_info))
    else:
        fish_name, fish_quantity = fish_info.split()
        await sell.finish(MessageSegment.at(user_id) + " " + await sell_fish(user_id, fish_name, int(fish_quantity)))


@free_fish_cmd.handle()
async def _(event: Event, arg: Message = CommandArg()):
    if not can_free_fish():
        await free_fish_cmd.finish("未开启此功能, 请联系机器人管理员")
    fish_name = arg.extract_plain_text()
    user_id = event.get_user_id()
    if fish_name == "":
        await free_fish_cmd.finish(MessageSegment.at(user_id) + " " + "请输入要放生的鱼的名字, 如 /放生 测试鱼")
    await free_fish_cmd.finish(MessageSegment.at(user_id) + " " + await free_fish(user_id, fish_name))


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
    await achievement_cmd.finish(MessageSegment.at(user_id) + " " + await get_achievements(user_id))


@give_cmd.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().split()
    if len(args) < 2 or len(args) > 3:
        await give_cmd.finish("请输入用户的 id 和鱼的名字和数量 (数量为1时可省略), 如 /give 114514 开发鱼 1")
    else:
        print(f"PLDEBUG1: {args}")
        quantity = int(args[2]) if len(args) == 3 else 1
        result = await give(args[0], args[1], quantity)
        achievements = await check_achievement(args[0])
        if achievements is not None:
            for achievement in achievements:
                await fishing.send(achievement) 
        await give_cmd.finish(result)


@board_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    top_users_list = await get_board()
    msg = '钓鱼富豪排行榜：'
    for index, user in enumerate(top_users_list):
        try:
            user_info = await bot.get_group_member_info(group_id=group_id, user_id=user[0])
            username = user_info['card'] if user_info['card'] is not None and user_info['card'] != '' else user_info['nickname']
        except ActionFailed:
            username = "[神秘富豪]"

        msg += f'\n{index + 1}. {username}: {user[1]} {fishing_coin_name}'
    
    await board_cmd.finish(msg)
            
            
    