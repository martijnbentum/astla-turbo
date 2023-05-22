if not __name__ == '__main__':
    from . import session_helper
import Levenshtein
from . import needleman_wunch
import unittest
    
def _add_whisper_dis_align_to_session(session, version = 'whisper_dis_json'):
    _add_whisper_align_to_session(session,version)

def _add_whisper_align_to_session(session, version = 'whisper_json'):
    print('version:',version, session)
    if not json_available(session, version): return False
    gt = ground_truth(session)
    hyp, indices = whisper_words_to_string_indices(session,version)
    if version == 'whisper_dis_json': attr = 'whisper_dis_align'
    else: attr= 'whisper_align'
    setattr(session,attr,needleman_wunch.nw(gt,hyp))
    session.save()

def extract_all_whisper_words_dis_version(session, remove_doubles = True):
    temp = extract_all_whisper_words(session, 'whisper_dis_json')
    words, disfluencies = [], []
    for d in temp:
        if d['text'] == '[*]': disfluencies.append(d)
        else: words.append(d)
    if remove_doubles: words = remove_double_words(words)
    return words, disfluencies

def extract_all_whisper_words(session, version = 'whisper_json'):
    words = []
    if not json_available(session, version): return False
    o = getattr(session,version)()
    if not o:return False
    if not 'segments' in o.keys(): []
    for segment in o['segments']:
        if not 'words' in segment.keys(): continue
        words.extend(segment['words'])
    return words

def whisper_words_to_string_indices(session, version = 'whisper_json'):
    if not json_available(session, version): return False, False
    if version == 'whisper_dis_json':
        whisper_words, _ = extract_all_whisper_words_dis_version(session)
    else:
        whisper_words = extract_all_whisper_words(session, version)
    words = []
    word_start_end_indices = []
    start, end = 0,0
    for word in whisper_words:
        words.append(word['text'])
        word_length = len(word['text'])
        end = start + word_length
        word_start_end_indices.append([start,end])
        start = end + 1 
    t = ' '.join(words)
    return t, word_start_end_indices
    

def match_whisper_words_and_word_list_dis_version(session, save = False):
    return match_whisper_words_and_word_list(session, save,
    version = 'whisper_dis_json')

def json_available(session, version = 'whisper_json'):
    o = getattr(session,version)()
    if not o:
        print('cannot find whisper output')
        return False
    return True

def match_whisper_words_and_word_list(session, save = False, 
    version = 'whisper_json'):
    if not json_available(session, version): return False
    if version == 'whisper_dis_json':
        whisper_words, _ = extract_all_whisper_words_dis_version(session)
    else:
        whisper_words = extract_all_whisper_words(session, version)
    if not whisper_words:
        print('could not extract whisper words')
        return
    print('version:',version, session)
    t,i = whisper_words_to_string_indices(session, version)
    words = session_helper.to_words(session)
    if version == 'whisper_dis_json': attr = 'whisper_dis_align'
    else: attr = 'whisper_align'
    gt, hyp = getattr(session,attr).split('\n')
    indices = find_indices(gt)
    hyp_bar = replace_char_at_index(hyp, indices)
    gt_aligned_words = gt.split(' ')
    hyp_aligned_words = hyp_bar.split('|')
    start_end_indices = to_start_end_indices(indices,gt)
    matches = []
    for index, word in enumerate(words):
        gt_aligned_word = gt_aligned_words[index]
        hyp_aligned_word = hyp_aligned_words[index]
        char_start_end_indices = start_end_indices[index]
        w_words,ww_indices =find_whisper_words(char_start_end_indices,hyp,i, 
            word,whisper_words)
        print(word)
        print(w_words)
        w_word, w_word_index = prune_whisper_words(w_words, word, ww_indices)
        print(index,w_word,word, '<---', char_start_end_indices)
        if not w_word:
            print('could not find match',w_word)
            continue
        w_word = add_info(w_word,word, char_start_end_indices,
            ww_indices, w_word_index)
        db_word = session.word_set.get(index = index)
        if save:
            if version == 'whisper_dis_json': attr = 'whisper_dis_info'
            else: attr = 'whisper_info'
            print('saving to attr', attr)
            setattr(db_word, attr, str(w_word) ) 
            db_word.save()
        matches.append([db_word,w_word])
        print('')
    return matches

def add_info(w_word,wl_word, char_start_end_indices, 
        whisper_word_indices, w_word_index):
    ratio= Levenshtein.ratio(wl_word, w_word['text'])
    w_word['levenshtein_ratio'] =ratio
    w_word['char_start_end_indices'] = char_start_end_indices 
    w_word['whisper_word_indices'] = whisper_word_indices
    w_word['selected_whisper_word_index'] = w_word_index
    return w_word

    
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

def find_whisper_words(char_start_end_indices, hyp_text,
    whisper_word_indices_set, wl_word, whisper_words, verbose = False):
    '''find the whisper word(s) that correpond to a word list word.
    char_start_end_indices      the start and end indices of the
                                whisper string corresponding to word 
                                list word.
    whisper_text                all whisper words concatenated
    whisper_word_indices_set    start end indices of the whisper words
                                in the whisper string
    wl_word                     the current word in the word list
    whisper_words               dict with whisper word info
    '''
    start, end = char_start_end_indices
    #needleman wunch adds - to align texts, shifting indices to text
    #without -
    delta_start = hyp_text[:start].count('-')
    delta_end = hyp_text[:end].count('-')
    start -= delta_start 
    end -= delta_end
    o = match_start_end_indices(whisper_word_indices_set,start, end)
    if verbose: print(o)
    whisper_word_indices = [x[0] for x in o]
    w_words = [whisper_words[i] for i in whisper_word_indices]
    return w_words, whisper_word_indices

def prune_whisper_words(w_words, wl_word, whisper_word_indices):
    ratios = []
    smallest = 10**6
    selected = []
    selected_index = []
    for index, w_word in zip(whisper_word_indices, w_words):
        w = w_word['text']
        distance = Levenshtein.distance(wl_word, w)
        if distance < smallest: 
            selected = w_word
            selected_index = index
            smallest = distance
    return selected, selected_index
        
            
    
    # ratio =Levenshtein.ratio(gt_aligned_word,hyp_aligned_word)
    

def ground_truth(session):
    return session.word_list.replace(',', ' ').lower()

def has_highest_confidence(whisper_words, word):
    confidence = word['confidence']
    highest = True
    for w in whisper_words:
        if w['text'] != word['text']: continue
        if w['confidence'] > confidence: highest = False
    return highest

def remove_double_words(whisper_words):
    output = []
    words = [x['text'] for x in whisper_words]
    for i,word in enumerate(whisper_words):
        t = word['text']
        if words.count(t) == 1: output.append(word) 
        elif has_highest_confidence(whisper_words,word): output.append(word)
    return output

def match_start_end_indices(indices_set, start,end):
    '''find the whisper word index (or indices) corresponding to a 
    word list word
    '''
    o = []
    for i,se in enumerate(indices_set):
        s, e = se
        if start <= s and end > s: o.append([i,se,start,end])
        elif start < e and end > s: o.append([i,se, start,end])
    return o

class TestMatchIndices(unittest.TestCase):
    '''check the match start end indices function for finding the
    the whisper word indices for a word from the prompt word list.'''

    def test_match_exact(self): 
        indices = test_indices
        o = match_start_end_indices(indices,0,2)
        self.assertEqual(len(o), 1, 'output should be len 1')
        whisper_word_index = o[0][0]
        self.assertEqual(whisper_word_index, 0, 'should be index 0')
        o = match_start_end_indices(indices,101,106)
        self.assertEqual(len(o), 1, 'output should be len 1')
        whisper_word_index = o[0][0]
        self.assertEqual(whisper_word_index, 22, 'should be index 22')
        o = match_start_end_indices(indices,138,142)
        self.assertEqual(len(o), 1, 'output should be len 1')
        whisper_word_index = o[0][0]
        self.assertEqual(whisper_word_index, 28,'should be index 28')

    def test_multiple_match(self):
        indices = test_indices
        o = match_start_end_indices(indices,0,5)
        self.assertEqual(len(o), 2, 'output should be len 2')
        whisper_word_indices = [x[0] for x in o]
        self.assertEqual(whisper_word_indices, [0,1], 'should be index 0,1')
        o = match_start_end_indices(indices,1,5)
        self.assertEqual(len(o), 2, 'output should be len 2')
        whisper_word_indices = [x[0] for x in o]
        self.assertEqual(whisper_word_indices, [0,1], 'should be index 0,1')
        o = match_start_end_indices(indices,2,5)
        self.assertEqual(len(o), 1, 'output should be len 1')
        whisper_word_index = o[0][0]
        self.assertEqual(whisper_word_index, 1, 'should be index 1')
        o = match_start_end_indices(indices,47,81)
        self.assertEqual(len(o), 7, 'output should be len 7')
        whisper_word_indices = [x[0] for x in o]
        self.assertEqual(whisper_word_indices, [10, 11, 12, 13, 14, 15, 16], 
            'should be index 10, 11, 12, 13, 14, 15, 16')

    def test_no_match(self):
        indices = test_indices
        o = match_start_end_indices(indices,2,3)
        self.assertEqual(len(o), 0, 'output should be len 0')
        self.assertEqual(o, [], 'should be index []')

        
   
test_indices = [
    [0, 2],
    [3, 6],
    [7, 11],
    [12, 16],
    [17, 21],
    [22, 28],
    [29, 33],
    [34, 35],
    [36, 41],
    [42, 44],
    [45, 51],
    [52, 56],
    [57, 61],
    [62, 68],
    [69, 71],
    [72, 77],
    [78, 80],
    [81, 86],
    [87, 89],
    [90, 93],
    [94, 97],
    [98, 100],
    [101, 106],
    [107, 112],
    [113, 120],
    [121, 126],
    [127, 131],
    [132, 137],
    [138, 142]
]

if __name__ == '__main__':
    unittest.main()





