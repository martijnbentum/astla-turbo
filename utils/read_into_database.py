from . import handle_dart_excel
from django.db import IntegrityError
from texts.models import Session, Pupil, Teacher, School, Word
import Levenshtein


def load_all_simple(data = None):
    '''load pupils, teachers and schools in the database.'''
    if not data:
        _, header, data = handle_dart_excel.open_dart_excel()
    pupils = handle_dart_excel.get_all_pupils(data)
    [load_pupil(pupil) for pupil in pupils]
    teachers = handle_dart_excel.get_all_teachers(data)
    [load_teacher(teacher) for teacher in teachers]
    schools = handle_dart_excel.get_all_schools(data)
    [load_school(school) for school in schools]

def load_all_dart_sessions(data = None):
    if not data:
        _, header, data = handle_dart_excel.open_dart_excel()
    urls = handle_dart_excel.audio_urls(data)
    for url in urls:
        load_dart_session(url,data)

def _load_simple(identifier, model):
    try: instance = model.objects.get(identifier = identifier)
    except model.DoesNotExist:
        print('creating',model, identifier)
        instance = model(identifier = identifier)
        instance.save()
    else:print(model,instance,'already exists')
    return instance

def load_pupil(identifier):
    return _load_simple(identifier, Pupil)

def load_teacher(identifier):
    return _load_simple(identifier, Teacher)

def load_school(identifier):
    return _load_simple(identifier, School)

def load_dart_session(url,data):
    d = {}
    s = handle_dart_excel.url_to_session_list(url,data)
    try: instance = Session.objects.get(audio_url = url)
    except Session.DoesNotExist:
        print('creating a session',url)
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
        d['audio_filename'] = url.split('/')[-1]
        d['identifier'] = url
        d['duration'] = handle_dart_excel.get_duration(s[0])
        d['list_id'] = handle_dart_excel.get_list_id(s[0])
        d['set_id'] = handle_dart_excel.get_set_id(s[0])
        d['page_id'] = handle_dart_excel.get_page_id(s[0])
        d['condition'] = handle_dart_excel.get_condition(s[0])
        d['test_type'] = handle_dart_excel.get_test_type(s[0])
        d['exercise'] = handle_dart_excel.get_exercise(s[0])
        d['info'] = str(s)
        d['dataset'] = 'dart'
        d['correct_available'] = True
        instance = Session(**d)
        instance.save()
    else:print(instance, 'already exists')
    return instance
  

def to_word_instance(session,index,word, gt_aligned_word, 
    hyp_aligned_word, char_start_end_indices):
    cl = session.correct_list.split(',')
    d ={}
    d['word'] = word
    d['index'] = index 
    d['audio_url'] = session.identifier
    d['audio_filename'] = session.audio_filename
    d['correct'] = int(cl[index])
    d['gt_aligned_word']= gt_aligned_word
    d['hyp_aligned_word'] = hyp_aligned_word
    d['span'] = ','.join(map(str,char_start_end_indices ))
    d['session'] = session
    distance =Levenshtein.distance(gt_aligned_word,hyp_aligned_word)
    ratio =Levenshtein.ratio(gt_aligned_word,hyp_aligned_word)
    d['levenshtein_distance'] = distance
    d['levenshtein_ratio'] = ratio
    w = Word(**d)
    try:w.save()
    except IntegrityError: print(word, 'already exists doing nothing')
    else: print(word, 'saved to database')


def load_zwijsen_session(audio_filename):
    o = audio_filename_to_session_info(audio_filename)
    identifier, audio, info_dict, prompt, word_list = o
    wl = word_list
    d = {}
    s = handle_dart_excel.url_to_session_list(url,data)
    try: instance = Session.objects.get(audio_url = url)
    except Session.DoesNotExist:
        print('creating a session', identifier)
        d['nwords'] = len(wl) 
        d['word_list'] = ','.join(wl)
        pupil_id = info_dict['pupil_id']
        d['pupil'] = Pupil.objects.get(identifier = pupil_id)
        d['audio_filename'] = audio_filename.split('/')[-1]
        d['identifier'] = identifier
        d['duration'] = audio.seconds
        d['list_id'] = handle_dart_excel.get_list_id(s[0])
        d['set_id'] = handle_dart_excel.get_set_id(s[0])
        d['page_id'] = handle_dart_excel.get_page_id(s[0])
        d['condition'] = handle_dart_excel.get_condition(s[0])
        d['test_type'] = handle_dart_excel.get_test_type(s[0])
        d['exercise'] = handle_dart_excel.get_exercise(s[0])
        d['info'] = str(info_dict)
        d['dataset'] = 'zwijsen'
        d['correct_available'] = False
        instance = Session(**d)
        instance.save()
    else:print(instance, 'already exists')
    return instance

