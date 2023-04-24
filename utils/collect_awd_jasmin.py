from texts.models import Jasmin_recording
import os


base_dir = '/vol/tensusers3/mbentum/astla/'
awd_dir = base_dir + 'jasmin_awd/'

def collect_awd():
    jr = Jasmin_recording.objects.all()
    for recording in jr:
        f = recording.awd_filename
        name = awd_dir + f.split('/')[-1]
        print('copying awd textgrid and converting to utf8',name)
        os.system('iconv -f ISO-8859-1 -t UTF-8 ' + f + ' > ' + name)

