from texts.models import Session

directory =  '/vol/tensusers5/mbentum/dart_wav/'

def make_text_dataset():
    s = Session.objects.all()
    o = []
    for x in s:
        f = directory + x.audio_filename.replace('.mp3','.wav')
        wl = x.word_list
        cl = x.correct_list
        pk = str(x.pk)
        url = x.identifier
        line = '\t'.join([pk,wl,cl,f,url])
        o.append(line)
    with open('text_dataset_dart.txt','w') as fout:
        fout.write('\n'.join(o))
    return o
        
        
