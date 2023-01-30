from collections import Counter
from texts.models import School, Pupil, Session, Word
from matplotlib import pyplot as plt
import numpy as np


def n_sesions_per_pupil(verbose = True):
    p = Pupil.objects.all()
    counts = [x.session_set.all().count() for x in p]
    cp = Counter(counts)
    if verbose: print(cp.most_common())
    return cp, counts

def n_sessions_per_shool(verbose = True):
    s = School.objects.all()
    counts = [x.sesion_set.all().count() for x in s]
    sp = Counter(counts)
    if verbose: print(sp.most_common())
    return sp, counts

def n_pupils_per_shool(verbose = True):
    s = School.objects.all()
    counts = []
    for x in s:
        c = [session.pupil.identifier for session in x.session_set.all()]
        counts.append(len(set(c)))
    sp = Counter(counter)
    if verbose: print(sp.most_common())
    return sp, counts


def nseconds_per_pupil(verbose = False):
    p = Pupil.objects.all()
    counts = [x.duration_sessions for x in p]
    sp = Counter(counts)
    if verbose: print(sp.most_common())
    return sp, counts

def nseconds_per_session(sessions = None,verbose = False):
    if not sessions: sessions = Session.objects.all()
    counts = [x.duration for x in sessions]
    ss = Counter(counts)
    if verbose: print(ss.most_common())
    return ss, counts

def nmistakes_per_session(sessions = None,verbose= True):
    if not sessions: sessions = Session.objects.all()
    counts = [x.nwords - x.ncorrect for x in sessions]
    ms = Counter(counts)
    if verbose: print(ms.most_common())
    return ms, counts

def home_language_upils(pupils = None):
    if not pupils:pupils = Pupil.objects.all()
    only_dutch = [x for x in pupils if x.only_dutch == True]
    also_dutch = [x for x in pupils if x.also_dutch == True]
    no_dutch = [x for x in pupils if x.no_dutch == True]
    unk = [x for x in pupils if x.only_dutch == None]
    return only_dutch, also_dutch, no_dutch, unk
    
def home_reading_level_pupils(pupils = None):
    if not pupils:pupils = Pupil.objects.all()
    zon, maan, ster, other, unk = [],[],[],[],[]
    for pupil in pupils:
        if pupil.reading_level == 'zon': zon.append(pupil)
        elif pupil.reading_level == 'maan': maan.append(pupil)
        elif pupil.reading_level == 'ster': ster.append(pupil)
        elif pupil.reading_level == 'onbekend': unk.append(pupil)
        else:  other.append(pupil)
    return zon, maan, ster, other, unk

def current_age_in_months_counts(pupils = None):
    if not pupils:pupils = Pupil.objects.all()
    counts = [x.current_age_in_months for x in pupils 
        if x.current_age_in_months]
    cam = Counter(counts)
    return cam, counts

def gender_pupils(pupils = None):
    if not pupils:pupils = Pupil.objects.all()
    male, female, unk = [],[],[]
    for pupil in pupils:
        if pupil.gender== 'male': male.append(pupil)
        elif pupil.gender== 'female': female.append(pupil)
        else:  unk.append(pupil)
    return male, female, unk


def describe_pupil_set(pupils = None, name = ''):
    if not pupils:pupils = Pupil.objects.all()
    print('\npupil set description, name:',name)
    print('n pupils: ', len(pupils))
    print('\nhome language')
    only_dutch,also_dutch,no_dutch,unk = home_language_upils(pupils)
    print('only_dutch:',len(only_dutch))
    print('also_dutch:',len(also_dutch))
    print('no_dutch:',len(no_dutch))
    print('unk:',len(unk))
    print('\nreading level')
    zon, maan, ster, other, unk = home_reading_level_pupils(pupils)
    print('zon (highest):',len(zon))
    print('maan (middle):',len(maan))
    print('ster (lowest):',len(ster))
    print('other:',len(other))
    print('unk:',len(unk))
    print('\ncurrent age in months')
    _ , counts = current_age_in_months_counts(pupils)
    print('avg age in months (std,min,max): ', round(np.mean(counts),2),
        '(',round(np.std(counts),2),',',np.min(counts),
        ',',np.max(counts),')')
    print('\ngender')
    male, female, unk = gender_pupils(pupils)
    print('male:',len(male))
    print('female:',len(female))
    print('unk:',len(unk))
    


def describe_session_set(sessions, name = ''):
    print('\nsession set description, name:',name)
    print('n sessions: ', len(sessions))
    _,second_counts = nseconds_per_session(sessions, False)
    print('total duration (hours): ',round(sum(second_counts) /3600,2))
    print('avg sec per session (std): ', round(np.mean(second_counts),2),
        '(',round(np.std(second_counts),2),')')
    _,mistake_counts = nmistakes_per_session(sessions, False)
    nwords = sum([x.nwords for x in sessions])
    print('total mistakes: ',sum(mistake_counts), '   ',
        round(sum(mistake_counts) / nwords *100,2),'%' )
    print('avg mistakes per session (std): ',
        round(np.mean(mistake_counts),2),
        '(',round(np.std(mistake_counts),2),')')
    print('total nwords: ', nwords, '(24 per session)\n')

    
def plot_histo_nseconds_per_pupil(counts = None):
    if counts == None:_, counts = nseconds_per_pupil()
    plt.ion()
    plt.clf()
    plt.hist(counts,30)
    plt.title('n seconds of material per pupil')
    plt.xlabel('n seconds')
    plt.ylabel('n pupils')
    plt.show()

def plot_histo_nseconds_per_session(counts = None):
    if count == None: _, counts = nseconds_per_session()
    plt.ion()
    plt.clf()
    plt.hist(counts,30)
    plt.title('n seconds of material per session')
    plt.xlabel('n seconds')
    plt.ylabel('n sessions')
    plt.show()

def plot_histo_nmistakes_per_sesion(counts = None):
    if counts == None:_, counts = nmistakes_per_session()
    plt.ion()
    plt.clf()
    plt.hist(counts,25)
    plt.title('n mistakes per session')
    plt.xlabel('n mistakes')
    plt.ylabel('n sessions')
    plt.show()
    

