from unidecode import unidecode
import re
import string

class Cleaner:
    def __init__(self,text):
        self.text_raw = text
        self.clean()

    def clean(self):
        self.text_clean = self.text_raw.lower()
        self.remove_diacritics()
        self.remove_in_word_apostrophe()
        self.remove_xword()
        self.remove_number()
        self.remove_punctuation()
        self.remove_extra_white_space()

    def remove_diacritics(self):
        self.text_clean = unidecode(self.text_clean)

    def remove_in_word_apostrophe(self):
        self.text_clean=  re.sub("(?<=[a-z])'(?=[a-z])",'',self.text_clean)

    def remove_xword(self):
        '''remove words with a number of xxxx.'''
        if not self.has_xword: return
        self.text_clean = re.sub('[x]{2,}','',self.text_clean)
        self.text_clean = re.sub('\s+',' ',self.text_clean).strip()

    def remove_number(self):
        self.text_clean = re.sub('\d+',' ',self.text_clean)
        self.text_clean = re.sub('\s+',' ',self.text_clean).strip()

    def remove_punctuation(self):
        for char in string.punctuation:
            self.text_clean = re.sub('\\'+char,' ',self.text_clean)
        self.text_clean = re.sub('\s+',' ',self.text_clean).strip()

    def remove_extra_white_space(self):
        #remove extra whitespace and some remaining characters
        self.text_clean = re.sub('\s+\n\s+','\n',self.text_clean)
        self.text_clean = re.sub('\n+','\n',self.text_clean)
        self.text_clean = re.sub('\s+',' ',self.text_clean).strip()

    @property
    def has_xword(self):
        if not hasattr(self,'_xwords'):
            self._xwords = re.findall('[x]{2,}',self.text_raw)
        return len(self._xwords) > 0

    @property
    def has_number(self):
        if not hasattr(self,'_numbers'):
            self._numbers= re.findall('\d+',self.text_raw)
        return len(self._numbers) > 0

    @property
    def has_apostrophe(self):
        if not hasattr(self,'_apostrophes'):
            self._apostrophes= re.findall("'+",self.text_raw)
        return len(self._apostrophes) > 0
