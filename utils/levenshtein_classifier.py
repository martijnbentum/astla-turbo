from utils import split_data
from scipy import stats
from matplotlib import pyplot as plt
import numpy as np

def make_levenshtein_dataset():
    train,dev,test = split_data.get_train_dev_test_words() 
    train = train + dev
    X_train = np.array([word.levenshtein_ratio for word in train])
    y_train = np.array([word.correct for word in train])
    X_test= np.array([word.levenshtein_ratio for word in test])
    y_test= np.array([word.correct for word in test])
    return X_train, X_test, y_train, y_test

def get_train_correct_incorrect_words():
    train,dev,test = split_data.get_train_dev_test_words() 
    train = train + dev
    correct_words = [w for w in train if w.correct]
    incorrect_words = [w for w in train if not w.correct]
    return correct_words, incorrect_words

def compute_levenshtein_ratio_density_for_correct_incorrect_words(cw,icw):
    correct_words, incorrect_words = cw, icw
    correct = [w.levenshtein_ratio for w in correct_words]
    incorrect = [w.levenshtein_ratio for w in incorrect_words]
    density_correct = stats.kde.gaussian_kde(correct)
    density_incorrect = stats.kde.gaussian_kde(incorrect)
    return density_correct, density_incorrect


def plot_density_correct_incorrect_words(save = False):
    correct_words, incorrect_words = get_train_correct_incorrect_words()
    o = compute_levenshtein_ratio_density_for_correct_incorrect_words(
        correct_words, incorrect_words)
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
    if save:
        plt.savefig('../levenshtein_ratio_density_plot.png')


class RatioClassifier:
    '''classifier to predict correct incorrect label based on the
    match between prompt and ASR transcription as measured with 
    levenshtein ratio.
    '''
    def __init__(self):
        self._get_data()
        self._get_densities()

    def _get_data(self):
        '''get data for validation and density computation.'''
        X_train, X_test, y_train, y_test =make_levenshtein_dataset()
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
            self.correct_words, self.incorrect_words)
        self.density_correct, self.density_incorrect = o

    def predict(self,levenshtein_ratio):
        '''predict correct incorrect label based on levenshtein ratio.'''
        if type(levenshtein_ratio) == float:
            levenshtein_ratio = np.array(levenshtein_ratio)
        output_correct = self.density_correct(levenshtein_ratio)
        output_incorrect = self.density_incorrect(levenshtein_ratio)
        output = np.array([output_incorrect,output_correct])
        return np.argmax(output,0)
        
            
        

    
    
    

    
