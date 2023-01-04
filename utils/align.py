from django.apps import apps
import glob
import textgrids
import sys
import pickle
import os

if sys.platform == 'darwin':
	align_dir = 'vol/tensusers/mbentum/ASTA/ALIGN/'
else:
	align_dir = '/vol/tensusers/mbentum/ASTA/ALIGN/'
output_dir = align_dir + 'OUTPUT/'
textgrid_dir = '../TEXTGRIDS/'

class Align:
    def __init__(self,recording, asr = None):
        if not asr: 
            from texts.models import Asr
            asr = Asr.objects.get(pk = 1)
        self.recording = recording
        self.asr = asr
        self.pickle_filename = '../pickle_align/align_r-' 
        self.pickle_filename += str(self.recording.pk)
        self.pickle_filename += '_a-' + str(self.asr.pk)
        if os.path.isfile(self.pickle_filename):
            self.__dict__ = self.load_pickle()
        else:
            self._load_alignment()
            if self.ok:
                self._align_ocr_transcriptions()
                self._get_asr_transcription()
                self._align_asr_words()
                self._check_ok()
                self.save_pickle()
        
    def __repr__(self):
        return 'Alignment of ' + self.recording.__repr__()

    def save_pickle(self):
        print('saving', self.pickle_filename)
        with open(self.pickle_filename, 'wb') as fout:
            pickle.dump(self, fout)

    def load_pickle(self):
        print('loading', self.pickle_filename)
        with open(self.pickle_filename, 'rb') as fin:
            o = pickle.load(fin)
        return o.__dict__
        

    def _check_ok(self):
        ok,ok1 = True,True
        for ocr_line in self.ocr_lines:
            if not ocr_line.ok: ok = False
        if not ok: self.ocr_lines_ok = False
        else: self.ocr_lines_ok = True 
        for asr_word in self.asr_words:
            if not asr_word.ok: ok1 = False
        if not ok1: self.asr_words_ok = False
        else: self.asr_words_ok=True 
        if not ok or not ok1: self.ok = False
        
    def _load_alignment(self):
        self.filename = recording_to_alignment_filename(self.recording,self.asr)
        o,a = recording_to_alignment(self.recording,self.asr)
        self.ocr_align = o
        self.asr_align = a
        if self.ocr_align:
            self.nchars = len(self.ocr_align)
        else: self.nchars = 0
        if self.nchars == 0 or not self.asr_align: self.ok = False
        else: 
            self.ok = True
            asr_check = list(set(self.asr_align))
            if len(asr_check) == 1 and asr_check[0] == '-': self.ok = False

    def _align_ocr_transcriptions(self):
        self.ocr_lines = []
        index = 0
        ocrline_index = 0
        for transcription in self.recording.ocr_transcriptions:
            if not transcription.text_clean: continue
            ol = Ocrline(transcription,self,index, ocrline_index=ocrline_index)
            self.ocr_lines.append(ol)
            index = ol.end + 1
            ocrline_index += 1

    @property
    def nocrlines(self):
        return len(self.ocr_lines)
            
    def _get_asr_transcription(self):
        self.asr_transcription = False
        asr_transcriptions = self.recording.asr_to_transcriptions(self.asr)
        if len(asr_transcriptions) == 0: return
        longest = asr_transcriptions[0]
        for x in asr_transcriptions:
            if x.duration > longest.duration: longest = x
        self.asr_transcription = longest

    def _align_asr_words(self):
        self.asr_words = []
        index=0
        self.index_to_times = {}
        self.index_to_asr_word= {}
        for word in self.asr_transcription.asr_word_table:
            aw = Asrword(word,self,index)
            self.asr_words.append(aw)
            index = aw.end + 1
            self.index_to_times.update(aw.index_to_times)
            self.index_to_asr_word.update(aw.index_to_asr_word)


    def _asr_word_tier(self):
        intervals = make_asr_word_intervals(self.asr_words)
        return textgrids.Tier(intervals)

    @property
    def textgrid(self):
        if hasattr(self,'_textgrid'): return self._textgrid 
        f = textgrid_dir + self.filename.split('/')[-1]
        self.filename_textgrid = f.replace('_output','.TextGrid')
        tg = textgrids.TextGrid()
        tg['asr words'] = self._asr_word_tier()
        for name in self.ocr_lines[0].interval_dict.keys():
            if name == 'asr words': continue
            if name not in tg.keys(): tg[name] = textgrids.Tier()
            for ocr_line in self.ocr_lines:
                if not ocr_line.start_time or not ocr_line.end_time:continue
                if ocr_line.duration == 0: continue
                interval = ocr_line.interval_dict[name]
                if not interval: continue
                tg[name].append(interval)
        tg.xmin = self.start_time
        tg.xmax = self.end_time
        tg.filename = self.filename_textgrid
        self._textgrid = tg
        return self._textgrid

    def save_textgrid(self):
        self.textgrid.write(self.filename_textgrid)

    @property
    def annotations(self):
        if hasattr(self,'_annotations'): return self._annotations
        from texts.models import Annotation
        self._annotations = Annotation.objects.filter(
            recording = self.recording,
            asr = self.asr
            )
        return self._annotations


    @property
    def start_time(self):
        return self.asr_words[0].start_time

    @property
    def end_time(self):
        return self.asr_words[-1].start_time
        
    def show(self,width = 90):
        starts = list(range(0,self.nchars,width))
        ends = list(range(width,self.nchars,width)) + [self.nchars+1]
        for start, end in zip(starts,ends):
            print('OCR: ', self.ocr_align[start:end])
            print('ASR: ', self.asr_align[start:end])
            print(' ')

    def show_ocrlines(self):
        for ol in self.ocr_lines:
            ol.show

    def filter_ocr_lines(self,mismatch_threshold = 55):
        if not hasattr(self,'ocr_lines'): return [] 
        output = []
        for ocr_line in self.ocr_lines:
            if ocr_line.align_mismatch < mismatch_threshold:
                output.append(ocr_line)
        return output

    @property
    def ocr_lines_ok_perc(self):
        return len(self.filter_ocr_lines()) / len(self.ocr_lines) * 100
        

class Ocrline:
    def __init__(self,transcription,align,index, ocrline_index):
        self.transcription = transcription
        self.align = align
        self.recording = align.recording
        self.index = index
        self.ocrline_index = ocrline_index
        self._align_transcription_with_alignment()

    def __repr__(self):
        m = 'Ocrline: ' + str(self.start) + ' ' + str(self.end) + ' | '
        m += str(self.start_time) + ' - '
        m += str(self.end_time) 
        return m

    def __str__(self):
        m = self.__repr__() + '\n'
        if self.duration: m += 'Duration: ' + str(self.duration) + '\n'
        m += 'mismatch: ' + str(self.align_mismatch) + '\n'
        m += 'ocr gaps: ' + str(self.ocr_align_gaps) + '\n'
        m += 'asr gaps: ' + str(self.asr_align_gaps) + '\n'
        m +=  'OCR: '+self.transcription.text_clean + '\n'
        m +=  'ASR: '+ self.asr_text + '\n'
        m +=  'OA:  '+self.ocr_align_text+ '\n'
        m +=  'AA:  '+self.asr_align_text
        return m

    def __hash__(self):
        return self.recording.pk * 10**6 + self.index

    def __eq__(self,other):
        return self.index == other.index
    
    def _align_transcription_with_alignment(self):
        self.indices,self.ok = align_ocr_transcription_with_ocr_alignment(
            self.index, self.transcription, self.align.ocr_align)
        if self.indices:
            self.start = self.indices[0]
            self.end = self.indices[-1]
        else: self.start, self.end = False, False

    @property
    def matching_indices(self):
        if hasattr(self,'_matching_indices'): return self._matching_indices
        indices = range(self.start,self.end+1)
        self._matching_indices = []
        for index in indices:
            if index in self.align.index_to_asr_word.keys():
                self._matching_indices.append(index)
        return self._matching_indices

    def _check_asr_word(self, word,other_indices):
        if not other_indices: return True
        indices = self.matching_indices
        other_count, this_count = 0, 0 
        for index in word.index_to_asr_word.keys():
            if index in other_indices: other_count += 1
            if index in indices: this_count += 1
        return this_count > other_count

    @property
    def annotations(self):
        if hasattr(self,'_annotations'): return self._annotations
        from texts.models import Annotation
        self._annotations = Annotation.objects.filter(
            recording = self.align.recording,
            asr = self.align.asr,
            ocrline_index = self.ocrline_index
            )
        return self._annotations
        

    @property
    def asr_words(self):
        if hasattr(self,'_asr_words'): return self._asr_words
        indices = self.matching_indices
        self._asr_words = []
        for index in indices:
            word = self.align.index_to_asr_word[index]
            if self.asr_words == []: 
                ok = self._check_asr_word(word,self.previous_indices)
            if word not in self._asr_words and ok:self.asr_words.append(word)
        if self._asr_words:
            ok = self._check_asr_word(self._asr_words[-1],self.next_indices)
            if not ok:
                self._asr_words = self._asr_words[:-1]
        return self._asr_words

    @property
    def asr_text(self):
        return ' '.join([x.word for x in self.asr_words])

    @property
    def ocr_text(self):
        return self.transcription.text_clean

    @property
    def ocr_align_text(self):
        return self.align.ocr_align[self.start:self.end+1]

    @property
    def asr_align_text(self):
        return self.align.asr_align[self.start:self.end+1]

    @property
    def align_mismatch(self):
        n = len(self.asr_align_text)
        mismatch = 0
        for achar,ochar in zip(self.asr_align_text,self.ocr_align_text):
            if achar != ochar: mismatch += 1
        return round(mismatch / n * 100,2)

    @property
    def align_match(self):
        return 100 - self.align_mismatch
            
    @property
    def asr_align_gaps(self):
        n = len(self.asr_align_text)
        gaps = self.asr_align_text.count('-')
        return round(gaps / n * 100,2)

    @property
    def ocr_align_gaps(self):
        n = len(self.asr_align_text)
        gaps = self.ocr_align_text.count('-')
        return round(gaps / n * 100,2)
                

    @property
    def start_time(self):
        if self.asr_words:
            return self.asr_words[0].start_time
        return False

            
    @property
    def end_time(self):
        if self.asr_words:
            return self.asr_words[-1].end_time
        return False

    @property
    def previous_indices(self):
        index = self.align.ocr_lines.index(self)
        if index == 0: return False
        return self.align.ocr_lines[index -1].matching_indices

    @property
    def next_indices(self):
        index = self.align.ocr_lines.index(self)
        if index == len(self.align.ocr_lines) -1: return False
        return self.align.ocr_lines[index +1].matching_indices

    @property
    def duration(self):
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return False

    @property
    def show(self):
            print(self.ocrline_index,'OCR: ', self.ocr_align_text)
            print(self.ocrline_index,'ASR: ', self.asr_align_text)


    @property
    def interval_dict(self):
        return make_ocr_line_intervals(self)
        

class Asrword:
    def __init__(self,asr_word,align,index):
        self.asr_word = asr_word
        self.word = asr_word['word']
        self.start_time = self.asr_word['start']
        self.end_time = self.asr_word['end']
        self.align = align
        self.index = index
        self._align_asr_word_with_alignment()
        self.start = self.indices[0]
        self.end = self.indices[-1]

    def __repr__(self):
        m = 'Asr word: '+ self.word + ' | ' 
        m += str(self.start_time) + ' - ' + str(self.end_time)
        return m
        
    def _align_asr_word_with_alignment(self):
        self.indices,self.ok = align_asr_word_with_asr_alignment(
            self.index, self.asr_word, self.align.asr_align)

    @property
    def duration(self):
        return self.end_time - self.start_time

    @property
    def show(self):
        print(self.align.asr_align[self.start:self.end+1])
        print(self.asr_word['word'])

    @property
    def index_to_times(self):
        indices = range(self.start,self.end+1)
        d = {}
        for index in indices:
            d[index] = {'start_time':self.start_time, 'end_time':self.end_time}
        return d
            
    @property
    def index_to_asr_word(self):
        indices = range(self.start,self.end+1)
        d = {}
        for index in indices:
            d[index] = self
        return d

    def in_interval(self,start,end):
        if start > end: return False
        if self.start_time < start and self.end_time > start: return True
        if self.start_time > start and self.start_time < end: return True
        if end < self.end_time and end > self.start_time: return True
        return False


def align_ocr_transcription_with_ocr_alignment(start_index,transcription,
    align_text):
    t = transcription.text_clean
    indices,ok = _string_pair_to_indices(start_index, t, align_text)
    return indices,ok
            
def align_asr_word_with_asr_alignment(start_index, asr_word, align_text):
    t = asr_word['word']
    indices, ok = _string_pair_to_indices(start_index,t,align_text)
    return indices,ok

def _string_pair_to_indices(start_index,short_string,long_string):
    ok = True
    indices = []
    for char in short_string:
        while True:
            if start_index > len(long_string) -1: break
            align_char = long_string[start_index] 
            if char == align_char: 
                indices.append(start_index)
                start_index += 1
                break
            start_index += 1
    if len(indices) != len(short_string): 
        print(short_string,start_index)
        ok = False
    if short_string != _make_string_from_indices(indices,long_string):
        print(short_string,_make_string_from_indices(indices,long_string))
        ok = False
    #assert len(indices) == len(short_string)
    #assert short_string == _make_string_from_indices(indices,long_string)
    return indices, ok 
    

def _make_string_from_indices(indices,align_text):
    o = ''
    for index in indices:
        o += align_text[index]
    return o


def make_ocr_line_intervals(ocr_line):
    '''make textgrid intervals for different tiers based on ocr line info.'''
    start, end = ocr_line.start_time, ocr_line.end_time
    d = {}
    d['ocr transcription'] = textgrids.Interval(
        ocr_line.transcription.text_clean, start, end)
    d['asr transcription'] = textgrids.Interval(ocr_line.asr_text,start,end) 
    d['ocr align'] = textgrids.Interval(ocr_line.ocr_align_text,start,end) 
    d['asr align'] = textgrids.Interval(ocr_line.asr_align_text,start,end) 
    d['asr words'] = make_asr_word_intervals(ocr_line.asr_words)
    return d

def make_asr_word_intervals(asr_words):
    '''make textgrid intervals for different asr word interval tier.'''
    asr_word_intervals = []
    for word in asr_words:
        interval = textgrids.Interval(word.word, word.start_time, 
            word.end_time)
        asr_word_intervals.append(interval)
    return asr_word_intervals

def recording_to_alignment_filename(recording, asr = None):
    if not asr: 
        from texts.models import Asr
        asr = Asr.objects.get(pk = 1)
    f = output_dir + '*recording-' + str(recording.pk) +'_asr-'+str(asr.pk)+'*'
    fn = glob.glob(f)
    if fn: return fn[0]
    else: return False

def recording_to_alignment(recording, asr = None):    
    '''
    recording  the recording you need the alignment for between ocr and asr
    asr        asr object to select the asr version to align with the ocr text
    '''
    if not asr: 
        from texts.models import Asr
        asr = Asr.objects.get(pk = 1)
    f = recording_to_alignment_filename(recording,asr)
    if not f: return False,False
    print(f)
    with open(f) as fin:
        ocr, asr = fin.read().split('\n')
    return ocr, asr


