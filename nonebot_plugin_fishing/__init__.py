from nonebot import on_command, require

require("nonebot_plugin_orm")  # noqa

from nonebot.plugin import PluginMetadata
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Message, MessageSegment, ActionFailed

import asyncio

from typing import Union

from .config import Config, config
from .data_source import (
    choice,
    can_fishing,
    can_catch_special_fish,
    can_free_fish,
    get_stats,
    save_fish,
    save_special_fish,
    get_backpack,
    sell_fish,
    get_balance,
    free_fish,
    random_get_a_special_fish,
    lottery,
    give,
    check_achievement,
    get_achievements,
    get_board
)

fishing_coin_name = config.fishing_coin_name

__plugin_meta__ = PluginMetadata(
    name="赛博钓鱼",
    description="你甚至可以电子钓鱼",
    usage=f'''钓鱼帮助
▶ 钓鱼：有 {config.fishing_limit}s 的冷却，时间随上一条鱼稀有度变化
▶ 卖鱼 [鱼名] [数量]：卖鱼获得{fishing_coin_name}
▶ 放生 [鱼名]：给一条鱼取名并放生
▶ 祈愿：向神祈愿，随机获取/损失{fishing_coin_name}
▶ 背包：查看背包中的{fishing_coin_name}与物品
▶ 成就：查看拥有的成就
▶ 钓鱼排行榜：查看{fishing_coin_name}排行榜
''',
    type="application",
    homepage="https://github.com/ALittleBot/nonebot-plugin-fishing",
    config=Config,
    supported_adapters=None,
)

fishing_help = on_command("fishing_help", aliases={"钓鱼帮助"}, priority=3,block=True)
fishing = on_command("fishing", aliases={"钓鱼"}, priority=5)
backpack = on_command("backpack", aliases={"背包", "钓鱼背包"}, priority=5)
sell = on_command("sell", aliases={"卖鱼", "出售"}, priority=5)
free_fish_cmd = on_command("free_fish", aliases={"放生", "钓鱼放生"}, priority=5)
lottery_cmd = on_command("lottery", aliases={"祈愿"}, priority=5)
achievement_cmd = on_command("achievement", aliases={"成就", "钓鱼成就"}, priority=5)
give_cmd = on_command("give", aliases={"赐予"}, permission=SUPERUSER, priority=5)
board_cmd = on_command("board", aliases={"排行榜", "钓鱼排行榜"}, priority=5)


@fishing_help.handle()
async def _():
    await fishing_help.finish(__plugin_meta__.usage)

@fishing.handle()
async def _(event: Event):
    user_id = event.get_user_id()
    if not await can_fishing(user_id):
        await fishing.finish("河累了, 休息一下吧")
    await fishing.send("正在钓鱼…")
    if await can_catch_special_fish():
        special_fish_name = await random_get_a_special_fish()
        result = f"你钓到了别人放生的 {special_fish_name}"
        await save_special_fish(user_id, special_fish_name)
        await fishing.finish(result)
    choice_result = choice()
    fish = choice_result[0]
    sleep_time = choice_result[1]
    result = f"钓到了一条{fish}, 你把它收进了背包里"
    await save_fish(user_id, fish)
    await asyncio.sleep(sleep_time)
    achievements = await check_achievement(user_id)
    if achievements is not None:
        for achievement in achievements:
            await fishing.send(achievement)
    await fishing.finish(MessageSegment.at(user_id) + " " + result)


@backpack.handle()
async def _(event: Event):
    user_id = event.get_user_id()
    await backpack.finish(MessageSegment.at(user_id) + " \n" + await get_stats(user_id) + "\n" + await get_balance(user_id) + "\n" + await get_backpack(user_id))


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
async def _(event: Event):
    user_id = event.get_user_id()
    await lottery_cmd.finish(MessageSegment.at(user_id) + " " + await lottery(user_id))


@achievement_cmd.handle()
async def _(event: Event):
    user_id = event.get_user_id()
    await achievement_cmd.finish(MessageSegment.at(user_id) + " " + await get_achievements(user_id))


@give_cmd.handle()
async def _(arg: Message = CommandArg()):
    info = arg.extract_plain_text().split()
    if len(info) < 2 or len(info) > 3:
        await give_cmd.finish("请输入用户的 id 和鱼的名字和数量 (数量为1时可省略), 如 /give 114514 开发鱼 1")
    else:
        quantity = int(info[2]) if len(info) == 3 else 1
        await give_cmd.finish(await give(info[0], info[1], quantity))


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
            
            
    