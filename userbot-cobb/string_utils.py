from io import StringIO
from html.parser import HTMLParser
import re
from unidecode import unidecode
import unicodedata

class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()
        
    def handle_data(self, d):
        self.text.write(d)
        
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = HTMLStripper()
    s.feed(html)
    return s.get_data()


def rip_unicode(text):
    text = unicodedata.normalize('NFKD', text)
    text = unicodedata.normalize('NFKC', text)
    return text.encode('ascii', 'ignore').decode('utf-8')
    

def strip_emoji(string_):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  
                           u"\U0001F300-\U0001F5FF"  
                           u"\U0001F680-\U0001F6FF"  
                           u"\U0001F1E0-\U0001F1FF"  
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           u"\U0001f926-\U0001f937"
                           u"\U00010000-\U0010ffff"
                           u"\u2640-\u2642"
                           "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', string_)

import string


def remove_punc(s):
    table = str.maketrans(dict.fromkeys(string.punctuation))
    return s.translate(table)

def prepare_for_classification(text):
    text = rip_unicode(text)
    text = strip_emoji(text)
    return remove_punc(text)

class REGEXS(object):
    phone_number = r"\+(9[976]\d|8[987530]\d|6[987]\d|5[90]\d|42\d|3[875]\d|2[98654321]\d|9[8543210]|8[6421]|6[6543210]|5[87654321]|4[987654310]|3[9643210]|2[70]|7|1)\d{1,14}$"
    email = r"^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
    

def strip_personal_data(text):
    out_text = ""
    for i in text.split(" "):
        string = re.sub(REGEXS.phone_number, "<phone-number>",i)
        string = re.sub(REGEXS.email, "<email>", string)
        out_text += string
    return out_text.strip()
