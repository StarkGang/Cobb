def monkeypatch(obj):
    def wrapper(sub):
        for (func_name, func_) in sub.__dict__.items():
            if func_name[:2] != "__":
                setattr(obj, func_name, func_)
        return sub
    return wrapper