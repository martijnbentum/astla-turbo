from texts.models import Session
import numpy as np
from sklearn.metrics import classification_report



def header():
    h = 'word,correct,session_id,pupil_id,teacher_id,core_set'
    h += ',word_id,other_ratings_continuous,other_ratings_majority_rules'
    h += ',other_ratings_tied,all_ratings_continous,all_ratings_majority_rules'
    h += ',all_ratings_tied,n_ratings,other_ratings_str'
    h = h.split(',')
    return h

def has_multiple_teacher_ratings(session):
    return len(session.teacher_to_correct_list_dict.keys()) > 1

def handle_teacher_ratings(words,ratings,session_id,pupil_id,teacher_id,
    core_set, teacher_to_correct_list_dict):
    output = []
    indices = range(len(words))
    for word_index, word, rating in zip(indices,words,ratings):
        other_ratings = _get_other_ratings(teacher_id,
            teacher_to_correct_list_dict, word_index)
        other_ratings_continuous = str(
            _multiple_ratings_to_continous(other_ratings))
        other_ratings_mr = _multiple_ratings_to_majority_rules(other_ratings)
        other_ratings_mr = str(other_ratings_mr).upper()
        other_ratings_tied = _are_ratings_tied(other_ratings)
        other_ratings_str = ','.join(map(str,other_ratings))
        all_ratings = [rating] + other_ratings
        ratings_continuous = str(
            _multiple_ratings_to_continous(all_ratings))
        ratings_mr = _multiple_ratings_to_majority_rules(all_ratings)
        ratings_mr = str(ratings_mr).upper()
        ratings_tied = _are_ratings_tied(all_ratings)
        correct = str(rating == 1).upper()
        word_id = word + '_' + session_id
        n_ratings = str(len(teacher_to_correct_list_dict.keys()))
        output.append([word,correct,session_id,pupil_id,
            str(teacher_id),core_set, word_id,other_ratings_continuous,
                other_ratings_mr, other_ratings_tied,
                ratings_continuous,ratings_mr,ratings_tied, n_ratings,
                other_ratings_str])
    return output

def _multiple_ratings_to_continous(ratings):
    return np.mean(ratings)

def _multiple_ratings_to_majority_rules(ratings):
    v = _multiple_ratings_to_continous(ratings)
    if v == 0.5: return 1
    else: return round(v)

def _are_ratings_tied(ratings):
    v = _multiple_ratings_to_continous(ratings)
    tied = v == 0.5
    return str(tied).upper()

def _get_other_ratings(teacher_id,teacher_to_correct_list_dict, word_index):
    other_ratings = []
    for other_id, ratings in teacher_to_correct_list_dict.items():
        if other_id == teacher_id: continue
        other_ratings.append(ratings[word_index])
    return other_ratings
        
    
def handle_session(session):
    if not has_multiple_teacher_ratings: return False
    output = []
    s = session
    core_set = str(s.n_correctors == 51).upper()
    session_id = s.audio_filename.split('.')[0]
    pupil_id = s.pupil.identifier
    words = s.word_list.split(',')
    for teacher_id, ratings in s.teacher_to_correct_list_dict.items():
        output.extend(
            handle_teacher_ratings(words,ratings,session_id,pupil_id,
                teacher_id, core_set, s.teacher_to_correct_list_dict)
        )
    return output

def make_dataset(save = False):
    s = Session.objects.all()
    output = [header()]
    for x in s:
        if not has_multiple_teacher_ratings(x): continue
        output.extend(handle_session(x))
    s = '\n'.join(['\t'.join(line) for line in output])
    if save:
        with open('../teacher_rating_dataset.tsv','w') as fout:
            fout.write(s)
    return output

def _convert(values):
    output = []
    for item in values:
        if item == 'TRUE': output.append(1)
        if item == 'FALSE': output.append(0)
    return output
    
def convert_dataset(output = None):
    if not output: output = make_dataset(False)
    output = [line for line in output[1:] if line]
    h= header()
    i_rating = h.index('n_ratings')
    i_teacher = h.index('teacher_id')
    i_word= h.index('word_id')
    i_correct = h.index('correct')
    i_mr = h.index('other_ratings_majority_rules')
    d = {}
    for nratings in [2,3,51]:
        temp = [line for line in output if int(line[i_rating]) == nratings]
        teacher_ids = list(set([line[i_teacher] for line in temp]))
        d[nratings] ={}
        for tid in teacher_ids:
            d[nratings]['tid_'+tid] = {}
            hyp = [line[i_correct] for line in temp if line[i_teacher] == tid]
            gt = [int(line[i_mr]) for line in temp if line[i_teacher] == tid]
            d[nratings]['tid_'+tid]['hyp'] = _convert(hyp) 
            d[nratings]['tid_'+tid]['gt'] = gt 
        word_ids,hyp, gt= [], [],[]#list(set([line[i_word] for line in temp]))
        for line in temp:
            word_id = line[i_word]
            if word_id not in word_ids:
                hyp.append(line[i_correct])
                gt.append(int(line[i_mr]))
                word_ids.append(word_id)
        d[nratings]['hyp'] = _convert(hyp)
        d[nratings]['gt'] = gt
    return d
            

def classification_report(output = None):
    if not output: output = make_dataset(False)
    d = convert_dataset(output)
    
    
        

    
