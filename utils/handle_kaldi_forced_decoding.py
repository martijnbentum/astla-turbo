from texts.models import Session

def load_kaldi_forced_decoding_output():
    t = open('../hclg_kaldi_fd_custom_output_301').read().split('\n')
    data = [line.split('\t') for line in t if line != '']
    return data


def get_file_id(line):
    return line[0]
def get_word_list(line):
    return line[1].split(',')
def get_confidence_list(line, to_float = True):
    if to_float:
        return list(map(float,line[2].split(',')))
    return line[2]
def get_mean_confidence(line):
    return float(line[3])

def get_info(line):
    file_id = get_file_id(line)
    word_list= get_word_list(line)
    confidence_list= get_confidence_list(line)
    mean_confidence = get_mean_confidence(line)
    return file_id, word_list, confidence_list, mean_confidence

def add_kaldi_confidence_to_session_and_word(line, save = False):
    file_id, word_list, confidence_list, mean_confidence = get_info(line)
    cl = get_confidence_list(line, to_float = False)
    session = Session.objects.get(identifier__contains = file_id)
    session.kaldi_fd_confidence_list = cl
    session.kaldi_fd_mean_confidence = mean_confidence
    if save: 
        session.save()
    words = session.word_set.all()
    for i in range(24):
        word = words.get(index = i)
        word.kaldi_fd_confidence = confidence_list[i]
        if save:
            word.save()
    return session

def add_all_kaldi_confidence():
    data = load_kaldi_forced_decoding_output()
    sessions =[]
    for i,line in enumerate(data):
        print(i,line[0])
        sessions.append(add_kaldi_confidence_to_session_and_word(line))
    return sessions

    

    
    
    
