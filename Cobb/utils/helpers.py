def humanbytes(size):
    """Convert Bytes To Bytes So That Human Can Read It"""
    if not size:
        return "0 B"
    power = 2 ** 10
    raised_to_pow = 0
    dict_power_n = {0: "", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size > power:
        size /= power
        raised_to_pow += 1
    return f"{str(round(size, 2))} {dict_power_n[raised_to_pow]}"