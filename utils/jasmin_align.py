# part of the ASTA project to align wav2vec and jasmin with nw

import glob
import json
from matplotlib import pyplot as plt
import os
import random
from utils import needleman_wunch as nw
from texts.models import Jasmin_recording

base_dir = '/vol/tensusers3/mbentum/astla/'
jasmin_wav2vec_dir = base_dir + 'jasmin_wav2vec2_transcription/'
jasmin_align = base_dir + 'jasmin_align/'

def _select_10_perc_table_filenames():
    random.seed(9)
    fn = table_filenames()
    random.shuffle(fn)
    nfiles = int(len(fn)/10)
    return fn[:nfiles]
    

def table_filenames():
    fn = glob.glob(jasmin_wav2vec_dir + '*.table')
    return fn

def text_filename():
    fn = glob.glob(jasmin_wav2vec_dir + '*.txt')
    return fn

def load_table(filename):
    with open(filename) as fin:
        t = fin.read()
    temp= [x.split('\t') for x in t.split('\n') if x]
    table = []
    for grapheme, start, end in temp:
        table.append([grapheme,float(start), float(end)])
    return table

def load_text(filename):
    with open(filename) as fin:
        t = fin.read()
    return t

def table_filename_to_jasmin_id(f):
    jasmin_id = f.split('/')[-1].split('.')[0]
    return jasmin_id

def make_alignments(small_set = False, component = None):
    from texts.models import Jasmin_recording
    if not small_set: fn = table_filenames()
    else: fn = _select_10_perc_table_filenames()
    random.shuffle(fn)
    for f in fn:
        jasmin_id = table_filename_to_jasmin_id(f)
        if component:
            jr = Jasmin_recording.objects.get(identifier=jasmin_id)
            if jr.component() != component: 
                print('skipping',jr.awd_filename)
                continue
        align_filename = jasmin_align+jasmin_id 
        if os.path.isfile(align_filename): 
            print('skiping',jasmin_id, small_set, len(fn))
            continue
        print('handling',jasmin_id, small_set, len(fn))
        Align(jasmin_id, make_phrases = False )


    
class Align:
    '''align object to align jasmin recoring and wav2vec transcript.
    '''
    def __init__(self,jasmin_id, make_phrases = True):
        self.jasmin_id = jasmin_id
        self.recording= Jasmin_recording.objects.get(identifier = jasmin_id)
        self.awd_words = list(self.recording.jasmin_word_set.all())
        # self.awd_text = ' '.join([w.awd_word for w in self.awd_words])
        self.awd_text = phrases_to_text(self.recording.phrases())
        self._set_wav2vec_table_and_text()
        self._set_align()
        if make_phrases:
            self._set_phrases()

    def _set_wav2vec_table_and_text(self):
        temp =jasmin_wav2vec_dir+self.recording.identifier
        self.wav2vec_base_filename=temp
        table = load_table(self.wav2vec_base_filename+'.table')
        self.wav2vec_table = fix_unk_in_table(table)
        self.wav2vec_text = load_text(self.wav2vec_base_filename+'.txt')

    def _set_align(self):
        directory = jasmin_align
        jasmin_text = self.awd_text
        self.align_filename = directory + self.jasmin_id
        print(self.align_filename)
        if os.path.isfile(self.align_filename): 
            with open(self.align_filename) as fin:
                self.align = fin.read()
        else:
            self.align = nw.nw(jasmin_text, self.wav2vec_text)
            with open(self.align_filename, 'w') as fout:
                fout.write(self.align)
        
    def _set_phrases(self):
        phrases = sort_phrases(self.recording.phrases())
        self.words = []
        o = align_phrases_with_aligned_text(phrases,
            self.aligned_jasmin_text)
        self.phrases = []
        for phrase, start_index, end_index in o:
            p = Phrase(phrase,self,start_index, end_index)
            if p.words:
                self.words.extend(p.words)
            self.phrases.append(p)
            
    def alignment_labels(self, delta = .5):
        return [p.alignment(delta = delta) for p in self.phrases]

    def perc_bad(self, delta = .5):
        labels = self.alignment_labels(delta)
        ntotal = len(labels)
        if ntotal == 0: return 0
        nbad = labels.count('bad')
        return round(nbad / ntotal * 100,2)

    @property
    def duration(self):
        return self.recording.duration

    @property
    def component(self):
        return 'jasmin'

    @property
    def nspeakers(self):
        return 1

    @property
    def aligned_wav2vec_text(self):
        return self.align.split('\n')[1]
        
    @property
    def aligned_jasmin_text(self):
        return self.align.split('\n')[0]

    @property
    def wav2vec_aligned_graphemes_timestamps(self):
        o = []
        i = 0
        for char in self.aligned_wav2vec_text:
            if char == '-': 
                o.append([])
                continue
            # print(i,char)
            o.append(self.wav2vec_table[i])
            i += 1
        return o

    @property
    def average_match_perc(self):
        match_percs = []
        for phrase in self.phrases:
            match_percs.append(phrase.match_perc)
        if len(match_percs) == 0: return 0
        return round(sum(match_percs) / len(match_percs),2)


class Phrase:
    def __init__(self,phrase,align=None,start_index=None,end_index=None):
        self.phrase = phrase
        self.align = align
        self.start_time = self.phrase[0].start_time
        self.end_time = self.phrase[-1].end_time
        self.duration = self.end_time - self.start_time
        self.nwords = len(self.phrase)
        self.start_index = start_index
        self.end_index = end_index
        self._set_info()
        self._add_words()

    def __repr__(self):
        m = self.text[:18].ljust(21)
        m += ' | ' + self.alignment()
        return m

    def __str__(self):
        m = self.aligned_jasmin_text + '\n'
        m += self.aligned_wav2vec_text + '\n'
        m += 'jasmin ts:'.ljust(12) + str(round(self.start_time,2)) + ' '
        m += str(round(self.end_time,2)) + '\n' 
        m += 'w2v ts:'.ljust(12) + str(self.wav2vec_start_time) + ' '
        m += str(self.wav2vec_end_time) +'\n' 
        m += 'alignment:'.ljust(12) + self.alignment() + '\n'
        m += 'match:'.ljust(12) + str(self.match_perc)
        return m 

    def _set_info(self):
        if not self.align: return
        if self.start_index == self.end_index == None: return
        align = self.align
        start, end = self.start_index, self.end_index
        jasmin = align.aligned_jasmin_text[start:end]
        wav2vec= align.aligned_wav2vec_text[start:end]
        graphemes = align.wav2vec_aligned_graphemes_timestamps[start:end]
        self.aligned_jasmin_text= jasmin
        self.jasmin_text = jasmin.replace('-','').strip()
        self.aligned_wav2vec_text= wav2vec
        self.wav2vec_text = wav2vec.replace('-','')
        self.wav2vec_aligned_graphemes = graphemes
        self._set_wav2vec_timestamps()

    def _add_words(self):
        self.words = []
        o = phrase_words(self)
        for word_index,line in enumerate(o):
            w, start, end = line
            word = Word(w,word_index,start,end,self)
            self.words.append(word)

    def _set_wav2vec_timestamps(self):
        self.wav2vec_start_time= None
        self.wav2vec_end_time= None
        for line in self.wav2vec_aligned_graphemes:
            if len(line) == 3 and line[0] != ' ':
                self.wav2vec_start_time= line[1]
                break
        for line in self.wav2vec_aligned_graphemes[::-1]:
            if len(line) == 3 and line[0] != ' ':
                self.wav2vec_end_time= line[-1]
                break
        if self.wav2vec_start_time == self.wav2vec_end_time == None:
            self.wav2vec_timestamps_ok = False
        else:
            self.wav2vec_timestamps_ok = False

    def alignment(self,delta = 0.5):
        if self.start_index == self.end_index == None: return 'bad'
        if not self.wav2vec_start_time and not self.wav2vec_end_time:
            return 'bad'
        self.text_ok = self.jasmin_text == self.text
        d = delta
        self.start_ok=equal_with_delta(self.start_time,
            self.wav2vec_start_time,d)
        self.end_ok = equal_with_delta( self.end_time, self.wav2vec_end_time, d)
        if self.start_ok and self.end_ok: return 'good'
        if self.start_ok:  return 'start match'
        if self.end_ok:  return 'end match'
        if self.text_ok: return 'middle match'
        return 'bad'

    @property
    def match_perc(self):
        match = 0
        nchar = len(self.aligned_jasmin_text)
        if nchar == 0: return 0
        texts = zip(self.aligned_jasmin_text,self.aligned_wav2vec_text)
        for jasmin_char,w2v_char in texts:
            if jasmin_char == w2v_char: match += 1
        return round(match / nchar * 100,2)

    @property
    def text(self):
        return phrase_to_text(self.phrase).replace('-','')

    @property
    def nchars(self):
        return len(self.text)

class Word:
    def __init__(self,word, word_index, start_index, end_index, phrase):
        self.word = word
        self.awd_word = word.awd_word
        self.text = word.awd_word
        self.start_time = self.word.start_time
        self.end_time = self.word.end_time
        self.word_index = word_index
        self.start_index = start_index
        self.end_index = end_index
        self.phrase = phrase
        self._set_info()

    def __repr__(self):
        m = self.awd_word + ' '+str(self.wav2vec_start_time) + ' - ' 
        m += str(self.wav2vec_end_time) + ' | '
        m += self.alignment()
        return m

    def _set_info(self):
        if self.start_index == self.end_index == None: return
        start, end = self.start_index, self.end_index
        jasmin = self.phrase.aligned_jasmin_text[start:end]
        wav2vec= self.phrase.aligned_wav2vec_text[start:end]
        self.aligned_jasmin_text= jasmin
        self.jasmin_text = jasmin.replace('-','').strip()
        self.aligned_wav2vec_text= wav2vec
        self.wav2vec_text = wav2vec.replace('-','')
        self.wav2vec_start_time= None
        self.wav2vec_end_time= None
        if hasattr(self.phrase, 'wav2vec_aligned_graphemes'):
            graphemes = self.phrase.wav2vec_aligned_graphemes[start:end]
            self.wav2vec_aligned_graphemes = graphemes
            self._set_wav2vec_timestamps()

    def _set_wav2vec_timestamps(self):
        for line in self.wav2vec_aligned_graphemes:
            if len(line) == 3 and line[0] != ' ':
                self.wav2vec_start_time= line[1]
                break
        for line in self.wav2vec_aligned_graphemes[::-1]:
            if len(line) == 3 and line[0] != ' ':
                self.wav2vec_end_time= line[-1]
                break
        if self.wav2vec_start_time == self.wav2vec_end_time == None:
            self.wav2vec_timestamps_ok = False
        else:
            self.wav2vec_timestamps_ok = False

    def alignment(self,delta = 0.25):
        if self.start_index == self.end_index == None: return 'bad'
        if not self.wav2vec_start_time or not self.wav2vec_end_time:
            return 'bad'
        self.text_ok = self.jasmin_text == self.text
        d = delta
        self.start_ok=equal_with_delta(self.start_time,
            self.wav2vec_start_time,d)
        self.end_ok = equal_with_delta( self.end_time, 
            self.wav2vec_end_time, d)
        if self.start_ok and self.end_ok: return 'good'
        if self.start_ok:  return 'start match'
        if self.end_ok:  return 'end match'
        if self.text_ok: return 'middle match'
        return 'bad'
         

    @property
    def duration(self):
        return self.end_time - self.start_time

    @property
    def nchars(self):
        return len(self.text)

    @property
    def match_perc(self):
        match = 0
        nchar = len(self.aligned_jasmin_text)
        if nchar == 0: return 0
        texts = zip(self.aligned_jasmin_text,self.aligned_wav2vec_text)
        for jasmin_char,w2v_char in texts:
            if jasmin_char == w2v_char: match += 1
        return round(match / nchar * 100,2)


def phrase_words(phrase):
    start = 0
    output = []
    for word in phrase.phrase:
        w = word.awd_word
        end = _find_end_index(w, phrase.aligned_jasmin_text,start,start)
        if not end:
            output.append([word,None,None])
        else:
            output.append([word,start,end])
            start = end 
    return output

            
def phrase_to_text(phrase):
    return ' '.join([w.awd_word for w in phrase]).replace('-','')

def phrase_to_len(phrase):
    return len(phrase_to_text(phrase))

def _find_end_index(phrase_text, text, start_index, end_index):
    if type(start_index) != int: return False
    if end_index < start_index + len(phrase_text):
        end_index = start_index + len(phrase_text)
    compare_text = text[start_index:end_index].replace('-','').strip(' -')
    #print(phrase_text, compare_text)
    if phrase_text.replace('-','').strip() == compare_text:
        return end_index
    return _find_end_index(phrase_text,text,start_index,end_index+1)
   

def align_phrases_with_aligned_text(phrases, text):
    output = []
    start = 0
    word_indices = []
    for phrase in phrases:
        if hasattr(phrase,'text'): phrase = phrase.phrase
        pt = phrase_to_text(phrase)
        end = _find_end_index(pt,text,start, start)
        if not end:
            output.append([phrase,None,None])
        else:
            output.append([phrase,start,end])
            start = end
    return output






    
def equal_with_delta(n1,n2,delta):
    if type(n1) != float: raise ValueError('gt timestamp should be available')
    if type(n2) != float: return False
    lower_bound, upper_bound = n1-delta, n1+delta
    if n2 >= lower_bound and n2 <= upper_bound: return True
    return False

def sort_phrases(phrases):
    return sorted(phrases, key = lambda x: x[0].start_time)

def phrases_to_text(phrases):
    p= sort_phrases(phrases)
    o = []
    for phrase in p:
        o.append(phrase_to_text(phrase))
    return ' '.join(o)

def _unk_in_table(table):
    for line in table:
        if line[0] == '[UNK]': return True
    return False

def fix_unk_in_table(table):
    if not _unk_in_table(table): return table
    output = []
    for line in table:
        if line[0] == '[UNK]':
            output.extend([[x,line[1],line[2]] for x in list('[UNK]')])
        else: output.append(line)
    return output
    

def extract_all_phrases(aligns):
    phrases = []
    for align in aligns:
        phrases.extend(align.phrases)
    return phrases

def word_to_dataset_line(word, word_index):
    w, a = word, word.phrase.align
    line = [word_index, a.jasmin_id, a.duration, a.component,a.nspeakers]
    line.extend([w.start_index,w.end_index, w.nchars])
    line.extend([round(w.duration,2),w.start_time,w.end_time])
    line.extend([w.wav2vec_start_time,w.wav2vec_end_time])
    line.extend([w.alignment(), w.match_perc])
    return line

def words_to_dataset(words):
    ds = []
    for i,word in enumerate(words):
        line = word_to_dataset_line(word,i)
        ds.append(line)
    return ds

def phrase_to_dataset_line(phrase, phrase_index, randomize = None):
    p, a = phrase, phrase.align
    line = [phrase_index,a.jasmin_id, a.duration, a.component,a.nspeakers]
    line.extend([p.start_index,p.end_index, p.nwords])
    line.extend([round(p.duration,2),p.start_time,p.end_time])
    line.extend([p.wav2vec_start_time,p.wav2vec_end_time])
    line.extend([p.alignment(),p.alignment(1),p.alignment(0.1)])
    line.append(p.match_perc)
    line.append(randomize)
    return line

def phrases_to_dataset(phrases, randomize = None):
    ds = []
    for i,phrase in enumerate(phrases):
        line = phrase_to_dataset_line(phrase,i, randomize)
        ds.append(line)
    return ds

def align_to_dataset_line(align, randomize = None):
    a = align
    line = [a.jasmin_id, a.duration, a.component, a.nspeakers]
    line.extend( [len(a.phrases), a.average_match_perc, a.perc_bad()] )
    line.extend( [a.perc_bad(1),a.perc_bad(0.1)] )
    line.append(randomize)
    return line

def save_dataset(ds,filename):
    with open(filename,'w') as fout:
        json.dump(ds,fout)

def load_dataset(filename):
    with open(filename) as fin:
        ds = json.load(fin)
    return ds


def load_word_dataset():
    header = 'word_index,jasmin_id,audiofile_duration,component,nspeakers'
    header += ',start_index,end_index,nchars,word_duration,start_time'
    header += ',end_time,wav2vec_start_time,wav2vec_end_time'
    header += ',label_0.5,match_perc'
    header = header.split(',')
    return load_dataset('../word_ds.json'), header

def load_align_dataset(randomized = False):
    header = 'jasmin_id,duration,component,nspeakers,nphrases'
    header = ',avg_match_perc'
    header += ',perc_bad_0.5,perc_bad_1,perc_bad_0.1'
    header = header.split(',')
    if randomized:
        header.append('randomize')
        return load_dataset('../align_randomized_text_ds.json'), header
    return load_dataset('../align_ds.json'), header

def load_phrase_dataset(randomized = False):
    header = 'phrase_index,jasmin_id,audiofile_duration,component,nspeakers'
    header += ',start_index,end_index,nwords,phrase_duration,start_time'
    header += ',end_time,wav2vec_start_time,wav2vec_end_time'
    header += ',label_0.5,label_1,label_0.1,match_perc'
    header = header.split(',')
    if randomized:
        print('loading randomized')
        header.append('randomize')
        return load_dataset('../phrase_randomized_text_ds.json'), header
    return load_dataset('../phrase_ds.json'), header
    
def make_word_dataset(save = False):
    jasmin_ids = [f.split('/')[-1] for f in glob.glob(jasmin_align +'fn*')]
    word_ds = []
    for i,jasmin_id in enumerate(jasmin_ids):
        print(jasmin_id,i,len(jasmin_ids))
        align = Align(jasmin_id)
        word_ds.extend( words_to_dataset(align.words ) )
    if save:
        save_dataset(word_ds,'../word_ds.json')
    return word_ds
    

def make_datasets(save = False):
    jasmin_ids = [f.split('/')[-1] for f in glob.glob(jasmin_align +'fn*')]
    phrase_ds = []
    align_ds = []
    for i,jasmin_id in enumerate(jasmin_ids):
        print(jasmin_id,i,len(jasmin_ids))
        align = Align(jasmin_id)
        phrase_ds.extend( phrases_to_dataset(align.phrases, ) )
        align_ds.append(align_to_dataset_line(align) )
    if save:
        save_dataset(phrase_ds,'../phrase_ds.json')
        save_dataset(align_ds,'../align_ds.json')
    return phrase_ds, align_ds


        
def perc_bad_duration_plot(alpha = .2):
    ds, header = load_align_dataset()
    ci = header.index('component')
    di = header.index('duration')
    pi = header.index('perc_bad_0.5')
    comps = list(set([x[ci] for x in ds]))
    comps = sorted(comps)
    comps.pop(comps.index('d'))
    plt.figure()
    for comp in comps:
        if comp == 'c': 
            temp = [x for x in ds if x[ci] in 'cd']
        else: temp = [x for x in ds if x[ci] == comp]
        dur = [x[di] for x in temp]
        perc = [x[pi] for x in temp]
        plt.scatter(dur,perc,alpha=alpha)
    component_names = ['p','q']
    leg = plt.legend(component_names)
    for lh in leg.legendHandles:
        lh.set_alpha(1)
    plt.xlabel('audio duration in seconds')
    plt.ylabel('% incorrectly aligned phrases')
    return leg, component_names



def multiple_regression_ds(ads,header):
    di = header.index('duration')
    si = header.index('nspeakers')
    pi = header.index('perc_bad_0.5')
    ci = header.index('component')
    speech_type, duration, nspeakers, perc_bad,comps = [], [], [], [], []
    speech_types = get_all_speech_types()
    ds = []
    for x in ads:
        duration.append( x[di] )
        nspeakers.append( x[si] )
        speech_type.append( get_speech_type(x[ci], speech_types) )  
        comps.append(x[ci])
        perc_bad.append( x[pi] )
        line = [x[pi],x[di],x[si],speech_type[-1]]
        ds.append('\t'.join(map(str,line)))
    return ds, perc_bad, duration, nspeakers, speech_type, comps
        

def delta_start_delta_end_phrase_line(phrase_line, header):
    l = phrase_line
    start,end = l[header.index('start_time')],l[header.index('end_time')]
    w2v_start = l[header.index('wav2vec_start_time')]
    w2v_end = l[header.index('wav2vec_end_time')]
    if w2v_start == None or w2v_end == None: return False, False
    dstart = start - w2v_start
    dend = end - w2v_end
    return dstart, dend

def delta_start_delta_end_phrases_ds(phrase_ds, header):
    dstart, dend = [], [] 
    for phrase in phrase_ds:
        s, e = delta_start_delta_end_phrase_line(phrase,header)
        if s == None or e == None: continue
        dstart.append(s)
        dend.append(e)
    return dstart, dend

def delta_start_delta_end_word_ds(word_ds, header):
    dstart, dend = delta_start_delta_end_phrases_ds(word_ds, header)
    return dstart, dend

def plot_delta_histogram_words(dstart,dend):
    plot_delta_histogram(dstart, dend, ylabel = 'word counts')

def plot_delta_histogram(dstart, dend, ylabel = 'phrase counts'):
    s = [x for x in dstart if x < 1 and x > -1]
    e = [x for x in dend if x < 1 and x > -1]
    fig = plt.figure()
    plt.hist(s,bins=100,alpha = 0.5,color='blue')
    plt.hist(e,bins=100,alpha = 0.5,color='red')
    plt.legend(['start delta','end delta'])
    plt.xlabel('seconds')
    plt.ylabel(ylabel)
    return fig

    

def _make_index_mapping_aligned_text(aligned_text):
    '''maps indices from not aligned text to aligned text.
    aligned text contains - characters to align a text with another text
    that containes more/differenct characters at a given location.
    '''
    output = []
    no_underscore_index = 0
    text_to_aligned = {}
    aligned_to_text = {}
    for i,char in enumerate(aligned_text):
        if char == '-': continue
        output.append({'aligned_text':i,'text':no_underscore_index})
        text_to_aligned[no_underscore_index] = i
        aligned_to_text[i] = no_underscore_index
        no_underscore_index += 1
    return output, aligned_to_text, text_to_aligned

def set_phrase_boundaries_to_space(phrases, text, aligned_text):
    '''phrase boundaries should be ' ' for the alignement procedure
    with randomized text it can be non ' '
    there for to align a phrase with the randomized text the phrase boundaries
    need to be set to ' ' (this does not effect the randomized text /w2v 
    alignment
    this function sets the characters at the phrase boundary to ' '
    '''
    output = align_phrases_with_random_text(phrases, text)
    o, at, ta = _make_index_mapping_aligned_text(aligned_text)
    text_to_aligned = ta
    aligned_text_list = list(aligned_text)
    for line in output:
        i = line[-1]
        if i == len(text): continue
        phrase_boundary_index_aligned = text_to_aligned[i]
        # print(text[i],aligned_text[phrase_boundary_index_aligned],i)
        aligned_text_list[phrase_boundary_index_aligned] = ' '
        # print(aligned_text_list[phrase_boundary_index_aligned], phrase_boundary_index_aligned)
        # print('+')
    return ''.join(aligned_text_list)
        
        
        
    
def _mv_error_random_align(align):
    directory = '/'.join(align.align_filename.split('/')[:-1]) + '/'
    old_directory = directory + 'OLD/'
    if not os.path.isdir(old_directory): os.mkdir(old_directory)
    cmd = 'mv ' + align.align_filename + ' ' + old_directory
    os.system(cmd)

def _check_old_dir(align):
    directory = '/'.join(align.align_filename.split('/')[:-1]) + '/'
    old_directory = directory + 'OLD/'
    if not os.path.isdir(old_directory): os.mkdir(old_directory)
    f = old_directory + align.jasmin_id
    print(f)
    return os.path.isfile(f)
    
def _handle_error_align(jasmin_id,n):
    try: a = Align(jasmin_id,randomize = n)
    except:
        print('fixing',jasmin_id,n)
        a = Align(jasmin_id, randomize = n, make_phrases = False)
        _mv_error_random_align(a)
        a = Align(jasmin_id, randomize = n, make_phrases = False)
        _handle_error_align(jasmin_id,n)
    else:print(jasmin_id,n,'ok')
    
def handle_all_error_align(n = []):
    directory = jasmin_align[:-1] + '_2/'
    jasmin_ids = [f.split('/')[-1] for f in glob.glob(directory +'fn*')]
    random.shuffle(jasmin_ids)
    phrase_ds = []
    align_ds = []
    if not n:
        randomizes =[2,4,8,16,32,64]
    else: randomizes = n
    random.shuffle(randomizes)
    for n in randomizes:
        print(n)
        for jasmin_id in jasmin_ids:
            _handle_error_align(jasmin_id,n)
        


