import asyncio
from pyrogram import Client, idle, filters
from pyrogram.types import Message, Dialog
from validators import url
from string_utils import prepare_for_classification


API_ID = 69
API_HASH = "your api hash"

userbot_client = Client('Cobb_ub', api_id=API_ID, api_hash=API_HASH)

hardware_mode = input('Switch to hardware mode? (y/n): \n')

def write_file(path, string):
    with open(path, "a+") as f:
        f.write(f"{string}\n")
        
def duplicate_lines(file):
    import hashlib
    output_file_path = f'{file}.copy'
    input_file_path = f'{file}'
    completed_lines_hash = set()
    with open(output_file_path, "w") as output_file:
        for line in open(input_file_path, "r").readlines():
            if line:
                hashValue = hashlib.md5(line.rstrip().encode('utf-8')).hexdigest()
                if hashValue not in completed_lines_hash:
                    output_file.write(line)
                completed_lines_hash.add(hashValue)

if hardware_mode == 'n':
    @userbot_client.on_message(filters.me & filters.command(['ham', 'spam'], '!'))
    async def load_(c: Client, m: Message):
        await m.edit('Running....')
        offset_ = m.reply_to_message.id if m.reply_to_message else 0
        txt = ""
        no = 0
        async for x in c.get_chat_history(m.chat.id, limit=0 if offset_ != 0 else 99, offset_id=offset_):
            no += 1
            if x.text:
                if url(x.text):
                    no -= 1
                    continue
                text = prepare_for_classification(x.text)
                text = text.replace("\n", " ")
                if text and text not in [' ', '']:
                    txt += f"\n{m.command[0]},{text},,,"
            if no == 400:
                break
        if txt != '':
            write_file('./dataset/classify_model.csv', txt)
        await m.delete()
        
    async def run_bot():
        await userbot_client.start()
        await idle()

else:
    
    async def run_bot():
        await userbot_client.start()
        print(await userbot_client.export_session_string())
        dict_ = {}
        len_ = 0
        print('Choose a chat from below to start scrapping messages :\n')
        async for x in userbot_client.get_dialogs():
            x : Dialog = x
            if x.chat:
                len_ += 1
                dict_[len_] = x.chat.id
                print(f"{len_} - {x.chat.title or x.chat.first_name}\n")
        option = int(input('Now choose an chat to scrap from :'))
        if option not in dict_:
            return print('Invalid Option selected.')
        option_chose = dict_[option]
        ham_or_spam = input('ham or spam :\n')
        txt = ''
        async for x in userbot_client.get_chat_history(option_chose, limit=1000):
            if x.text:
                if url(x.text):
                    continue
                text = prepare_for_classification(x.text)
                text = text.replace("\n", " ").strip()
                if text and text not in [' ', '']:
                    txt += f"\n{ham_or_spam},{text},,,"
        if txt != '':
            write_file('./dataset/classify_model.csv', txt)
        input_file = './dataset/classify_model.csv'
        duplicate_lines(input_file)
        print('Done..')
        

                
    
loop = asyncio.get_event_loop()
loop.run_until_complete(run_bot())
