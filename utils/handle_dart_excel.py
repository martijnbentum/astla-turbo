from openpyxl import load_workbook

def open_dart_excel():
    wb = load_workbook('../DART_test_data.xlsx')
    ws = wb['Blad1']
    lines = list(ws.values)
    header = lines[0]
    data = lines[1:]
    return wb, header, data

def audio_urls(dart_data = None):
    if not dart_data:
        wb, header, dart_data = open_dart_excel()
    output = []
    for line in dart_data:
        audio_url = line[18]
        if audio_url not in output: output.append(audio_url)
    return output


def show_column_unique_values(header,data):
    '''show the number of unique values per column.'''
    for i, cn in enumerate(header):
        print(i,cn, len(set([x[i] for x in data])))

def url_to_session_list(url,data):
    return [x for x in data if x[18] == url]

def session_list_to_word_list(session_list):
    return [get_word(line) for line in session_list]

def session_list_to_correct_list(session_list):
    return [get_correct(line) for line in session_list]

   


def get_all_pupils(data):
    return list(set([get_pupil(line) for line in data]))

def get_all_teachers(data):
    return list(set([get_teacher(line) for line in data]))

def get_all_schools(data):
    return list(set([get_school(line) for line in data]))


def get_word(line):
    return line[2]
def get_correct(line):
    return line[3]

def get_condition(line):
    return line[14]
def get_test_type(line):
    return line[15]
def get_exercise(line):
    return line[17]

def get_list_id(line):
    return line[1]
def get_set_id(line):
    return line[4]
def get_page_id(line):
    return line[16]

def get_pupil(line):
    return line[8]
def get_teacher(line):
    return line[0]
def get_school(line):
    return line[9]

def get_url(line):
    return line[18]
def get_duration(line):
    return line[19]
def get_date_str(line):
    return line[7]


# list set page id makes a word list unique n = 3724
# can use audio filename to select sessions n = 3127

def get_all_list_numbers(dart_data):
    return list(set([x[1] for x in dart_data]))

def get_all_list_set_page_combinations(dart_data):
    list_numbers = get_all_list_numbers(dart_data)
    output = []
    for x in dart_data:
        combination = data_line_to_list_set_page(x)
        if combination not in output: output.append(combination)
    return output

def make_list_page_to_wordlist_dict(dart_data):
    o = {}
    for x in dart_data:
        word = x[2]
        combination = data_line_to_list_set_page(x)
        if combination not in o.keys(): o[combination] = []
        if word not in o[combination]:
            o[combination].append(word)
    return o

def data_line_to_list_set_page(data_line):
    '''helper function to get list, set and page number from a data line.'''
    list_number = data_line[1]
    set_number = data_line[4]
    page_number = data_line[16]
    return list_number, set_number, page_number

