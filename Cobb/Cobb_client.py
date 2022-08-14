import contextlib
from pyromod import listen
import logging
from random import randint
from pyrogram.errors.exceptions.flood_420 import FloodWait, SlowmodeWait
import aiofiles
from pyrogram import Client, idle, filters
import traceback
from pathlib import Path
from glob import glob
import Cobb.monkey_patch_message_object
import sys
from pyrogram.handlers import MessageHandler
import importlib
from Cobb.config import Config
import asyncio
import os
import inspect
from pyrogram.errors.exceptions.bad_request_400 import *
from pyrogram.types import Message
from functools import wraps
from Cobb.database import MongoDB 
import multiprocessing
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from cachetools import TTLCache
from .utils.cache_dict import *
from threading import RLock

appeal_link = "https://t.me/{}?start=appeal_user_id"
report_link = "https://t.me/{}?start=report_user_id"

class CobbBot(Client):
    def __init__(self, *args, **kargs):
        self.api_id = Config.API_ID
        self.api_hash = Config.API_HASH
        self.bot_token = Config.BOT_TOKEN
        self.command_handler = Config.COMMAND_HANDLER
        self.config = Config
        self.main_client = None
        self.super_users = []
        self.all_cmds = []
        self.all_functions = {}
        self.THREAD_LOCK = RLock()
        self.ADMIN_CACHE = TTLCache(maxsize=2048, ttl=(60 * 60), timer=perf_counter)
        self.SELF_ADMIN_CACHE = TTLCache(maxsize=2048, ttl=(60 * 60), timer=perf_counter)
        self.mongo_url = Config.MONGO_URL
        self.executor = ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() * 5)
        self.myself = None
        self._init_logger()
        self.ext_bot_clients = []
        self.config_checkup()
        
    async def get_alt_client(self):
        col = self.db.make_collection('EXTRA_CLIENTS')
        count = 0
        async for x in col.find({}):
            if x.get('token'):
                count += 1
                try:
                    client = Client(f"{x.get('_id')}_bot", api_id=self.api_id, api_hash=self.api_hash, bot_token=x.get('token'))
                    await client.start()
                except Exception as e:
                    with contextlib.suppress(Exception):
                        await self.send_message(int(x.get('_id')), f'Failed to start your own instance! \n<b>Error :</b> <code>{e}</code> \nYour token has been removed from our database! You may connect again if you want.')
                    await col.delete_one({'_id': x.get('_id')})
                else:
                    client.myself = await client.get_me()
                    self.ext_bot_clients.append(client)
        logging.info(f'Installed {count} Clients.')
            
    async def load_cache(self):
        col_2 = self.db.make_collection('AEC')
        col = self.db.make_collection('ANTISPAM_COLLECTION')
        col_3 = self.db.make_collection('ACC')
        sil_chats = await col.find_one(dict(_id='SILENT_CHATS'))
        AEC_CHATS = await col_2.find_one(dict(_id='CHAT_LIST'))
        if sil_chats and sil_chats.get('chats'):
            SILENT_MODE_CHATS.extend(sil_chats.get('chats'))
            self.log('Cached Silent Chats List')
        async for x in col_3.find({}):
            if x.get('chat_id') and x.get('action'):
                ACTION_CHATS[x['chat_id']] = dict(action=x['action'], duration=int(x['duration']))
        self.log('Cached Actions.')
        if AEC_CHATS and AEC_CHATS.get('chats'):
            Anti_Throttle_CHAT_LIST.extend(AEC_CHATS.get('chats'))
            self.log('Cached Anti Flood Chats.')
        self.log('All Data Cached into memory!')
    
    async def load_sudo_users(self):
        susers = self.db.make_collection('SUDO_USERS')
        super_user_z = (await susers.find_one({'_id': 'SUPER_USERS'}))
        if super_user_z:
            self.super_users.extend(super_user_z.get('user_ids'))
        logging.info('Loaded Super Users.')
        
    async def invoke(self, *args, **kwargs):
        mmax_ = 5
        max_count = 0
        while True:
            try:
                return await self.send_req(*args, **kwargs)
            except (FloodWait, SlowmodeWait) as e:
                if max_count > mmax_:
                    raise e
                logging.info(f"[{e.__class__.__name__}]: sleeping for - {e.x + 3}s.")
                await asyncio.sleep(e.x + 3)
                max_count += 1
        
    @property
    def sudo_owner(self):
        list_ = [self.config.OWNER_ID]
        if self.config.SUDO_USERS:
            list_.extend(self.config.SUDO_USERS)
        return list_
        
    def config_checkup(self):
        if not self.api_id or not self.api_id.isdigit():
            self.log('API_ID is not integer!', logging.ERROR)
            exit()
        self.api_id = int(self.api_id)
        if not self.api_hash:
            self.log('API_HASH is not set!', logging.ERROR)
            exit()
        if not self.bot_token:
            self.log('BOT_TOKEN is not set!', logging.ERROR)
            exit()
        if not self.mongo_url:
            self.log('MONGO_URL is not set!', logging.ERROR)
            exit()
            
    @staticmethod
    def log(message: str = None, level=logging.INFO) -> None:
        logging.log(level, message or traceback.format_exc())
        return message or traceback.format_exc()
    
    def _init_logger(self) -> None:
        logging.getLogger("pyrogram").setLevel(logging.WARNING)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
        logging.basicConfig(
            level=logging.INFO,
            datefmt="[%d/%m/%Y %H:%M:%S]",
            format="%(asctime)s - [Cobb] >> %(levelname)s << %(message)s",
            handlers=[logging.FileHandler("Cobbbot.log"), logging.StreamHandler()],
        )
        self.log("Initialized Logger successfully!")
    
    def register_handler(self, func, cmd_list=None, _filters=None, group=0, no_ext_client=False):
        if not _filters:
            _filters = filters.command(cmd_list, prefixes=self.command_handler)
        _filters &= ~filters.me & ~filters.channel
        self.add_handler(MessageHandler(func, _filters), group)
        if not no_ext_client and self.ext_bot_clients:
            for x in self.ext_bot_clients:
                x.add_handler(MessageHandler(func, _filters), group)
        func_name = func.__name__
        while func_name in self.all_functions:
            func_name = f'{func_name}_{str(randint(1, 99))}'
        self.all_functions[func_name] = dict(func=func, filters=_filters, group=group)
        
    async def run_bot(self):
        super().__init__('Cobb_bot', api_id=self.api_id, api_hash=self.api_hash, bot_token=self.bot_token)
        logging.info('Starting Bot....')
        await self.start()        
        logging.info('Starting Database....')
        self.db = MongoDB(self.mongo_url)
        await self.db.ping()
        await self.load_sudo_users()
        await self.load_cache()
        await self.get_alt_client()
        logging.info('Bot Started! Starting to load plugins...')
        self.myself = await self.get_me()
        self.main_client = self.myself
        self.load_from_directory("./Cobb/modules/*.py")
        logging.info('All plugins loaded!')
        logging.info(f"Logined As : @{self.myself.username}")
        await idle()
    
    def load_from_directory(self, path: str, log=True):
        helper_scripts = glob(path)
        if not helper_scripts:
            return self.log(f"No plugins loaded from {path}", level=logging.INFO)
        for name in helper_scripts:
            with open(name) as a:
                path_ = Path(a.name)
                plugin_name = path_.stem.replace(".py", "")
                plugins_dir = Path(path.replace("*", plugin_name))
                import_path = path.replace("/", ".")[:-4] + plugin_name
                spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
                load = importlib.util.module_from_spec(spec)
                try:
                    spec.loader.exec_module(load)
                    sys.modules[import_path + plugin_name] = load
                    if log:
                        self.log(f"Plugin - Loaded {plugin_name}")
                except Exception as err:
                    self.log(f"Failed To Load : {plugin_name} ({err})", level=50)
                    self.log(traceback.format_exc())
                               
    def on_message(self, filters, group=1):
        def decor(func):
            async def wrapper(c: Client, message: Message): 
                if str(message.chat.type).lower().startswith("chattype."):
                    chat_type = str((str(message.chat.type).lower()).split("chattype.")[1])
                    message.chat.chat_type = chat_type
                await func(c, message)
            self.register_handler(wrapper, _filters=filters, group=group)                           
            return wrapper
        return decor
    
    def run_in_exc(self, func_):
        @wraps(func_)
        async def wrapper(*args, **kwargs):
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                self.executor, lambda: func_(*args, **kwargs)
            )
        return wrapper
    
    def register_on_cmd(
        self,
        cmd: list,
        pm_only: bool = False,
        requires_input=False,
        requires_reply=False,
        no_private=False,
        group=0,
        no_ext_client=False
    ):
        cmd = cmd if isinstance(cmd, list) else [cmd]
        previous_stack_frame = inspect.stack()[1]
        file_name = os.path.basename(previous_stack_frame.filename.replace(".py", ""))
        def decorator(func):
            async def wrapper(client, message: Message):
                if str(message.chat.type).lower().startswith("chattype."):
                    chat_type = str((str(message.chat.type).lower()).split("chattype.")[1])
                    message.chat.chat_type = chat_type
                input_ = message.input_str
                if requires_input and input_ in ["", " ", None]:
                    return await message.reply('Please enter a valid input!')
                if requires_reply and not message.reply_to_message:
                    return await message.reply('Please reply to a message!')
                if no_private and chat_type == 'private':
                    return await message.reply('This command is not available in private chats!')
                if pm_only and chat_type != "private":
                    return await message.reply('This command can only be used in a private chat!')
                try:
                    await func(client, message)
                except (
                        MessageNotModified,
                        MessageIdInvalid,
                        UserNotParticipant,
                        MessageEmpty,
                    ):
                        pass
                except ChatAdminRequired:
                        await message.reply("I don't have proper rights to perform this action!")
                except Exception as _be:
                    try:
                        await self.send_error(cmd, traceback.format_exc(), file_name=file_name, chat_id=message.chat.id)
                    except Exception as e:
                        logging.error(e)
                        raise _be from e
            self.register_handler(wrapper, cmd, group=group, no_ext_client=no_ext_client)
            return wrapper
        return decorator
    
    async def write_file(self, to_write, file_name: str):
        async with aiofiles.open(file_name + str(randint(1, 100)) + ".txt", "w") as f:
            await f.write(to_write)
        return file_name + str(randint(1, 100)) + ".txt"
    
    def digit_wrap(self, digit):
        try:
            return int(digit)
        except ValueError:
            return str(digit)
    
    async def send_error(self, cmd, error, file_name, chat_id):
        if not Config.LOG_CHAT:
            raise ValueError
        error_to_send = Config.ERROR_REPORT.format(cmd, error, file_name)
        if len(error_to_send) > int(Config.TG_MSG_LIMIT):
            file_path = await self.write_file(error_to_send, file_name)
            await self.send_document(self.digit_wrap(Config.LOG_CHAT), file_path, f'Error Raised in {chat_id}')
            return os.remove(file_path)
        return await self.send_message(self.digit_wrap(Config.LOG_CHAT), error_to_send)
