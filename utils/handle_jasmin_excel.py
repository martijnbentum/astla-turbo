import glob
from openpyxl import load_workbook
import subprocess

'''
Jasmin is a corpus of child speech

comp p 
------
Human Machine Interaction - dialogue. 
Asked open ended questions (stereo recordings).

comp q
------
Read speech (mono recordings).
Native::  Selected texts from nine different reading levels from books 
belonging to the Veilig Leren Lezen.
Non-Native:: Selected AVI texts (same as Native)

groups
------
1	Native 7-11 year olds
2	Native 12-16 year olds (Special secondary school for children learning dutch)
3	Non-native children 7-16 year olds

dialect regions
---------------
N1a - c	West Dutch (Core)
N2a - f	Transitional Areas
N3a - e	Northern Dutch
N4a - b	Southern Dutch
'''

jasmin_directory = '/vol/bigdata/corpora/JASMIN/'
jasmin_filenames = None

def get_all_jasmin_filenames():
    '''get all jasmin filenames based on jasmin_directory.'''
    global jasmin_filenames
    if not jasmin_filenames:
        jasmin_filenames = glob.glob(jasmin_directory + '**',recursive=True)
    return jasmin_filenames

def open_jasmin_excel():
    '''load an excel file'''
    wb = load_workbook('../jasmin_child_data_summary.xlsx')
    return wb

def _load_sheet(wb, name):
    '''load a specific sheet from an excel file 
    return a header and a list of list of data (rows in the excel file)
    '''
    ws = wb[name]
    lines = list(ws.values)
    header = lines[0]
    data = lines[1:]
    return header, data

def load_child_info(wb = None):
    '''load the child sheet with child meta data.'''
    if not wb: wb = open_jasmin_excel()
    return _load_sheet(wb, 'child-speakers')

def load_recording_info(wb = None):
    '''load the recording sheet with recording meta data.'''
    if not wb: wb = open_jasmin_excel()
    return _load_sheet(wb, 'child-recordings')

def make_audio_filename(file_id):
    '''create the audio file based on file id 
    and the collected jasmin filenames.
    '''
    global jasmin_filenames
    if not jasmin_filenames: _ = get_all_jasmin_filenames()
    for f in jasmin_filenames:
        if f.endswith('.wav') and file_id in f: return f
    raise ValueError('could not find audio file',file_id)
    
def make_awd_filename(file_id):
    '''create the awd file based on file id 
    and the collected jasmin filenames.
    this is a textgrid file with forced aligned transcriptions.
    '''
    global jasmin_filenames
    if not jasmin_filenames: _ = get_all_jasmin_filenames()
    for f in jasmin_filenames:
        if f.endswith('.awd') and file_id in f: return f
    raise ValueError('could not find awd file',file_id)

def make_child_dict(line):
    '''create a dictionary to load metadata into the data base.'''
    d = {}
    d['identifier'] = line[0]
    d['residence_place'] = line[1]
    gender = 'male' if line[2] == 'M' else 'female'
    d['gender'] = gender
    d['age'] = int(line[3])
    d['birth_place'] = line[4]
    d['group'] = int(line[5])
    d['home_language1'] = line[6]
    d['home_language2'] = line[7]
    d['educational_place'] = line[8]
    d['dialect_region'] = line[9]
    d['dialect_region'] = line[9]
    d['info'] = str(line[:12])
    return d

def make_recording_dict(line):
    '''create a dictionary to load metadata into the data base.'''
    child_id = line[1]
    d = {}
    d['identifier'] = line[0]
    f = make_audio_filename(line[0])
    d['audio_filename'] = f
    d['awd_filename'] = make_awd_filename(line[0])
    d['component'] = line[2]
    d['group'] = int(line[3])
    d['reading_level'] = line[10]
    duration, sample_rate, nchannels = get_audio_info(f)
    d['duration'] = duration
    d['sample_rate'] = sample_rate
    d['nchannels'] = nchannels
    d['info'] = str(line[:12])
    return d, child_id

def sox_info(filename):
    '''run sox and collect audio file information.'''
    o = subprocess.run(['sox','--i',filename],stdout=subprocess.PIPE)
    return o.stdout.decode('utf-8')

def clock_to_duration_in_seconds(t):
    '''map str representation to seconds.'''
    hours, minutes, seconds = t.split(':')
    s = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
    return s

def get_audio_info(filename):
    '''return number of channels, sample rate and duration for an audio file.'''
    x = sox_info(filename).split('\n')
    nchannels = int(x[2].split(': ')[-1])
    sample_rate = int(x[3].split(': ')[-1])
    t = x[5].split(': ')[-1].split(' =')[0]
    duration = clock_to_duration_in_seconds(t)
    return duration, sample_rate, nchannels
