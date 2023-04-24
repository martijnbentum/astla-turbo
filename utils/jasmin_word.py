def speaker_textgrid_to_words(jasmin_recording):
    from texts.models import Jasmin_word
    t = jasmin_recording.load_awd()
    child = jasmin_recording.child
    intervals = t[child.identifier]
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
        d['awd_word_phoneme'] = t[child.identifier +'_FON'][i].text
        d['awd_word_phonemes'] = str(get_phonemes(t,child,interval))
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


def get_phonemes(t,child,interval):
    s1, e1 = interval.xmin, interval.xmax
    segment_intervals = t[child.identifier + '_SEG']
    overlapping_intervals = []
    for phoneme in segment_intervals:
        if phoneme.text == '': continue
        s2, e2 = phoneme.xmin, phoneme.xmax
        if overlap(s1,e1,s2,e2, strict = True):
            overlapping_intervals.append(phoneme)
    phoneme_dict = intervals_to_dict(overlapping_intervals)
    return phoneme_dict

def overlap(s1,e1,s2,e2, strict = False):
    if not strict:
        if s1 < s2 and e1 < s2: return False 
        if s1 > e2 and e1 > e2: return False
        return True
    if s1 <= s2 and e1 <= s2: return False
    if s1 >= e2 and e1 >= e2: return False
    return True

def intervals_to_dict(intervals):
    d = {}
    for i, iv in enumerate(intervals):
        d[i] = '\t'.join(map(str,[iv.text,iv.xmin,iv.xmax]))
    return d

    

