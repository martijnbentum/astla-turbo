from texts.models import School, Pupil, Session, Word
import glob
import os
import random
import shutil
import time

from . import descriptive_stats


def get_train_correct_incorrect_words():
    train,dev,test = get_train_dev_test_words() 
    train = train + dev
    correct_words = [w for w in train if w.correct]
    incorrect_words = [w for w in train if not w.correct]
    return correct_words, incorrect_words

def _compute_number_of_items_per_set(train,dev,test,nsamples):
    assert train + dev + test - 1 < 0.0001
    ntrain = int(nsamples * train)
    ndev = int(nsamples * dev)
    ntest = int(nsamples * test)
    total = ntrain + ndev + ntest
    ndev += nsamples - total
    assert ntrain + ndev + ntest == nsamples
    print(ntrain, ndev, ntest, nsamples)
    return ntrain, ndev, ntest

def _exclude_from_list(exclude_list, all_list):
    output_list = []
    for line in all_list:
        if line in exclude_list: continue
        output_list.append(line)
    return output_list
        
def _check_split(train,dev,test, items):
    assert len(train) + len(dev) + len(test) == len(items)
    all_items = train + dev + test
    assert len(set(all_items)) == len(items)


def split_data(train = .4, dev = .1, test = .5, items = None):
    if items == None:items = Session.objects.all()
    if type(items) != list: items = list(items)
    nitems = len(items)
    o =  _compute_number_of_items_per_set(train,dev,test,nitems)
    ntrain, ndev, ntest = o
    sample_items = items[:]
    random.shuffle(sample_items)
    train = sample_items[:ntrain]
    dev = sample_items[ntrain:ntrain+ndev]
    test = sample_items[ntrain+ndev:]
    _check_split(train,dev,test, items)
    return train, dev, test

def split_on_sessions(train=.4,dev=.1,test=.5,sessions = None):
    if sessions == None:sessions = Session.objects.all()
    return split_data(train,dev,test,sessions)

def _split_on_pupil_test_type(train_perc,dev_perc,test_perc,pupils):
    d = make_test_type_pupil_dict(pupils)
    ptrain, pdev, ptest = [], [], []
    for k, v in d.items():
        print(k,len(v))
        train, dev, test = split_data(train_perc,dev_perc,test_perc,v)
        ptrain.extend(train)
        pdev.extend(dev)
        ptest.extend(test)
    return ptrain, pdev, ptest
    
    

def split_on_pupils(train=.4,dev=.1,test=.5,pupils = None, save = False,
    split_on_test_type = True):
    if pupils == None:pupils= Pupil.objects.all()
    if split_on_test_type: 
        ptrain, pdev, ptest = _split_on_pupil_test_type(train,dev,test,pupils)
    else:
        ptrain,pdev,ptest = split_data(train,dev,test,pupils)
    train, dev, test = [], [], []
    for p in ptrain:
        train.extend( list(p.session_set.exclude(all_incorrect = True)) ) 
    descriptive_stats.describe_session_set(train,'train')
    descriptive_stats.describe_pupil_set(ptrain,'train')
    print('-'*80)
    for p in pdev:
        dev.extend( list(p.session_set.exclude(all_incorrect=True)) ) 
    descriptive_stats.describe_session_set(dev,'dev')
    descriptive_stats.describe_pupil_set(pdev,'dev')
    print('-'*80)
    for p in ptest:
        test.extend( list(p.session_set.exclude(all_incorrect=True)) ) 
    descriptive_stats.describe_session_set(test,'test')
    descriptive_stats.describe_pupil_set(ptest,'test')
    d = {'sessions':{'train':train,'dev':dev,'test':test},
        'pupils':{'train':ptrain, 'dev':pdev,'test':ptest}}
    if save: save_split(d)
    return d
    
def save_split(split_dict):
    o = []
    print('saving split on sessions')
    for split in split_dict['sessions'].keys():
        for session in split_dict['sessions'][split]:
            session.train_dev_test = split
            session.save()
            o.append(str(session.pk) + '\t' + split)
    print('saving split on pupils')
    for split in split_dict['pupils'].keys():
        for pupil in split_dict['pupils'][split]:
            pupil.train_dev_test = split
            pupil.save()
    print('saving split on words')
    _save_split_on_words()
    print('saving split in text file')
    with open('../train_dev_test_split_dart.txt','w') as fout:
        fout.write('\n'.join(o))


def _save_split_on_words():
    words = Word.objects.filter(dataset = 'dart')
    for word in words:
        word.train_dev_test = word.session.train_dev_test
        word.save()


def get_train_dev_test_words():
    train, dev, test = [], [], []
    words = Word.objects.filter(dataset = 'dart')
    for w in words:
        if w.train_dev_test == '':continue
        if w.train_dev_test == 'train':train.append(w)
        if w.train_dev_test == 'dev':dev.append(w)
        if w.train_dev_test == 'test':test.append(w)
    return train,dev,test
    

        
def make_test_type_pupil_dict(pupils = None):
    if not pupils: pupils = Pupil.objects.all()
    d = {}
    for pupil in pupils:
        k = ','.join(pupil.test_types)
        if k not in d.keys(): d[k] = [pupil]
        else: d[k].append(pupil)
    return d


def _add_exclude(sessions,d):
    '''add sessions to exclude list to ensure they are not selected again'''
    f = '../exclude_list_sessions_sa.txt'
    o = []
    for s in sessions:
        o.append( str(s.pk) + '\t' + d + '\t' + s.audio_filename)
    with open(f,'a') as fout:
        fout.write('\n'.join(o)+'\n')

def _overwrite_exclude(d):
    '''if a folder is overwritten also overwrite the exclude files'''
    f = '../exclude_list_sessions_sa.txt'
    audio_filenames = glob.glob(d+'*.mp3')
    with open(f,'r') as fin:
        t = fin.read().split('\n')
    o = []
    for line in t:
        if not line:continue
        found = False
        for af in audio_filenames:
            af = af.split('/')[-1]
            if af in line: found = True
        print(line,found)
        if not found: o.append(line)
    if not o: o = ''
    else: o = '\n'.join(o) +'\n'
    with open(f,'w') as fout:
        fout.write(o)
        
def _generate_textgrids(d):
    '''create textgrids for all mp3 files for directory d'''
    ad = os.path.abspath(d) + '/'
    cmd = '/usr/bin/praat --run ../audio2textgrid.psc '
    cmd += ad + ' .mp3 ' + ad
    print('create praat scripts')
    print(cmd)
    os.system(cmd)
    os.system('cp ../edit_textgrid.psc ' + d)

def _make_wordlist(sessions,d):
    '''create a word list for all sessions and save it in directory d'''
    o = ['File;Words']
    for s in sessions:
        wl = s.word_list
        f = s.audio_filename
        o.append(f.split('.')[0] + ';' + wl)
    with open(d + 'word_list','w') as fout:
        fout.write('\n'.join(o))
    
def _get_exclude():
    '''get the database ids for all excluded sessions.'''
    f = '../exclude_list_sessions_sa.txt'
    if not os.path.isfile(f): return []
    with open(f) as fin:
        t = [line for line in fin.read().split('\n') if line]
    return [int(line.split('\t')[0]) for line in t]

def select_files_sa(n_files, sa_name, version = 1, overwrite = False):
    '''select a random set of sessions from the training set to be transcribed.'''
    if overwrite:
        print('should you really be overwriting?''')
        return
    if sa_name not in ['janneke','stephanie','martijn']: 
        raise ValueError('unknown sa',sa_name)
    exclude = _get_exclude()
    sessions = Session.objects.filter(train_dev_test = 'train')
    sessions = sessions.exclude(pk__in = exclude)
    sessions = random.sample(list(sessions), n_files)
    directory= '../' + sa_name + '_v' + str(version) + '/'
    dart_mp3 = '../dart_mp3/'
    if os.path.isdir(directory) and overwrite:
        _overwrite_exclude(directory)
        shutil.rmtree(directory)
    if not os.path.isdir(directory):
        os.mkdir(directory)
    else: 
        print('directory',directory,'already exists',
            ' use overwrite=true or other version != (',version,')' )
        return
    for s in sessions:
        os.system('cp ' + dart_mp3 + s.audio_filename +' ' + directory)
    _add_exclude(sessions,directory)
    _make_wordlist(sessions,directory)
    _generate_textgrids(directory)
    
    
    
    
    
    
    

def delta(start):
    return time.time() -start
