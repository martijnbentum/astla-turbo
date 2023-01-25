from texts.models import School, Pupil, Session, Word
import random
import time


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

def split_on_pupils(train=.4,dev=.1,test=.5,pupils = None):
    if pupils == None:pupils= Pupil.objects.all()
    ptrain,pdev,ptest = split_data(train,dev,test,pupils)
    train, dev, test = [], [], []
    for p in ptrain:
        train.extend( list(p.session_set.all()) ) 
    for p in pdev:
        dev.extend( list(p.session_set.all()) ) 
    for p in ptest:
        test.extend( list(p.session_set.all()) ) 
    return train, dev, test


        
    
    
    

def delta(start):
    return time.time() -start
