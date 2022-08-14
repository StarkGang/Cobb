from Cobb import Cobb_bot
import asyncio
from pyrogram import Client

if not hasattr(Client, "send_req"):
     setattr(Client, "send_req", Client.invoke)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Cobb_bot.run_bot())
