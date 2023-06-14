from texts.models import Session, Word
from utils import word_helper

directory =  '/vol/tensusers5/mbentum/dart_wav/'
output_dir = '../SHARED/'

def save_dataset(name, data):
    with open(output_dir + name,'w') as fout:
        fout.write('\n'.join(data))
    
def session_header():
    h = 'session_id,word_list,word_ids,pupil_id,teacher_id,correct_list'
    h += ',wav_filename,url'
    h += ',teacher_ids,train_dev_test,number_of_correctors,condition'
    h += ',test_type,exercise'
    return h.split(',')
        

def _session_to_word_ids(session):
    word_set = session.word_set.all()
    return ','.join( [str(x.pk) for x in word_set] )

def make_session_dataset( save = False):
    s = Session.objects.all()
    o = ['\t'.join(session_header())]
    for x in s:
        f = directory + x.audio_filename.replace('.mp3','.wav')
        wl = x.word_list
        wids = _session_to_word_ids(x)
        p = x.pupil.identifier
        t = x.teacher.identifier
        cl = x.correct_list
        pk = str(x.pk)
        url = x.identifier
        tids = ','.join(map(str,x.teacher_to_correct_list_dict.keys()))
        tdt = x.train_dev_test
        nc = str(x.n_correctors)
        con = x.condition
        tt = x.test_type
        e = str(x.exercise)
        line = '\t'.join([pk,wl,wids,p,t,cl,f,url,tids,tdt,nc,con,tt,e])
        o.append(line)
    if save: save_dataset('session_dart.tsv', o)
    return o

def teacher_evaluation_header():
    h = 'teacher_id,session_id,pupil_id,word_list,word_ids,correct_list'
    h += ',wav_filename,url'
    return h.split(',')
        
def _make_teacher_evaluation_line(session, teacher_id):
    t = str(teacher_id)
    pk = str(session.pk)
    p = session.pupil.identifier
    wl = session.word_list
    wids = _session_to_word_ids(session)
    cl = ','.join(map(str,session.teacher_to_correct_list_dict[teacher_id]))
    f = directory + session.audio_filename.replace('.mp3','.wav')
    url = session.identifier
    return '\t'.join([t,pk,p,wl,wids,cl,f,url])

def make_teacher_evaluation_dataset(save = False):
    s = Session.objects.all()
    o = ['\t'.join(teacher_evaluation_header())]
    for x in s:
        for teacher_id in x.teacher_to_correct_list_dict.keys():
            o.append(_make_teacher_evaluation_line(x, teacher_id))
    if save: save_dataset('teacher_evaluations.tsv', o)
    return o

    

def make_word_general_info_file(save = False):
    '''function to make word info file with start end times for words.'''
    output = ['\t'.join(make_word_general_info_header())]
    for word in Word.objects.all():
        line = list(map(str,word_to_general_info_line(word)))
        output.append('\t'.join(line))
    if save: save_dataset('word_dart.tsv',output)
    return output
    
def make_word_general_info_header():
    h = 'word_id,session_id,pupil_id,teacher_id,word_index'
    h += ',word,correct,wav_filename,teacher_ids,corrects'
    h += ',train_dev_test'
    return h.split(',')
    

def word_to_general_info_line(word):
    '''creates a a list of word information for a single word.'''
    d = word_helper.word_to_teacher_correctness_dict(word)
    o = []
    o.append(word.pk)
    o.append(word.session.pk)
    o.append(word.session.pupil.identifier)
    o.append(word.session.teacher.identifier)
    o.append(word.index)
    o.append(word.word)
    o.append(word.correct)
    o.append(directory + word.audio_filename.replace('.mp3','.wav'))
    o.append(','.join(map(str,d.keys())))
    o.append(','.join(map(str,d.values())))
    o.append(word.session.train_dev_test)
    return o

def word_to_wav2vec_line(word):
    '''creates a a list of word information for a single word.'''
    o = []
    o.append(word.pk)
    o.append(word.session.pk)
    o.append(word.index)
    o.append(word.word)
    o.append(round(word.levenshtein_ratio,3))
    o.append(word.session.audio_filename)
    o.append(word.start_time)
    o.append(word.end_time)
    o.append(round(word.duration,3))
    o.append(int(word.word_time_information_available))
    return o




        
    
