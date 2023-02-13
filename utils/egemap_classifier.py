from utils import split_data
from scipy import stats
from matplotlib import pyplot as plt
import numpy as np
from sklearn.metrics import classification_report
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

def make_egemap_features_dataset(double_incorrect_words = True):
    train,dev,test = split_data.get_train_dev_test_words() 
    train = train + dev
    X_train = np.array([get_egemap_features(w) for w in train])
    X_test= np.array([get_egemap_features(w) for w in test])
    y_train = np.array([word.correct for word in train])
    y_test= np.array([word.correct for word in test])
    if double_incorrect_words:
        X_train, y_train = resample_incorrect_words(X_train,y_train)
    return X_train, X_test, y_train, y_test

def get_egemap_features(word):
    if not word.egemap_features: return [0] * 62
    return eval(word.egemap_features)

def resample_incorrect_words(X_train, y_train):
    x_incorrect = X_train[np.argwhere(y_train == 0).ravel()]
    y_incorrect = y_train[np.argwhere(y_train == 0).ravel()]
    output_x_train = np.concatenate([X_train,x_incorrect])
    output_y_train = np.concatenate([y_train,y_incorrect])
    return output_x_train, output_y_train
    

class EgemapFeaturesSVCClassifier:
    def __init__(self, train = True):
        self._get_data()
        if train: self.train()

    def _get_data(self):
        '''get data for validation and density computation.'''
        X_train, X_test, y_train, y_test =make_egemap_features_dataset()
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        cw, icw = split_data.get_train_correct_incorrect_words()
        self.correct_words = cw
        self.incorrect_words = icw

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


class EgemapFeaturesMLPClassifier:
    '''classifier to predict correct incorrect label based on the
    the confidence for a given word from whisper or kaldi
    '''
    def __init__(self, train = True):
        self._get_data()
        if train: self.train()

    def _get_data(self):
        '''get data for validation and density computation.'''
        X_train, X_test, y_train, y_test =make_egemap_features_dataset()
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        cw, icw = split_data.get_train_correct_incorrect_words()
        self.correct_words = cw
        self.incorrect_words = icw

    def train(self):
        self.clf= make_pipeline(StandardScaler(),MLPClassifier(
        early_stopping = True, max_iter=400, hiddenlayer_sizes=(50,)))
        self.clf.fit(self.X_train,self.y_train)

    def predict(self,features):
        '''predict correct incorrect label based on confidence.'''
        return self.clf.predict(features)
        
    def classification_report(self):
        self.hyp = self.predict(self.X_test)
        self.report = classification_report(self.y_test, self.hyp)
        print(self.report)

