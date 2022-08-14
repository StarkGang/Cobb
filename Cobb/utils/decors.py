from pyrogram.types import Message, ChatMember, CallbackQuery
from typing import Union
from pyrogram import Client
from Cobb import Cobb_bot

def admin_check(reverse=False, can_reply=True, allow_call_if_no_user=False, allow_if_no_input=True):
    def decor(func):
        async def wrapper(c: Client, m: Union[CallbackQuery, Message]):
            if not m.from_user or not m.from_user.id:
                return (await func(c, m)) if allow_call_if_no_user else None
            if isinstance(m, Message):
                if not m.input_str and allow_if_no_input:
                    return await func(c, m)
            reply = m.answer if isinstance(m, CallbackQuery) else m.reply
            if isinstance(m, CallbackQuery):
                m.chat = m.message.chat
            with Cobb_bot.THREAD_LOCK:
                if not Cobb_bot.ADMIN_CACHE.get(m.chat.id):
                    Cobb_bot.ADMIN_CACHE[m.chat.id] = {}
                if Cobb_bot.ADMIN_CACHE.get(m.chat.id) and Cobb_bot.ADMIN_CACHE.get(m.chat.id).get(m.from_user.id):
                    perm : ChatMember = Cobb_bot.ADMIN_CACHE[m.chat.id][m.from_user.id]
                else:
                    if isinstance(m, Message):
                        perm : ChatMember = await m.chat.get_member(m.from_user.id)
                    else:
                        chat_id = m.message.chat.id
                        perm = await c.get_chat_member(chat_id, m.from_user.id)
                    Cobb_bot.ADMIN_CACHE[m.chat.id][m.from_user.id] = perm
            if reverse and perm.status.name.lower() in ['administrator', 'owner']:
                if can_reply:
                    await reply("You are an admin and you can't perform this action")
                return
            elif not reverse and (perm.status.name.lower() not in ['administrator', 'owner']):
                if can_reply:
                    await reply("You are not an admin and you can't perform this action!")
                return
            await func(c, m)
        return wrapper
    return decor
    
