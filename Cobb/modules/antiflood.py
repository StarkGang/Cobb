from collections import defaultdict
from datetime import datetime
from Cobb import Cobb_bot
from pyrogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from Cobb.utils.cache_dict import Anti_Throttle_CHAT_LIST, ACTION_CHATS
from Cobb.utils.warn_db import *
from pyrogram.utils import zero_datetime
import asyncio
from pyrogram import Client, filters
from Cobb.config import Config
from Cobb.utils.decors import admin_check
from time import time

CHAT_FLOOD_LIST = defaultdict(list)

antithrottle_enabled_chats = Cobb_bot.db.make_collection('AEC')

@Cobb_bot.register_on_cmd(['antithrottle'], no_private=True)
@admin_check(allow_if_no_input=True)
async def Anti_Throttle(c: Client, m: Message):
    if not m.input_str:
        if m.chat.id in Anti_Throttle_CHAT_LIST:
            return await m.reply('This chat has already enabled Anti-throttle feature!')
        return await m.reply('This chat has not enabled Anti-throttle mode / feature!')
    elif m.input_str not in ['on', 'off']:
        return await m.reply('Invalid input use - on/off only!')
    data = await antithrottle_enabled_chats.find_one({'_id': 'CHAT_LIST'})
    if m.input_str == 'on':
        if data and data.get('chats') and m.chat.id in data.get('chats'):
            return await m.reply('This chat is already in my antithrottle database.')
        if not data:
            await antithrottle_enabled_chats.insert_one({'_id': 'CHAT_LIST', 'chats': [m.chat.id]})
        else:
            await antithrottle_enabled_chats.find_one_and_update({'_id': 'CHAT_LIST'}, {"$push": {'chats': m.chat.id}})
        if m.chat.id not in Anti_Throttle_CHAT_LIST:
            Anti_Throttle_CHAT_LIST.append(m.chat.id)
        return await m.reply('Chat Added to my antithrottle database!')
    else:
        if data and data.get('chats') and m.chat.id in data.get('chats'):
            await antithrottle_enabled_chats.find_one_and_update({'_id': 'CHAT_LIST'}, {'$pull': {'chats': m.chat.id}})
            return await m.reply('Chat removed from my antithrottle database!')
        if m.chat.id in Anti_Throttle_CHAT_LIST:
            Anti_Throttle_CHAT_LIST.remove(m.chat.id)
        return await m.reply('This chat is not even in my database!')
    
@Cobb_bot.on_message(filters.group, 4)
@admin_check(True, False, True)
async def antithrottlewait(c: Client, m: Message):
    if m.chat.id not in Anti_Throttle_CHAT_LIST:
        return
    CHAT_FLOOD_LIST[f"{m.chat.id}_{m.from_user.id if m.from_user else m.sender_chat.id}"].append(time())
    if len(list(filter(lambda x: time() - int(x) < Config.SECONDS_WAIT, CHAT_FLOOD_LIST[f"{m.chat.id}_{m.from_user.id if m.from_user else m.sender_chat.id}"]))) > Config.MESSAGES:
        CHAT_FLOOD_LIST[f"{m.chat.id}_{m.from_user.id if m.from_user else m.sender_chat.id}"] = list(filter(lambda x: time() - int(x) < Config.SECONDS_WAIT, CHAT_FLOOD_LIST[f"{m.chat.id}_{m.from_user.id if m.from_user else m.sender_chat.id}"]))
        action_col = ACTION_CHATS[m.chat.id] if m.chat.id in ACTION_CHATS else None
        if not m.from_user and m.sender_chat:
            await m.chat.ban_member(m.sender_chat.id)
        elif action_col and action_col.get('action'):
            user = f"@{m.from_user.username}" if m.from_user.username else m.from_user.first_name
            if action_col.get('action') == 'ban':
                await m.chat.ban_member(m.from_user.id, (datetime() + action_col.get('duration')) if action_col.get('duration') != 0 else zero_datetime())
            elif action_col.get('action') == 'mute':
                await m.chat.restrict_member(m.from_user.id, permissions=ChatPermissions(can_send_messages=False), until_date=(datetime() + action_col.get('duration')) if action_col.get('duration') != 0 else zero_datetime())
            elif action_col.get('action') == 'kick':
                await m.chat.ban_member(m.from_user.id)
                await asyncio.sleep(2)
                await m.chat.unban_member(m.from_user.id)
            elif action_col.get('action') == 'warn':
                user_warns = await get_warn(m.from_user.id, m.chat.id)
                if not user_warns or user_warns == 0:
                    user_warns = 1
                else:
                    user_warns += 1
                max_warns = action_col.get('duration', 5)
                if user_warns and user_warns >= int(max_warns):
                    try:
                        await m.chat.ban_member(m.from_user.id)
                    except Exception as e:
                        await m.reply(f"<b>An exception was raised while banning user :</b> <code>{e}</code>")
                    else:
                        await m.reply(f"User {user} has {user_warns}/{max_warns} warns! Banned.")
                    await warn(m.from_user.id, m.chat.id, clear=True)
                else:
                    bttn = [[InlineKeyboardButton('Unwarn', f'unwarn_{m.from_user.id}')]]
                    await warn(m.from_user.id, m.chat.id)
                    await m.reply(f"User {user} got {user_warns}/{max_warns} warns! Send {max_warns-user_warns} more spam and get banned!", reply_markup=InlineKeyboardMarkup(bttn))
        else:
            await m.chat.ban_member(m.from_user.id)
            j = await m.reply('User has been banned due to throttling!')
            await asyncio.sleep(10)
            return await j.delete()
        if action_col and action_col.get('action') != 'warn':
            j = await m.reply(f'Anti-Throttling Triggered! User has been {action_col.get("action")}ed!')
            await asyncio.sleep(10)
            await j.delete()