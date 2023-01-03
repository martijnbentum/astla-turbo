import glob
from openpyxl import load_workbook
import os

def open_dart_excel():
    wb = load_workbook('../DART_test_data.xlsx')
    ws = wb['Blad1']
    lines = list(ws.values)
    header = lines[0]
    data = lines[1:]
    return wb, header, data

def audio_urls(dart_data = None):
    if not dart_data:
        wb, header, dart_data = open_dart_excel()
    output = []
    for line in dart_data:
        audio_url = line[18]
        if audio_url not in output: output.append(audio_url)
    return output

def collect_audio(urls = None, goal_dir = '../dart_mp3/'):
    if not urls: urls = audio_urls()
    if not goal_dir or not os.path.isdir(goal_dir): goal_dir = ''
    else: goal_dir = ' -P ' + goal_dir
    n_mp3_before = len(glob.glob(goal_dir + '*.mp3'))
    for url in urls:
        print('collecting:',url)
        os.system('wget' + goal_dir + ' ' + url)
    n_mp3_after= len(glob.glob(goal_dir + '*.mp3'))
    print('added',n_mp3_after - n_mp3_before,'mp3 files')
    print('n mp3 files',n_mp3_after, 'currently in:', goal_dir)



