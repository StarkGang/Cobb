from Cobb import Cobb_bot

col_warned = Cobb_bot.db.make_collection("WARNS")

async def warn(user, chat, clear=False, reverse=False):
    warns = f'{str(user)}_{str(chat)}'
    if col_ := await col_warned.find_one({"_id": warns}):
        if reverse:
            if int(col_.get('warn')) >= 1:
                warn = 0 if clear else (int(col_.get('warn')) - 1)
        else:
            warn = 0 if clear else (int(col_.get('warn')) + 1)
        await col_warned.find_one_and_update({"_id": warns}, {"$set": {"warn": warn}})
    else:
        await col_warned.insert_one({"_id": warns, "warn": 1})

async def get_warn(user, chat):
    warns = f'{str(user)}_{str(chat)}'
    if col_ := await col_warned.find_one({"_id": warns}):
        return col_.get('warn')
    else:
        return 0
    
async def un_warn(user, chat):
    warns = f'{str(user)}_{str(chat)}'
    if col_ := await col_warned.find_one({"_id": warns}):
        warn = int(col_.get('warn')) - 1
        await col_warned.find_one_and_update({"_id": warns}, {"$set": {"warn": warn}})