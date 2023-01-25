from collections import Counter
from texts.models import School, Pupil, Session, Word
from matplotlib import pyplot as plt


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
    counts = [x.duration for x in s]
    ss = Counter(counts)
    if verbose: print(ss.most_common())
    return ss, counts

def nmistakes_per_session(sessions = None,verbose= True):
    if not sessions: sessions = Session.objects.all()
    counts = [x.nwords - x.ncorrect for x in sessions]
    ms = Counter(counts)
    if verbose: print(ms.most_common())
    return ms, counts


    
def plot_histo_nseconds_per_pupil():
    _, counts = nseconds_per_pupil()
    plt.ion()
    plt.clf()
    plt.hist(counts,30)
    plt.title('n seconds of material per pupil')
    plt.xlabel('n seconds')
    plt.ylabel('n pupils')
    plt.show()

def plot_histo_nseconds_per_session():
    _, counts = nseconds_per_session()
    plt.ion()
    plt.clf()
    plt.hist(counts,30)
    plt.title('n seconds of material per session')
    plt.xlabel('n seconds')
    plt.ylabel('n sessions')
    plt.show()

def plot_histo_nmistakes_per_sesion():
    _, counts = nmistakes_per_session()
    plt.ion()
    plt.clf()
    plt.hist(counts,25)
    plt.title('n mistakes per session')
    plt.xlabel('n mistakes')
    plt.ylabel('n sessions')
    plt.show()
    

