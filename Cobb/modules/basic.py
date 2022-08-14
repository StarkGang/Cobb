import re
from Cobb import Cobb_bot
from Cobb.utils.strings import *
from pyrogram.types import Message, ReplyKeyboardRemove
from pyrogram import Client
from pyrogram.handlers import MessageHandler
from Cobb.config import *
from pyrogram import filters
from pykeyboard import ReplyKeyboard, ReplyButton

BOT_TOKEN_REGEX = r'^[0-9]{8,10}:[a-zA-Z0-9_-]{35}$'
bt_token_col = Cobb_bot.db.make_collection('EXTRA_CLIENTS')

def fetch_bot_token(string: str):
    for xy in string.split('\n'):
        if k := re.match(BOT_TOKEN_REGEX, xy):
            return k[0]
    for xx in string.split(' '):
        if k := re.match(BOT_TOKEN_REGEX, xx):
            return k[0]
    return None

@Cobb_bot.register_on_cmd(['start'])
async def start_cmd(c: Client, m: Message):
    keyboard = ReplyKeyboard(row_width=1)
    if c.myself.username == Cobb_bot.main_client.username:
        keyboard.add(
        ReplyButton('Policy'),
        ReplyButton('Help'),
        ReplyButton('Creator'),
        ReplyButton('Create Your Own Bot')
        )
    else:
        keyboard.add(
        ReplyButton('Policy'),
        ReplyButton('Help'),
        ReplyButton('Creator')
        )
    if m.chat.chat_type != 'private':
        keyboard = None
    ftext = f"\n<b>Powered By -</b> @{Cobb_bot.main_client.username}" if c.myself.username != Cobb_bot.main_client.username else ''
    await m.reply(f'Hello, I am {c.myself.first_name}! \nI can help you eliminate spam from your chat. Click on "Help" button below or use cmd - /help to know about my full potential and please do read our "Policy" by click the button below or use cmd /policy. Thank you and do visit our support chat for more information - @CobbSupport {ftext}', reply_markup=keyboard, quote=True)
    
@Cobb_bot.on_message(filters.text & ~filters.channel, 3)
async def everything(c: Client, m: Message):
    if m.text and m.text.lower().startswith(("/")) and "@" in m.text.lower():
        text, username = m.text.split("@", 1)
        if username == c.myself.username:
            m.text = text
    if m.text.lower() in ['creator', '/creator', '!creator']:
        await m.reply_sticker(sticker=Cobb_bot.config.TROLL_STICKER, quote=True)
    elif m.text.lower() in ['help', '/help', '!help']:
        await m.reply(help_msg, quote=True)
    elif m.text.lower() in ['policy', '/policy', '!policy']:
        await m.reply(policy, quote=True)
    elif m.text.lower() in ['create your own bot', '/connect', '!connect']:
        if c.myself.username.lower() != Cobb_bot.main_client.username.lower():
            return await m.reply('This action only can be performed by main bot only!')
        if await bt_token_col.find_one({'_id': m.from_user.id}):
            return await m.reply('You already have a bot connected. we only allow 1 bot / user with free subscription.')
        token = await m.from_user.ask('Alright forward me the message from bot father or send me an bot token.', reply_markup=ReplyKeyboardRemove())
        keyboard = ReplyKeyboard(row_width=1)
        if c.myself.username == Cobb_bot.main_client.username:
            keyboard.add(
        ReplyButton('Policy'),
        ReplyButton('Help'),
        ReplyButton('Creator'),
        ReplyButton('Create Your Own Bot')
        )
        else:
            keyboard.add(
        ReplyButton('Policy'),
        ReplyButton('Help'),
        ReplyButton('Creator'),
        )
        if not token.text:
            return await token.reply('Invalid Message Type. Try again.', reply_markup=keyboard)
        token_ = None
        token.text = token.text.strip()
        token_ = fetch_bot_token(token.text)
        if token_ is None:
            return await token.reply('Invalid Bot Token Provided. Try Again /connect.', reply_markup=keyboard)
        if await bt_token_col.find_one({'token': token_}):
            return await token.reply("Token already in use!")
        client = Client(f'{m.from_user.id}_bot', api_id=Cobb_bot.api_id, api_hash=Cobb_bot.api_hash, bot_token=token_)
        try:
            await client.start()
        except Exception:
            return await token.reply("Invalid Bot token supplied. Try again with /start", reply_markup=keyboard)
        await bt_token_col.insert_one({'_id': m.from_user.id, 'token': token_})
        client.myself = await client.get_me()
        for y in Cobb_bot.all_functions.keys():
            xx = Cobb_bot.all_functions[y]
            client.add_handler(MessageHandler(xx.get('func'), xx.get('filters')), xx.get('group'))
        await token.reply('Instance Connected Sucessfully! Please use /start in your bot!', reply_markup=keyboard)
