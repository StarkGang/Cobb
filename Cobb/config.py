from os import getenv
import dotenv

dotenv.load_dotenv('local.env')

class Config(object):
    BOT_TOKEN = getenv('BOT_TOKEN')
    API_ID = getenv('API_ID')
    API_HASH = getenv('API_HASH')
    COMMAND_HANDLER = list(set(getenv("CMD_HANDLER", "").split())) or ['!', '/']
    if '/' in COMMAND_HANDLER:
        COMMAND_HANDLER.append('/')
    MONGO_URL = getenv('MONGO_URL')
    LOG_CHAT = getenv('LOG_CHAT')
    ERROR_REPORT = "<b><u>An error occurred while executing the command!</b></u> \n\n<b>Command :</b> <code>{}</code> \n<b>Error :</b> <code>{}</code> \n<b>File Name :</b> <code>{}</code>"
    TG_MSG_LIMIT = 4095
    MAIN_BOT_USERNAME = getenv('MBU')
    TROLL_STICKER = getenv('TROLL_STICKER', 'CAACAgQAAxkBAAIgqWKY2Od6XJfA_xWnjJ6mH0IiBRwfAALSAANx5LgK4uT_Ygh4tAweBA')
    ASLC = getenv('ASLC')
    MESSAGES = 6
    SECONDS_WAIT = 5
