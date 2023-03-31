from utils import split_data
from scipy import stats
from matplotlib import pyplot as plt
import numpy as np
from sklearn.metrics import classification_report

def make_confidence_dataset(confidence_type = 'wispher'):
    train,dev,test = split_data.get_train_dev_test_words() 
    train = train + dev
    if confidence_type== 'whisper':
        X_train = np.array([get_whisper_confidence(w) for w in train])
        X_test= np.array([get_whisper_confidence(w) for w in test])
    if confidence_type== 'kaldi':
        X_train = np.array([get_kaldi_confidence(w) for w in train])
        X_test= np.array([get_kaldi_confidence(w) for w in test])
    else:raise ValueError(confidence_type,'unknown')
    y_train = np.array([word.correct for word in train])
    y_test= np.array([word.correct for word in test])
    return X_train, X_test, y_train, y_test

def get_whisper_confidence(word):
    if not word.whisper_info: return 0
    return eval(word.whisper_info)['confidence']

def get_kaldi_confidence(word):
    return word.kaldi_fd_confidence


def compute_confidence_density_for_correct_incorrect_words(cw,icw,
    confidence_type = 'whisper'):
    correct_words, incorrect_words = cw, icw
    if confidence_type == 'whisper':
        correct = [get_whisper_confidence(w) for w in correct_words]
        incorrect = [get_whisper_confidence(w) for w in incorrect_words]
    elif confidence_type == 'kaldi':
        correct = [get_kaldi_confidence(w) for w in correct_words]
        incorrect = [get_kaldi_confidence(w) for w in incorrect_words]
    else:raise ValueError(confidence_type,'unknown')
    density_correct = stats.kde.gaussian_kde(correct)
    density_incorrect = stats.kde.gaussian_kde(incorrect)
    return density_correct, density_incorrect

def plot_density_correct_incorrect_words(save = False, 
    confidence_type = 'whisper'):
    o = split_data.get_train_correct_incorrect_words()
    correct_words, incorrect_words = o
    o = compute_confidence_density_for_correct_incorrect_words(
        correct_words, incorrect_words, confidence_type= confidence_type)
    density_correct, density_incorrect = o
    x = np.arange(0.,1.,.01)
    plt.ion()
    plt.clf()
    plt.plot(x,density_correct(x))
    plt.plot(x,density_incorrect(x))
    plt.legend(['correct','incorrect'])
    title='density plot of confidence for correct and correct words'
    plt.xlabel('confidence')
    plt.ylabel('density')
    plt.title(title)
    plt.show()
    if save:
        f = '../' + confidence_type + 'confidence_density_plot.png'
        plt.savefig(f)

class ConfidenceClassifier:
    '''classifier to predict correct incorrect label based on the
    the confidence for a given word from whisper or kaldi
    '''
    def __init__(self, confidence_type = 'whisper'):
        self.confidence_type = confidence_type 
        self._get_data()
        self._get_densities()

    def _get_data(self):
        '''get data for validation and density computation.'''
        X_train, X_test, y_train, y_test =make_confidence_dataset(
            self.confidence_type)
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        cw, icw = split_data.get_train_correct_incorrect_words()
        self.correct_words = cw
        self.incorrect_words = icw

    def _get_densities(self):
        '''compute density for correct and incorrect words.'''
        o = compute_confidence_density_for_correct_incorrect_words(
            self.correct_words, self.incorrect_words,self.confidence_type)
        self.density_correct, self.density_incorrect = o

    def predict(self,confidence):
        '''predict correct incorrect label based on confidence.'''
        if type(confidence) == float:
            confidence= np.array(confidence)
        output_correct = self.density_correct(confidence)
        output_incorrect = self.density_incorrect(confidence)
        output = np.array([output_incorrect,output_correct])
        return np.argmax(output,0)
        
    def classification_report(self):
        self.hyp = self.predict(self.X_test)
        self.report = classification_report(self.y_test, self.hyp)
        print(self.report)
