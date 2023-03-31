from utils import split_data
from utils.levenshtein_classifier import get_whisper_levenshtein_ratio
from utils.egemap_classifier import get_egemap_features
from utils.confidence_classifier import get_whisper_confidence

from scipy import stats
from matplotlib import pyplot as plt
import numpy as np
from sklearn.metrics import classification_report
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

train,dev,test = split_data.get_train_dev_test_words() 
'''
X_train = np.array([word.levenshtein_ratio for word in train])
X_test= np.array([word.levenshtein_ratio for word in test])
X_train = np.array([get_whisper_levenshtein_ratio(w) for w in train])
X_test= np.array([get_whisper_levenshtein_ratio(w) for w in test])
y_train = np.array([word.correct for word in train])
y_test= np.array([word.correct for word in test])
#return X_train, X_test, y_train, y_test
'''


def wav2vec_levenshtein_ratio():
    X_train = np.array([word.levenshtein_ratio for word in train])
    X_test= np.array([word.levenshtein_ratio for word in test])
    return make_2d(X_train, X_test)

def whisper_levenshtein_ratio():
    X_train = np.array([get_whisper_levenshtein_ratio(w) for w in train])
    X_test= np.array([get_whisper_levenshtein_ratio(w) for w in test])
    return make_2d(X_train, X_test)

def egemap_features():
    X_train = np.array([get_egemap_features(w) for w in train])
    X_test= np.array([get_egemap_features(w) for w in test])
    return X_train, X_test

def whisper_confidence():
    X_train = np.array([get_whisper_confidence(w) for w in train])
    X_test= np.array([get_whisper_confidence(w) for w in test])
    return make_2d(X_train, X_test)

def word_duration():
    X_train = np.array([w.duration for w in train])
    X_test= np.array([w.duration for w in test])
    return make_2d(X_train, X_test)

def speech_rate():
    X_train = np.array([_compute_speech_rate(w) for w in train])
    X_test= np.array([_compute_speech_rate(w) for w in test])
    return make_2d(X_train, X_test)

def _compute_speech_rate(word):
    if word.duration <= 0.0:return 0.0
    return len(word.word) * 1/word.duration

def make_2d(train,test):
    return train.reshape(-1,1), test.reshape(-1,1)


def make_combined_features_dataset():
    lr1_train, lr1_test = wav2vec_levenshtein_ratio()
    lr2_train, lr2_test = whisper_levenshtein_ratio()
    em_train, em_test = egemap_features()
    wc_train, wc_test = whisper_confidence()
    wd_train, wd_test = word_duration()
    sr_train, sr_test = speech_rate()
    X_train = np.concatenate([em_train,lr1_train,wc_train,wd_train,sr_train],
        axis = 1)
    X_test = np.concatenate([em_test,lr1_test,wc_test,wd_test,sr_test],
        axis = 1)
    y_train = np.array([word.correct for word in train])
    y_test= np.array([word.correct for word in test])
    return X_train, X_test, y_train, y_test
    

class CombinedFeaturesSVCClassifier:
    '''classifier to predict correct incorrect label based on the
    the combined for a given word 
    '''
    def __init__(self, train = True):
        self._get_data()
        if train: self.train()

    def _get_data(self):
        '''get data for validation and density computation.'''
        X_train, X_test, y_train, y_test =make_combined_features_dataset()
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

    def train(self):
        self.clf= make_pipeline(StandardScaler(),SVC(gamma='auto'))
        self.clf.fit(self.X_train,self.y_train)

    def predict(self,features):
        '''predict correct incorrect label based on confidence.'''
        return self.clf.predict(features)
        
    def classification_report(self):
        self.hyp = self.predict(self.X_test)
        self.report = classification_report(self.y_test, self.hyp)
        print(self.report)


class CombinedFeaturesMLPClassifier:
    '''classifier to predict correct incorrect label based on the
    the combined for a given word 
    '''
    def __init__(self, train = True):
        self._get_data()
        if train: self.train()

    def _get_data(self):
        '''get data for validation and density computation.'''
        X_train, X_test, y_train, y_test =make_combined_features_dataset()
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

    def train(self):
        self.clf= make_pipeline(StandardScaler(),MLPClassifier(
        early_stopping = True, max_iter=400, hidden_layer_sizes=(50,)))
        self.clf.fit(self.X_train,self.y_train)

    def predict(self,features):
        '''predict correct incorrect label based on confidence.'''
        return self.clf.predict(features)
        
    def classification_report(self):
        self.hyp = self.predict(self.X_test)
        self.report = classification_report(self.y_test, self.hyp)
        print(self.report)

