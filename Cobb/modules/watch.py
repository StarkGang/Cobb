import asyncio
from datetime import datetime
import traceback
import logging
from Cobb import Cobb_bot
from pyrogram import filters, Client
import os
import platform
import psutil
from pyrogram.types import Message, ChatPermissions, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, User
from pyrogram.utils import zero_datetime
from Cobb.config import Config
from Cobb.utils.cache_dict import ACTION_CHATS, SILENT_MODE_CHATS
from Cobb.utils.decors import admin_check
from Cobb.utils.helpers import humanbytes
from Cobb.utils.predict import *
from Cobb.utils.string_utils import prepare_for_classification
from Cobb.utils.warn_db import get_warn, warn

def blue_text_scan(text: str):
    scan = text.split(" ")
    if len(scan) > 3:
        return True
    return False

collection = Cobb_bot.db.make_collection('ANTISPAM_COLLECTION')
collection2 = Cobb_bot.db.make_collection('ACC')

classify = SClassifier('./dataset/classify_model.csv')
classify.load_model()
classify.cv_and_train()
available_actions = ['ban', 'kick', 'mute', 'warn']

@Cobb_bot.register_on_cmd(['action'], no_private=True)
@admin_check(allow_if_no_input=True)
async def set_action_(c: Client, m: Message):
    if not m.input_str:
        if m.chat.id not in ACTION_CHATS:
            return m.reply('This chat has not actions enabled!')
        to_say = f"This chat has set action to {ACTION_CHATS[m.chat.id].get('action')} "
        if ACTION_CHATS[m.chat.id].get('duration'):
            limit_ = f"{ACTION_CHATS[m.chat.id].get('duration')}s"
            if ACTION_CHATS[m.chat.id].get('action') == 'warn':
                limit_ = f"{ACTION_CHATS[m.chat.id].get('duration')} times"
            to_say += f"with limit of {limit_}"
        return await m.reply(to_say)
    action_type = m.input_str
    duration = 0
    if " " in m.input_str:
        action_type, duration = m.input_str.split(" ", 1)
    if not duration.isdigit():
        return await m.reply("Invalid Type, Expected A Integer!")
    if int(duration) < 1:
        return await m.reply('Input should be larger than 1!')
    if action_type not in available_actions:
        return await m.reply("Invalid Operation selected, Try again!")
    prev_action = await collection2.find_one({'chat_id': m.chat.id})
    if prev_action and ((prev_action.get('action') != action_type) or (prev_action.get('duration') != duration)):
        await collection2.find_one_and_update({'chat_id': m.chat.id}, {"$set": {'action': action_type, "duration": int(duration)}})
    elif not prev_action:
        await collection2.insert_one({'chat_id': m.chat.id, 'action': action_type, 'duration': int(duration)})
    else:
        return await m.reply("Looks like you have already set to that action earlier!")
    ACTION_CHATS[m.chat.id] = dict(action=action_type, duration=int(duration))
    await m.reply(f'Alright, Action has been modified to {action_type}.')
    
@Cobb_bot.register_on_cmd(['silent'], no_private=True)
@admin_check(allow_if_no_input=True)
async def silent_mode(c: Client, m: Message):
    if not m.input_str:
        if m.chat.id in SILENT_MODE_CHATS:
            return await m.reply('This chat has already enabled SILENT MODE')
        return await m.reply('This chat has not enabled SILENT MODE')
    input_str = m.input_str
    if input_str in ['on', 'off']:
        data = await collection.find_one({'_id': 'SILENT_CHATS'})
        if input_str == 'off':
            if data and data.get('chats') and m.chat.id in data.get('chats'):
                await collection.find_one_and_update({'_id': 'SILENT_CHATS'}, {'$pull': {'chats': m.chat.id}})
            else:
                return await m.reply('This chat has not enabled silent mode. why should i bother to disable it?')
            if m.chat.id in SILENT_MODE_CHATS:
                SILENT_MODE_CHATS.remove(m.chat.id)
            await m.reply('Disabled silent mode for this chat!')
        else:
            if not data:
                await collection.insert_one({'_id': 'SILENT_CHATS', 'chats': [m.chat.id]})
            elif m.chat.id not in data.get('chats'):
                await collection.find_one_and_update({'_id': 'SILENT_CHATS'}, {'$push': {'chats': m.chat.id}})
            else:
                return await m.reply("Looks like this chat has already enabled silent mode!")
            if m.chat.id not in SILENT_MODE_CHATS:
                SILENT_MODE_CHATS.append(m.chat.id)
            await m.reply('Enabled Silent mode for this chat!')
            
            
async def send_log(c: Client, text: str, user_object: User, ham_per, spam_per, chat_id):
    if not Config.ASLC:
        return None
    chat_id = str(int((int(chat_id) + (chat_id + 100)))).split("-")[1]
    user_id = int((user_object.id + (user_object.id + 100)))
    to_send = Cobb_bot.digit_wrap(Config.ASLC)
    _text = f"""<b><u>SPAM LOG</b></u>
    
<b>User ID (NOT RAW) :</b> <code>{user_id}</code>
<b>Chat ID (NOW RAW) :</b> <code>{chat_id}</code>
<b>Spam Percentage :</b> <code>{spam_per}%</code>
<b>Ham Percentage :</b> <code>{ham_per}%</code>
"""
    final_text = f"{_text}\n\n======= CONTENT ========\n<code>{text}</code>" 
    if len(final_text) >= Config.TG_MSG_LIMIT:
        file_name = f"{chat_id}_{user_object.id}_spam_content.txt"
        with open(file_name) as f:
            f.write(text)
        sent = await c.send_document(to_send, file_name, caption=_text)
        if os.path.exists(file_name):
            os.remove(file_name)
    else:
        sent = await c.send_message(to_send, final_text)
    return sent.link
    
    
@Cobb_bot.register_on_cmd(['info'])
async def _info(c: Client, m: Message):
    splatform = platform.system()
    platform_release = platform.release()
    platform_version = platform.version()
    architecture = platform.machine()
    ram = humanbytes(round(psutil.virtual_memory().total))
    cpu_freq = psutil.cpu_freq().current
    if cpu_freq >= 1000:
        cpu_freq = f"{round(cpu_freq / 1000, 2)}GHz"
    else:
        cpu_freq = f"{round(cpu_freq, 2)}MHz"
    du = psutil.disk_usage(c.workdir)
    psutil.disk_io_counters()
    disk = f"{humanbytes(du.used)} / {humanbytes(du.total)} " f"({du.percent}%)"
    cpu_len = len(psutil.Process().cpu_affinity())
    await m.reply(f'''<b><u>Information</b></u>
        
<b>Dataset :</b> <code>ham_spam.dat</code>
<b>Accuracy :</b> <code>{str(round(classify.score, 2)).split("0.")[1]}%</code>
<b>Technology Used :</b> <code>Pandas, Pyrogram, Python, Sk-Learn</code>
<b>System :</b> <code>{splatform} {platform_version}</code>
<b>Release :</b> <code>{platform_release}</code>
<b>Architecture :</b> <code>{architecture}</code>
<b>Memory :</b> <code>({ram} | {cpu_len})</code>
<b>Frequency :</b> <code>{cpu_freq}</code>
<b>Disk Usage :</b> <code>{disk}</code>
''')
    
@Cobb_bot.on_message((filters.text | filters.caption) & ~filters.private, 5)
@admin_check(True, False, True)
async def scan_result(c: Client, m: Message):
    text_2_scan = await prepare_for_classification(m.caption or m.text)
    if not blue_text_scan(text_2_scan): # why should we scan cmds?
        spam_bool, ham_perc, spam_perc = await classify.predict(text_2_scan)
        if spam_bool: 
            await m.delete()
            try:
                link = await send_log(c, m.caption or m.text, m.from_user or m.sender_chat, ham_perc, spam_perc, m.chat.id)
            except Exception:
                logging.error(traceback.format_exc())
                link = None
            action_col = ACTION_CHATS[m.chat.id] if m.chat.id in ACTION_CHATS else None
            if not m.from_user and m.sender_chat:
                await m.chat.ban_member(m.sender_chat.id) # Ban send as channel
            elif action_col and action_col.get('action'):
                user = f"@{m.from_user.username}" if m.from_user.username else m.from_user.first_name
                if action_col.get('action') == 'ban':
                    await m.chat.ban_member(m.from_user.id, (datetime() + int(action_col.get('duration'))) if action_col.get('duration') != 0 else zero_datetime())
                elif action_col.get('action') == 'mute':
                    await m.chat.restrict_member(m.from_user.id, permissions=ChatPermissions(can_send_messages=False), until_date=(datetime() + int(action_col.get('duration'))) if action_col.get('duration') != 0 else zero_datetime())
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
                    max_warns = int(action_col.get('duration', 5))
                    if user_warns and user_warns >= max_warns:
                        x_bttn = InlineKeyboardMarkup([[InlineKeyboardButton('View Message', url=link)]]) if link else None
                        try:
                            await m.chat.ban_member(m.from_user.id)
                        except Exception as e:
                            await m.reply(f"<b>An exception was raised while banning user :</b> <code>{e}</code>")
                        else:
                            await m.reply(f"{user} got {user_warns}/{max_warns} warns! Banned.", reply_markup=x_bttn)
                        await warn(m.from_user.id, m.chat.id, clear=True)
                    else:
                        bttn = [InlineKeyboardButton('Unwarn', f'unwarn_{m.from_user.id}')]
                        if link:
                            bttn.append(InlineKeyboardButton('View Message', url=link))
                        await warn(m.from_user.id, m.chat.id)
                        await m.reply(f"{user} got {user_warns}/{max_warns} warns! Send {max_warns-user_warns} more spam and get banned!", reply_markup=InlineKeyboardMarkup([bttn]))
            if m.chat.id not in SILENT_MODE_CHATS and (not action_col or (action_col.get('action') != 'warn')):
                bttn = [[InlineKeyboardButton('View Message', url=link)]] if link else None
                await m.reply(f"<b>Spam Detected</b> \n<b>Spam Percentage :</b> <code>{spam_perc}%</code> \n<b>Ham Percentage :</b> <code>{ham_perc}%</code> \nAction has been performed as directed!", reply_markup=InlineKeyboardMarkup(bttn))
                

@Cobb_bot.on_callback_query(filters.regex('^unwarn_(.*)'))
@admin_check()
async def unwarn_(c: Client, m: CallbackQuery):
    chat_id = m.message.chat.id
    user_id = m.matches[0].group(1)
    await warn(user_id, chat_id, reverse=True)
    await m.message.edit(f'Admin {m.from_user.username or m.from_user.first_name} Removed The warn!')
