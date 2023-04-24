def speaker_textgrid_to_words(jasmin_recording):
    '''load words from jasmin corpus in the database.'''
    from texts.models import Jasmin_word
    t = jasmin_recording.load_awd()
    child = jasmin_recording.child
    identifier = child_identifier(child, t)
    intervals = t[identifier]
    words = []
    for i, interval in enumerate(intervals):
        text = interval.text.strip('.?!')
        if text in ['',' ','_','ggg','xxx']: continue
        try:
            words.append(Jasmin_word.objects.get(recording=jasmin_recording,
                child = child, awd_word_tier_index = i))
            continue
        except Jasmin_word.DoesNotExist: pass
        d = {}
        d['awd_word'] = text
        d['awd_word_phoneme'] = t[identifier +'_FON'][i].text
        d['awd_word_phonemes'] = str(get_phonemes(t,identifier,interval))
        d['special_word'] = '*' in text
        d['eos'] = '.' in text or '?' in text
        d['awd_word_tier_index'] = i
        d['start_time'] = interval.xmin
        d['end_time'] = interval.xmax
        d['recording'] = jasmin_recording
        d['child'] = child
        w = Jasmin_word(**d)
        w.save()
        words.append(w)
    return words

def child_identifier(child, textgrid):
    if child: return child.identifier
    for key in textgrid.keys():
        if '_' not in key: return key
    m = 'expected identifier in list without _'
    raise ValueError(textgrid.keys(),m)
    

def get_phonemes(t,identifier,interval):
    '''get the phonemes associated with a given word.
    '''
    s1, e1 = interval.xmin, interval.xmax
    segment_intervals = t[identifier + '_SEG']
    overlapping_intervals = []
    for phoneme in segment_intervals:
        if phoneme.text == '': continue
        s2, e2 = phoneme.xmin, phoneme.xmax
        if overlap(s1,e1,s2,e2, strict = True):
            overlapping_intervals.append(phoneme)
    phoneme_dict = intervals_to_dict(overlapping_intervals)
    return phoneme_dict

def overlap(s1,e1,s2,e2, strict = False):
    '''checks whether start end point 1 overlaps with start end point 2
    with strict checking interval 2 should fall within interval 1
    '''
    if not strict:
        if s1 < s2 and e1 < s2: return False 
        if s1 > e2 and e1 > e2: return False
        return True
    if s1 <= s2 and e1 <= s2: return False
    if s1 >= e2 and e1 >= e2: return False
    return True

def intervals_to_dict(intervals):
    '''return a number dict with numbers for keys and
    tab separated line with text\tstart_time\tend_time for value
    '''
    d = {}
    for i, iv in enumerate(intervals):
        d[i] = '\t'.join(map(str,[iv.text,iv.xmin,iv.xmax]))
    return d


def words_to_duration(words):
    return sum([word.duration for word in words])

def _check_end_of_phrase(word, phrase, end_on_eos, maximum_duration):
    '''check whether a phrase should end
    adds word to phrase if the phrase does not end
    '''
    to_long, end = False, False
    if phrase: duration = word.end_time - phrase[0].start_time
    else: duration = 0
    if maximum_duration: to_long = duration > maximum_duration
    exclude_word = word.special_word
    if exclude_word: end = True
    elif to_long: end = True
    else: phrase.append(word)
    if end_on_eos and word.eos: end = True
    return end, duration, to_long, exclude_word

def _add_phrase_to_phrases(phrase,phrases, minimum_duration):
    '''whether to add the phrase to the phrases list based on 
    minimum_duration'''
    if not phrase: return
    phrase_duration = words_to_duration(phrase)
    if minimum_duration:
        if phrase_duration >= minimum_duration:
            phrases.append(phrase)
    else: phrases.append(phrase)
        
    
def words_to_phrases(words, end_on_eos = True, minimum_duration = None,
    maximum_duration = None):
    '''split word list into phrases based on several criteria
    see _check_end_Of_phrase.
    end_on_eos      whether to end a phrases because end of sentence token
    minimum...      whether to exclude phrases shorther than this value
    maximum...      whether to exclude phrases longer than this value
    (if min/max duration is None don't exclude based on duration)
    '''
    phrases, phrase = [], []
    for i, word in enumerate(words):
        end, duration, to_long, exclude_word = _check_end_of_phrase(
            word, phrase, end_on_eos, maximum_duration)
        if i == len(words) -1: end = True
        if end:
            _add_phrase_to_phrases(phrase, phrases, minimum_duration)
            phrase = []
            if to_long and not exclude_word:
                phrase.append(word)
                duration = word.duration
            to_long = False
    return phrases
