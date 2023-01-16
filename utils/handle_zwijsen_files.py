import glob
import os
import pickle
import re
import subprocess

f = '../zwijsen_audio_info.txt'
audio_info = dict([l.split('\t') for l in open(f).read().split('\n') if l])

def load_ok_audios():
    '''Some audio files do not contain any speech 
    ASR results in empty transcription
    this function loads all audios that contain some speech
    this selection is based on the asr output not being empty
    '''
    audios = make_audios()
    empty, d = check_transcriptions()
    ok_audios = {}
    identifiers = [x.split('/')[-1].split('.')[0] for x in d.keys()]
    for i in identifiers:
        if i in audios.keys(): ok_audios[i] = audios[i]
        else: print('could not find id in audios:',i)
    return ok_audios
    

def find_bad_audio_files(audios = None):
    '''some audio files are corrupted.
    files with very low bit rate indicate corruption 
    returns all files with unexpectedly low bit rate
    '''
    if not audios: audios = make_audios()
    bads = []
    for audio in audios.values():
        #very low bit rate indicates a problem
        if not 'k' in audio.bit_rate: bads.append(audio) 
    return bads

def move_bad_audio_files(audios = None):
    ''' move the corrupted audio files to a different folder. '''
    bads = find_bad_audio_files(audios)
    goal_dir = '../bad_zwijsen_wav16/'
    for bad in bads:
        if os.path.isfile(bad.path):
            filename = bad.path.split('/')[-1]
            new_path = goal_dir + filename
            print('mv ' + bad.path + ' ' + new_path)
            os.system('mv ' + bad.path + ' ' + new_path)
        else: print(bad.path, 'not found')

def make_audios():
    '''make all audio objects based on sox info stored in text file.
    contains information about the ../zwijsen_wav16 wav files.
    '''
    audios = {}
    for k in audio_info.keys():
        # print(k,audio_info[k])
        audios[k] = Audio(k)
        if not audios[k].ok: print(k)
    return audios

class Audio:
    def __init__(self,file_id):
        self.file_id = file_id
        self._set_info()
        if self.ok:
            t = self.info.split(',')
            self.path = t[0].split(':')[1]
            self.channels= int(t[1].split(':')[1])
            self.sample_rate= int(t[2].split(':')[1])
            self.precision= t[3].split(':')[1]
            self.duration= t[4].strip('Duration:').split('=')[0]
            self.samples= t[4].strip('Duration:').split('=')[1]
            self.samples = int(self.samples.split('samples')[0])
            self.file_size= t[5].split(':')[1]
            self.bit_rate = t[6].split(':')[1]
            self.sample_encoding = t[7].split(':')[1]
            self.seconds = self.samples / self.sample_rate
            self.comp = self.path.split('/')[-3]
            self.region= self.path.split('/')[-2]

    def __repr__(self):
        m = 'Audio: ' + self.file_id + ' | ' + self.duration + ' | ' 
        m += str(self.channels) + ' | ' + self.comp + ' | ' + self.region
        return m

    def _set_info(self):
        self.ok =True
        try: self.info = audio_info[self.file_id]
        except:
            print(file_id,'not found in audio_info')
            self.ok = False
        if 'Duration' not in self.info:self.ok = False

def make_time(seconds):
    '''converts sox str time to float seconds.'''
    seconds = int(seconds)
    h = str(seconds //3600)
    seconds = seconds % 3600
    m = str(seconds // 60)
    s = str(seconds % 60)
    if len(h) == 1:h =  '0' + h
    if len(m) == 1:m =  '0' + m
    if len(s) == 1:s = '0' + s
    return ':'.join([h,m,s])

def _make_audio_info():
    '''writes sox info to a text file for wav files in ../zwijsen_wav16.'''
    fn = glob.glob('../zwijsen_wav16/*.wav')
    output = []
    for f in fn:
        file_id = f.split('/')[-1].split('.')[0]
        o = subprocess.check_output('sox --i ' + f, shell =True).decode()
        o = o .replace('\n','\t').strip()
        o = o.replace('\t',',').replace("'",'')
        o = re.sub('\s+','',o)
        output.append(file_id + '\t' + o)
    with open('../zwijsen_audio_info.txt','w') as fout:
        fout.write('\n'.join(output))
    return output

def check_transcriptions():
    '''check whether transcriptions are empty.
    return filename list of empty transcriptions 
    and a dictionary mapping filename to transcription
    '''
    fn = glob.glob('../zwijsen_wav2vec2_transcription/*.txt')
    empty = []
    d = {}
    for f in fn:
        with open(f) as fin:
            t = fin.read()
        if not t: empty.append(f)
        else: d[f] = t
    return empty, d


def read_map_flow_file():
    '''file created by simone to map audio to prompt.
    flow prompts are story like?
    '''
    with open('../audio2text-matched_flow.map') as fin:
        t = fin.read().split('\n')
    txt_dir = '../zwijsen_text/flow/'
    audio_dir = '../zwijsen_wav16/'
    d = {}
    for i,line in enumerate(t):
        if not line:continue
        audio, txt = line.split('\t')
        identifier = audio.split('.')[0]
        d[identifier] = [audio_dir + audio, txt_dir + txt]
    return d

def read_map_stage_file():
    '''file created by simone to map audio to prompt.
    stage prompts are news like?
    '''
    with open('../audio2text-matched_stage.map') as fin:
        t = fin.read().split('\n')
    txt_dir = '../zwijsen_text/stage/'
    audio_dir = '../zwijsen_wav16/'
    d = {}
    for i,line in enumerate(t):
        if not line:continue
        audio, txt = line.split('\t')
        identifier = audio.split('.')[0]
        d[identifier] = [audio_dir + audio, txt_dir + txt]
    return d

def read_map_text_file():
    return {}

def identifier_to_info_dict(identifier):
    role = {'p1':'news broadcaster', 'p2':'poet', 'p3':'traveller',
        'p4':'joker','p5':'reading chair'}
    chunks = identifier.split('_')
    d={'pupil_id':chunks[0],'role':'','reading_level':'','chapter':''}
    d['session_type'] = chunks[1]
    d['avi_level'] = chunks[2]
    d['package'] = chunks[3]
    if d['session_type'] == 'stage':
        d['role'] = role[chunks[4]]
        f = read_map_stage_file
    if d['session_type'] == 'flow':
        d['reading_level'] == chunks[4]
        f = read_map_flow_file
    if d['session_type'] == 'text':
        d['chapter'] = chunks[4]
        f = read_map_text_file
    d['fragment_id'] = chunks[5]
    map_d= f()
    if identifier not in map_d.keys(): 
        d['audio_path'], d['text_path'] = None, None
    else:
        d['audio_path'], d['text_path'] = map_d[identifier]
    return d

def get_all_pupil_ids():
    audios = load_ok_audios()
    pupil_ids = []
    for k in audios.keys():
        d = identifier_to_info_dict(k)
        n = d['pupil_id']
        if n not in pupil_ids: pupil_ids.append(n)
    return pupil_ids
    
def audio_filename_to_identifier(audio_filename):
    identifier = audio_filename.split('/')[-1].split('.')[0]
    return identifier

def audio_filename_to_prompt(audio_filename):
    identifier = audio_filename_to_identifier(audio_filename)
    info_dict = identifier_to_info_dict(identifier)
    if not info_dict['text_path']: return False
    with open(info_dict['text_path']) as fin:
        prompt = fin.read()
    return prompt 

def audio_filename_to_session_info(audio_filename):
    audios = load_ok_audios()
    identifier = audio_filename_to_identifier(audio_filename)
    if identifier not in audios.keys(): return False
    audio = audios[identifier]
    info_dict = identifier_to_info_dict(identifier)
    prompt = audio_filename_to_prompt(audio_filename)
    prompt = prompt.strip()
    if not prompt: return False
    word_list = prompt_to_word_list(prompt)
    return identifier, audio, info_dict, prompt, word_list

def prompt_to_word_list(prompt):
    wl = cleaner.Cleaner(prompt).text_clean.split(' ')
    return wl
    
    
    wl = handle_dart_excel.session_list_to_word_list(s)
    cl = handle_dart_excel.session_list_to_correct_list(s)
    d['ncorrect'] = cl.count(1)
    d['nwords'] = len(wl) 
    d['all_correct'] = cl.count(1) == len(cl)
    d['all_incorrect'] = cl.count(0) == len(cl)
    d['word_list'] = ','.join(wl)
    d['correct_list'] = ','.join(map(str,cl))
    pupil_id = handle_dart_excel.get_pupil(s[0])
    d['pupil'] = Pupil.objects.get(identifier = pupil_id)
    teacher_id = handle_dart_excel.get_teacher(s[0])
    d['teacher']= Teacher.objects.get(identifier = teacher_id)
    school_id = handle_dart_excel.get_school(s[0])
    d['school']= School.objects.get(identifier = school_id)
    d['audio_filename'] = wav_filename.split('/')[-1]
    d['identifier'] = identifier
    d['duration'] = audio.seconds
    d['list_id'] = handle_dart_excel.get_list_id(s[0])
    d['set_id'] = handle_dart_excel.get_set_id(s[0])
    d['page_id'] = handle_dart_excel.get_page_id(s[0])
    d['condition'] = handle_dart_excel.get_condition(s[0])
    d['test_type'] = handle_dart_excel.get_test_type(s[0])
    d['exercise'] = handle_dart_excel.get_exercise(s[0])
    d['info'] = str(s)
    d['dataset'] = 'zwijsen'
    d['correct_available'] = False
    
    
