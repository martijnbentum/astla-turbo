import glob
import os
import re
import subprocess

f = '../zwijsen_audio_info.txt'
audio_info = dict([l.split('\t') for l in open(f).read().split('\n') if l])

def find_bad_audio_files(audios = None):
    if not audios: audios = make_audios()
    bads = []
    for audio in audios.values():
        #very low bit rate indicates a problem
        if not 'k' in audio.bit_rate: bads.append(audio) 
    return bads

def move_bad_audio_files(audios = None):
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
            self.samples= int(t[4].strip('Duration:').split('=')[1].split('samples')[0])
            self.file_size= t[5].split(':')[1]
            self.bit_rate = t[6].split(':')[1]
            self.sample_encoding = t[7].split(':')[1]
            self.seconds = self.samples / self.sample_rate
            self.comp = self.path.split('/')[-3]
            self.region= self.path.split('/')[-2]

    def __repr__(self):
        m = 'Audio: ' + self.file_id + ' | ' + self.duration + ' | ' + str(self.channels)
        m += ' | ' + self.comp + ' | ' + self.region
        return m


    def _set_info(self):
        self.ok =True
        try: self.info = audio_info[self.file_id]
        except:
            print(file_id,'not found in audio_info')
            self.ok = False
        if 'Duration' not in self.info:self.ok = False

def make_time(seconds):
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
