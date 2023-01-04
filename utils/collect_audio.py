import glob
import os
from . import handle_dart_excel 


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



