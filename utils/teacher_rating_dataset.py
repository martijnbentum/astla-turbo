from texts.models import Session
import random
import numpy as np
from sklearn.metrics import classification_report, matthews_corrcoef
import pickle
from matplotlib import pyplot as plt



def get_header():
    h = 'word,correct,session_id,pupil_id,teacher_id,core_set'
    h += ',word_id,other_ratings_continuous,other_ratings_majority_rules'
    h += ',other_ratings_tied,all_ratings_continous'
    h += ',all_ratings_majority_rules'
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
    output = [get_header()]
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
    h= get_header()
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
        all_hyp, all_gt = [], [] 
        for line in temp:
            word_id = line[i_word]
            if word_id not in word_ids:
                hyp.append(line[i_correct])
                gt.append(int(line[i_mr]))
                word_ids.append(word_id)
            all_hyp.append(line[i_correct])
            all_gt.append(int(line[i_mr]))
        d[nratings]['hyp'] = _convert(hyp)
        d[nratings]['gt'] = gt
        d[nratings]['all_hyp'] = _convert(all_hyp)
        d[nratings]['all_gt'] = all_gt
    return d
            

def classification_report(output = None):
    if not output: output = make_dataset(False)
    d = convert_dataset(output)

def compute_mcc_for_51_teachers(d = None):
    if not d: d = convert_dataset()
    mccs = []
    for teacher_id in d[51].keys():
        if not 'tid' in teacher_id: continue
        temp = d[51][teacher_id]
        gt, hyp = temp['gt'], temp['hyp']
        mcc = matthews_corrcoef(gt, hyp)
        mccs.append(mcc)
    return mccs
    


class Data:
    def __init__(self, output = None, n_ratings = None):
        if not output: output = make_dataset(False)
        self.header = output[0]
        self._data_raw = output[1:]
        self._set_info()
        if n_ratings: self._select_data_with_n_raters(n_ratings)


    def __repr__(self):
        return 'Data: ' + str(len(self.data))

    def _set_info(self):
        self.data = []
        for line in self._data_raw:
            self.data.append(Dataline(line, self.header))
            
    def _select_data_with_n_raters(self, n_ratings):
        output = []
        for line in self.data:
            if line.n_ratings == n_ratings: output.append(line)
        self.data = output

    def make_dataset_with_bootstrapped_other_ratings(self,n_other_raters,
        apply_majority_rules = True, select_teacher_id = None):
        hyp, gt = [], []
        for line in self.data:
            if select_teacher_id and select_teacher_id != line.teacher_id:
                # print(select_teacher_id,'skipping',line.teacher_id)
                continue
            hyp.append( line.correct )
            gt.append( line.bootstrap_other_ratings(n_other_raters,
                apply_majority_rules) )
        return gt, hyp

    def compute_bootstrapped_mccs(self,n_other_raters, n_bootstraps = 1000,
        select_teacher_id = None):
        mccs = []
        check = []
        for _ in range(n_bootstraps):
            gt, hyp = self.make_dataset_with_bootstrapped_other_ratings(
                n_other_raters, select_teacher_id = select_teacher_id)
            mccs.append( matthews_corrcoef(gt, hyp) )
            check.append([gt,hyp])
        return mccs, check

    @property
    def teacher_ids(self):
        output = []
        for line in self.data:
            tid = line.teacher_id
            if tid not in output: output.append(tid)
        return output
    
        
            

class Dataline:
    def __init__(self,line, header):
        self.header = header
        self.line = line
        self._set_info()

    def __repr__(self):
        return 'Dataline: ' + self.word + ' ' + str(self.n_ratings)
    
    def _set_info(self):
        for name, value in zip(self.header,self.line):
            if name == 'correct':
                value = 1 if value == 'TRUE' else 0
            if name == 'n_ratings': value = int(value)
            if name == 'other_ratings_str':
                name = 'other_ratings'
                value = list(map(int,value.split(',')))
            setattr(self,name,value)

    def bootstrap_other_ratings(self, n_other_raters, 
        apply_majority_rules = True):
        other_ratings = random.choices(self.other_ratings,
            k = n_other_raters)
        if apply_majority_rules:
            return majority_rules(other_ratings)
        return other_ratings
            
        

        
def majority_rules(values):
    value = np.mean(values)
    if value >= .5: return 1
    return 0
        
    
def bootstrap_classification(output = None, n_bootstraps = 100,
    filename = '../bootstrap_classification.pickle', save = False): 
    data = Data(output, 51)
    print(len(data.data), 'ndatalines')
    teacher_ids = data.teacher_ids + [None]
    n_other_raters = list(range(1,52))
    d = {}
    for n_raters in n_other_raters:
        d[n_raters] = {}
        for tid in teacher_ids:
            d[n_raters][tid] = {}
            mccs, check = data.compute_bootstrapped_mccs(n_raters,
                n_bootstraps = n_bootstraps, select_teacher_id = tid)
            d[n_raters][tid]['mccs'] = mccs 
            d[n_raters][tid]['check'] = check
            d[n_raters][tid]['mean_mccs'] = np.mean(mccs)
            if tid == None:
                print('n raters:',n_raters,'teacher_id',tid,'mccs',
                    np.mean(mccs))
    if save:
        save_pickle(d, filename)
    return d

def load_bootstrap_classification(
    filename = '../bootstrap_classification.pickle'):
    with open(filename, 'rb') as fin:
        d = pickle.load(fin)
    return d

def save_pickle(obj, filename):
    with open(filename,'wb') as fout:
        pickle.dump(obj,fout)

def get_mccs_boostrap_stats(d = None, teacher_id = None, plot = True):
    if not d: d = load_bootstrap_classification()
    minimum, maximum, mean, median = [],[],[],[]
    for n_raters, value in d.items():
        mccs = value[teacher_id]['mccs']
        minimum.append(np.min(mccs))
        maximum.append(np.max(mccs))
        median.append(np.median(mccs))
        mean.append(np.mean(mccs))
    if plot: 
        plot_bootstrapped_mccs(minimum,maximum,median,mean, teacher_id)
    return minimum, maximum,median, mean

def plot_bootstrapped_mccs(minimum, maximum, median, mean, teacher_id):
    plt.clf()
    nraters = list(range(1,52))
    plt.plot(nraters,minimum)
    plt.plot(nraters,maximum )
    plt.plot(nraters,median )
    plt.plot(nraters,mean )
    plt.legend(['minimum','maximum','median','mean'])
    plt.xlabel('n raters (bootstrapped - sampled with replacement)')
    plt.ylabel("Matthew's correlation coefficient")
    if teacher_id:title = 'teacher_id: ' + teacher_id
    else: title = 'All teachers'
    plt.title(title)
    plt.grid()
    plt.show()

def plot_bootstrapped_mccs_per_teacher(d):
    plt.clf()
    nraters = list(range(1,52))
    teacher_ids = d[1].keys()
    for teacher_id in teacher_ids:
        if teacher_id == None: continue
        minimum, maximum, median, mean = get_mccs_boostrap_stats(d,
            teacher_id, plot = False)
        plt.plot(nraters,median, alpha = 0.4, color = 'blue' ,lw =1)
    plt.xlabel('n raters (bootstrapped - sampled with replacement)')
    plt.ylabel("Matthew's correlation coefficient")
    plt.title('scores per teacher')
    plt.grid()
    plt.show()

def good_bad_teacher_ids(d):
    temp = d[40]
    teacher_ids = temp.keys()
    good, bad = [],[]
    for teacher_id in teacher_ids:
        v = np.median(temp[teacher_id]['mccs'])
        if v < .4: bad.append(teacher_id)
        else: good.append(teacher_id)
    return good, bad
    
    
    

            
