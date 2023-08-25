from texts.models import Session, Word
from utils import session_helper
from matplotlib import pyplot as plt

def word_to_teacher_correctness_dict(word):
    d = word.session.teacher_to_correct_list_dict
    o = {}
    for teacher_identifier, correct_list in d.items():
        o[teacher_identifier] = correct_list[word.index]
    return o
        
        
def word_duration(word):
    return word.end_time - word.start_time

def _set_all_start_end_times_words(start_index = 0):
    '''set the start and end time of each word in all sessions'''
    error = []
    for session in Session.objects.all()[start_index:]:
        print('handling:',session.pk)
        succes = _session_set_start_end_times_words(session)
        if not succes: error.append(session)
    return error

def _prepare_label_table(session):
    '''adds lines to the table with start end info for each char
    to align it with the aligned asr transcription
    the aligned asr transcription contains - to align it with the
    prompt (done with needleman wunch algorithm)
    '''
    table = session_helper.transcription_label_table(session)
    if not table: return False
    table = table.split('\n')
    asr = session.align.split('\n')[-1]
    output =[]
    j = 0
    for i,char in enumerate(asr):
        if list(set(asr[i:])) == ['-'] and j >= len(table): 
            output.append([])
            continue
        line = table[j].split('\t')
        if len(line) != 3: print([line])
        if char == '-': output.append([])
        else:
            output.append(list(map(float,[line[1], line[2]])))
            j += 1
    return output

def _adjust_indices(start_index, end_index, word):
    '''only chars in the asr transcription have time information
    if a asr word starts or ends with the filler label -
    the start or end index needs to be adjusted
    if there are only - than no time information is available
    '''
    # print(111,start_index, end_index, word.hyp_aligned_word)
    for char in word.hyp_aligned_word:
        if char != '-': break
        start_index += 1
    for char in word.hyp_aligned_word[::-1]:
        if char != '-': break
        end_index -= 1
    # print(333,start_index, end_index, word.hyp_aligned_word)
    if start_index >= end_index: return False, False
    return start_index, end_index
        

def _set_no_word_time_information_available(session):
    '''set word_time_information_available field on session and word
    to false to indicate there is no time information availabel
    for the session and each word
    '''
    session.word_time_information_available = False
    for word in session.word_set.all():
        word.word_time_information_available = False
        word.save()
    session.save()
    
def _session_set_start_end_times_words(session):
    '''set the start and end times for each word in a session
    based on the char timestamps and the aligned prompts and 
    asr transcription
    '''
    table = _prepare_label_table(session)
    if not table: 
        _set_no_word_time_information_available(session)
        return False
    words = session.word_set.all()
    for i,word in enumerate(words):
        start_index, end_index = list(map(int, word.span.split(',')))
        end_index -= 1
        start_index,end_index=_adjust_indices(start_index,end_index,word)
        print(i,word.span, start_index, end_index, len(table))
        print('--->',table[start_index],'---',table[end_index])
        if start_index == end_index == False:
            word.word_time_information_available = False
        else: 
            word.start_time = table[start_index][0]
            word.end_time = table[end_index][1]
            word.word_time_information_available = True
        word.audio_filename = session.audio_filename
        word.save()
    session.word_time_information_available = True
    session.save()
    return True
        

def plot_hist_words():
    words = Word.objects.filter(word_time_information_available=True)
    words = words.filter(duration__lt = 3)
    durs = [x.duration for x in words]
    plt.ion()
    plt.clf()
    plt.hist(durs,30)
    plt.title('histogram of word durations (< 3 seconds)')
    plt.xlabel('seconds')
    plt.ylabel('counts')
    plt.savefig('../histo_gram_of_word_durations')
    

def add_whisper_align_to_word(word):
    if not word.whisper_info: return
    d = eval(word.whisper_info)
    start, end = d['char_start_end_indices']
    wa = word.session.whisper_align.split('\n')[1][start:end]
    word.whisper_hyp_aligned = wa

def add_whisper_disfluency_align_to_word(word):
    if not word.whisper_dis_info: return
    d = eval(word.whisper_dis_info)
    start, end = d['char_start_end_indices']
    wa = word.session.whisper_dis_align.split('\n')[1][start:end]
    word.whisper_dis_hyp_aligned = wa
    
def add_whisper_hyp_alignments(word):
    add_whisper_align_to_word(word)
    add_whisper_disfluency_align_to_word(word)

def print_aligned_text(word):
    d = eval(word.whisper_dis_info)
    start, end = d['char_start_end_indices']
    start = start -10
    if start < 0: start = 0
    end = end + 10
    gt, hyp = word.session.whisper_align.split('\n')
    print(gt[start:end])
    print(hyp[start:end])



    
        

