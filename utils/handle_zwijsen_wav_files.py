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
        if i in audios.keys: ok_audios[i] = audios[i]
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
            self.samples= int(t[4].strip('Duration:').split('=')[1]
            self.samples = self.samples.split('samples')[0])
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

def check_transcriptions(save = False):
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
    if save:
        with open('../zwijsen_empty_files.txt','w') as fout:
            fout.write('\n'.join(empty))
        with open('../zwijsen_text_to_transcription_dict.pkl','wb') as fout:
            pickle.dump(d)
    return empty, d

def load_text_to_transcription_dict():
    with open('../zwijsen_text_to_transcription_dict.pkl','rb') as fin:
        d = pickle.load(fin)
    return d

def load_empty_files():
    with open('../zwijsen_empty_files.txt','r') as fin:
        o = open(fin).read().split('\n')
    return o

