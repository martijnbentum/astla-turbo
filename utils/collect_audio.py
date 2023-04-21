import glob
import os
from . import handle_dart_excel 
from texts.models import Jasmin_recording

# mp3 files downloaded her
# /vol/tensusers5/mbentum/dart_mp3

# converted to wav and stored here
# /vol/tensusers5/mbentum/dart_wav

#wav2vec transcriptions stored here
# /vol/tensusers5/mbentum/dart_transcriptions



def collect_audio(urls = None, goal_dir = '../dart_mp3/'):
    if not urls: urls = handle_dart_excel.audio_urls()
    if not goal_dir or not os.path.isdir(goal_dir): goal_dir = ''
    else: goal_dir = ' -P ' + goal_dir
    n_mp3_before = len(glob.glob(goal_dir + '*.mp3'))
    for url in urls:
        print('collecting:',url)
        os.system('wget' + goal_dir + ' ' + url)
    n_mp3_after= len(glob.glob(goal_dir + '*.mp3'))
    print('added',n_mp3_after - n_mp3_before,'mp3 files')
    print('n mp3 files',n_mp3_after, 'currently in:', goal_dir)



def collect_jasmin_audio():
    jr = Jasmin_recording.objects.all()
    goal_dir = '../jasmin_wav/'
    for recording in jr:
        f = recording.audio_filename
        output_name = goal_dir + f.split('/')[-1]
        if not os.path.isfile(output_name):
            print('converting to mono and copying to',goal_dir)
            os.system('sox ' + f + ' ' + output_name + ' channels 1')

        

