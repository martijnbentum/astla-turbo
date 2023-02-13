from openpyxl import load_workbook
import pickle
from texts.models import Word

def _open_egemaps_excel():
    '''loads very slowly, use load_header_data for fast data loading.''' 
    wb = load_workbook('../eGeMAPS_wordlevel_results.xlsx')
    ws = wb['Sheet1']
    lines = list(ws.values)
    header = lines[0]
    data = lines[1:]
    return wb, header, data

def _save_header_data(header, data):
    with open('../egemaps_header.pickle','wb') as fout:
        pickle.dump(header,fout)
    with open('../egemaps_data.pickle','wb') as fout:
        pickle.dump(data,fout)

def load_header_data():
    with open('../egemaps_header.pickle','rb') as fin:
        header = pickle.load(fin)
    with open('../egemaps_data.pickle','rb') as fin:
        data = pickle.load(fin)
    return header, data
        
    
def get_word_index(line):
    return line[65]
def get_word_id(line):
    return line[66]
def get_file_id(line):
    return line[0]
def get_features(line):
    return line[1:63]

def line_to_info(line):
    index = get_word_index(line)
    word_id = get_word_id(line)
    file_id= get_file_id(line)
    features = get_features(line)
    return index, word_id, file_id, features

def add_features_to_word(line,  save = False, verbose = False):
    index, word_id, file_id, features = line_to_info(line)
    word = Word.objects.get(pk = word_id)
    word_file_id = word.session.audio_filename.split('.')[0]
    if word.index != index:
        if verbose: print(word, index, word.index)
        return
    if word_file_id != file_id:
        if verbose: print(word, file_id, word_file_id)
        return
    word.egemap_features = str(features)
    if save:
        word.save()
    return word
        


def add_features_to_all_words(data = None, save = False, verbose = False):
    if not data: header, data = load_header_data()
    words = []
    for line in data:
        words.append(add_features_to_word(line, save, verbose))
    return words
        
    
    
