if not __name__ == '__main__':
    from . import session_helper
else: 
    import unittest
import Levenshtein
    

def _add_whisper_align_to_session(session):
    o = session.whisper_json()
    if not o:
        print('cannot find whisper output')
        return
    gt = ground_truth(session)
    whisper_words = whisper_helper.extract_all_words(o)
    hyp, indices = whisper_helper.whisper_words_to_string(whisper_words)
    session.whisper_align = needleman_wunch.nw(gt,hyp)
    session.save()

def extract_all_whisper_words(session):
    words = []
    o = session.whisper_json()
    for segment in o['segments']:
        words.extend(segment['words'])
    return words

def whisper_words_to_string_indices(session):
    whisper_words = extract_all_whisper_words(session)
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
    

def match_whisper_words_and_word_list(session):
    whisper_words = extract_all_whisper_words(session)
    t,i = whisper_words_to_string_indices(session)
    words = session_helper.to_words(session)
    gt, hyp = session.whisper_align.split('\n')
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
        w_words =find_whisper_words(char_start_end_indices,hyp,i, word,
            whisper_words)
        w_word = prune_whisper_words(w_words, word)
        w_word = add_levenshtein_ratio(w_word,word)
        matches.append([session.word_set.get(index = index),w_word])
    return matches

def add_levenshtein_ratio(w_word,wl_word):
    ratio= Levenshtein.ratio(wl_word, w_word['text'])
    w_word['levenshtein_ratio'] =ratio
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
    return w_words

def prune_whisper_words(w_words, wl_word):
    ratios = []
    smallest = 10**6
    selected = []
    for w_word in w_words:
        w = w_word['text']
        distance = Levenshtein.distance(wl_word, w)
        if distance < smallest: 
            selected = w_word
            smallest = distance
    return selected
        
            
    
    ratio =Levenshtein.ratio(gt_aligned_word,hyp_aligned_word)
    


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





