import os
from . import needleman_wunch
from . import read_into_database
from matplotlib import pyplot as plt
    
   

def ground_truth(session):
    return session.word_list.replace(',', ' ').lower()

def to_words(session):
    return session.word_list.split(',')

def transcription_txt(session, directory = '../dart_transcriptions/'):
    filename = directory + session.audio_filename.replace('.mp3','.txt')
    if os.path.isfile(filename):
        return open(filename).read()
    else:
        print('could not find transcription', filename)

def transcription_table(session, directory = '../dart_transcriptions/'):
    filename = directory + session.audio_filename.replace('.mp3','.table')
    if os.path.isfile(filename):
        return open(filename).read()
    else:
        print('could not find transcription', filename)

def transcription_label_table(session,
    directory='../dart_label_timestamps/'):
    filename = directory + session.audio_filename.replace('.mp3','.table')
    if os.path.isfile(filename):
        return open(filename).read()
    else:
        print('could not find transcription', filename)

def align(session):
    gt = ground_truth(session)
    hyp = transcription_txt(session).replace('[UNK]','[')
    gt , hyp= needleman_wunch.nw(gt,hyp).split('\n')
    print('gt:  ' + gt)
    print('hyp: ' + hyp)
    return gt, hyp


def to_word_instances(session):
    words = to_words(session)
    gt, hyp = session.align.split('\n')
    indices = find_indices(gt)
    hyp_bar = replace_char_at_index(hyp, indices)
    gt_aligned_words = gt.split(' ')
    hyp_aligned_words = hyp_bar.split('|')
    start_end_indices = to_start_end_indices(indices,gt)
    for index, word in enumerate(words):
        gt_aligned_word = gt_aligned_words[index]
        hyp_aligned_word = hyp_aligned_words[index]
        char_start_end_indices = start_end_indices[index]
        read_into_database.to_word_instance(session, index, word, 
            gt_aligned_word,hyp_aligned_word, char_start_end_indices)
    return words, gt_aligned_words,hyp_aligned_words
    


    
def to_start_end_indices(indices,gt):
    indices.append(len(gt))
    output = []
    start = 0
    for index in indices:
        output.append([start, index])
        start = index + 1
    return output


def find_indices(text, char = ' '):
    output = []
    for i,c in enumerate(text):
        if c == char: output.append(i)
    return output

def replace_char_at_index(text, indices, char= '|'):
    t = list(text)
    for index in indices:
        t[index] = char
    return ''.join(t)

def perc_correct_teacher_wav2vec_session(session, threshold = .6):
    correct_list = []
    for word in session.word_set.all():
        if word.levenshtein_ratio >= threshold:
            correct_list.append(1)
        else: correct_list.append(0)
    if len(correct_list) != 24: 
        raise ValueError(len(correct_list),'unexpected')
    teacher_correct_list = list(map(int,session.correct_list.split(',')))
    teacher_perc = sum(teacher_correct_list) / len(teacher_correct_list)
    wav2vec_perc = sum(correct_list) / len(correct_list)
    return teacher_perc, wav2vec_perc, teacher_correct_list, correct_list

def compute_perc_teacher_wav2vec_sessions(sessions = None, threshold = .6):
    from texts.models import Session
    if not sessions:
        sessions = Session.objects.filter(all_incorrect = False, 
            train_dev_test = 'train')
    teacher_percs, wav2vec_percs = [], []
    for session in sessions:
        tp,wp,_,_ = perc_correct_teacher_wav2vec_session(session,threshold)
        teacher_percs.append(tp)
        wav2vec_percs.append(wp)
    return teacher_percs, wav2vec_percs


def plot_teacher_wav2vec_session_comparison(teacher_percs = None, 
    wav2vec_percs = None,sessions = None, threshold =.6):
    if teacher_percs == None: 
        teacher_percs, wav2vec_percs = compute_perc_teacher_wav2vec_sessions(
            sessions, threshold)
    plt.clf()
    plt.ion()
    plt.scatter(teacher_percs,wav2vec_percs,alpha=.1)
    plt.title('Percentage correct words')
    plt.xlabel('rated by teachers')
    plt.ylabel('rated by wav2vec 2.0, levenshtein ratio')
    plt.show()


        
        
