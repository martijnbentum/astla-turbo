from utils import split_data
from scipy import stats
from matplotlib import pyplot as plt
import numpy as np
from sklearn.metrics import classification_report

def make_levenshtein_dataset(levenshtein_type = 'wav2vec'):
    train,dev,test = split_data.get_train_dev_test_words() 
    train = train + dev
    if levenshtein_type == 'wav2vec':
        X_train = np.array([word.levenshtein_ratio for word in train])
        X_test= np.array([word.levenshtein_ratio for word in test])
    elif levenshtein_type == 'whisper':
        X_train = np.array([get_whisper_levenshtein_ratio(w) for w in train])
        X_test= np.array([get_whisper_levenshtein_ratio(w) for w in test])
    else:raise ValueError(levenshtein_ratio,'unknown')
    y_train = np.array([word.correct for word in train])
    y_test= np.array([word.correct for word in test])
    return X_train, X_test, y_train, y_test

def get_train_correct_incorrect_words():
    train,dev,test = split_data.get_train_dev_test_words() 
    train = train + dev
    correct_words = [w for w in train if w.correct]
    incorrect_words = [w for w in train if not w.correct]
    return correct_words, incorrect_words

def get_whisper_levenshtein_ratio(word):
    if not word.whisper_info: return 0
    return eval(word.whisper_info)['levenshtein_ratio']

def compute_levenshtein_ratio_density_for_correct_incorrect_words(cw,icw,
    levenshtein_type = 'wav2vec'):
    correct_words, incorrect_words = cw, icw
    if levenshtein_type == 'wav2vec':
        correct = [w.levenshtein_ratio for w in correct_words]
        incorrect = [w.levenshtein_ratio for w in incorrect_words]
    elif levenshtein_type == 'whisper':
        correct = [get_whisper_levenshtein_ratio(w) for w in correct_words]
        incorrect = [get_whisper_levenshtein_ratio(w) for w in incorrect_words]
    else:raise ValueError(levenshtein_ratio,'unknown')
    density_correct = stats.kde.gaussian_kde(correct)
    density_incorrect = stats.kde.gaussian_kde(incorrect)
    return density_correct, density_incorrect


def plot_density_correct_incorrect_words(save = False, 
    levenshtein_type = 'wav2vec'):
    correct_words, incorrect_words = get_train_correct_incorrect_words()
    o = compute_levenshtein_ratio_density_for_correct_incorrect_words(
        correct_words, incorrect_words, levenshtein_type = levenshtein_type)
    density_correct, density_incorrect = o
    x = np.arange(0.,1.,.01)
    plt.ion()
    plt.clf()
    plt.plot(x,density_correct(x))
    plt.plot(x,density_incorrect(x))
    plt.legend(['correct','incorrect'])
    title='density plot of levenshtein ratio for correct and correct words'
    plt.xlabel('Levenshtein ratio')
    plt.ylabel('density')
    plt.title(title)
    plt.show()
    if save:
        f = '../' + levenshtein_type + 'levenshtein_ratio_density_plot.png'
        plt.savefig(f)


class RatioClassifier:
    '''classifier to predict correct incorrect label based on the
    match between prompt and ASR transcription as measured with 
    levenshtein ratio.
    '''
    def __init__(self, levenshtein_type = 'wav2vec'):
        self.levenshtein_type = levenshtein_type 
        self._get_data()
        self._get_densities()

    def _get_data(self):
        '''get data for validation and density computation.'''
        X_train, X_test, y_train, y_test =make_levenshtein_dataset(
            self.levenshtein_type)
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        cw, icw = get_train_correct_incorrect_words()
        self.correct_words = cw
        self.incorrect_words = icw

    def _get_densities(self):
        '''compute density for correct and incorrect words.'''
        o = compute_levenshtein_ratio_density_for_correct_incorrect_words(
            self.correct_words, self.incorrect_words,self.levenshtein_type)
        self.density_correct, self.density_incorrect = o

    def predict(self,levenshtein_ratio):
        '''predict correct incorrect label based on levenshtein ratio.'''
        if type(levenshtein_ratio) == float:
            levenshtein_ratio = np.array(levenshtein_ratio)
        output_correct = self.density_correct(levenshtein_ratio)
        output_incorrect = self.density_incorrect(levenshtein_ratio)
        output = np.array([output_incorrect,output_correct])
        return np.argmax(output,0)
        
    def classification_report(self):
        self.hyp = self.predict(self.X_test)
        self.report = classification_report(self.y_test, self.hyp)
        print(self.report)
            
        

    
    
    

    
