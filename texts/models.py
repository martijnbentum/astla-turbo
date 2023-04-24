from django.db import models
from utils import helper
import json
import os
import textgrids

# Create your models here.

class School(models.Model):
    identifier = models.CharField(max_length= 30, unique=True)

    def __repr__(self):
        return 'school: ' + str(self.identifier)

class Jasmin_child(models.Model):
    identifier = models.CharField(max_length = 30, unique=True)
    residence_place = models.CharField(max_length = 30)
    birth_place = models.CharField(max_length = 30)
    educational_place = models.CharField(max_length = 30)
    dialect_region= models.CharField(max_length = 30)
    gender = models.CharField(max_length=10)
    age = models.IntegerField(null = True)
    group = models.IntegerField(null = True)
    home_language1 = models.CharField(max_length = 30)
    home_language2 = models.CharField(max_length = 30, null=True)
    info= models.TextField(default = '')

class Jasmin_recording(models.Model):
    dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
    identifier = models.CharField(max_length = 30, unique = True)
    audio_filename = models.CharField(max_length = 300, default = '')
    awd_filename = models.CharField(max_length = 300, default = '')
    child = models.ForeignKey(Jasmin_child,**dargs)
    component = models.CharField(max_length = 10, default = '')
    reading_level = models.CharField(max_length = 15, default = '',null=True)
    group = models.IntegerField(null = True)
    nchannels = models.IntegerField(null = True)
    sample_rate = models.IntegerField(null = True)
    duration = models.FloatField(default=0.0)
    info= models.TextField(default = '')

    def load_awd(self):
        f = '../jasmin_awd/' + self.awd_filename.split('/')[-1]
        return textgrids.TextGrid(f)

    def phrases(self, end_on_eos = True, minimum_duration = None,
        maximum_duration = None):
        d = self.speaker_to_phrases_dict(end_on_eos, minimum_duration,
            maximum_duration)
        o = []
        for phrases in d.values():
            o.extend(phrases)
        return o
    
class Jasmin_word(models.Model):
    dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
    awd_word = models.CharField(max_length= 100, default = '')
    awd_word_phoneme = models.CharField(max_length= 100, default = '')
    awd_word_phonemes= models.TextField(default = '')
    start_time = models.FloatField(default=None, null=True)
    end_time = models.FloatField(default=None, null=True)
    recording = models.ForeignKey(Jasmin_recording,**dargs)
    child = models.ForeignKey(Jasmin_child,**dargs)
    awd_word_tier_index = models.PositiveIntegerField(null=True,blank=True)
    special_word= models.BooleanField(default=False)
    eos= models.BooleanField(default=False)

    class Meta:
        unique_together = ('recording','child','awd_word_tier_index')
    

class Pupil(models.Model):
    identifier = models.CharField(max_length= 30, unique=True)
    pupil_id = models.CharField(max_length= 30, default = '')
    class_id = models.CharField(max_length= 30, default = '')
    school_id = models.CharField(max_length= 30, default = '')
    birth_date = models.DateField(default = None, blank= True, null=True)
    home_lang_str = models.CharField(max_length= 50, default = '')
    gender = models.CharField(max_length= 10, default = '' )
    reading_level = models.CharField(max_length= 10, default = '')
    train_dev_test = models.CharField(max_length=5,default='')
    only_dutch = models.BooleanField(null=True)
    also_dutch = models.BooleanField(null=True)
    no_dutch = models.BooleanField(null=True)
    info= models.TextField(default = '')
    dataset = models.CharField(max_length=50,default='')
    
    def __repr__(self):
        return 'pupil: ' + str(self.identifier)

    @property
    def duration_sessions(self):
        if not hasattr(self,'_duration_sessions'):
            n = sum([x.duration for x in self.session_set.all()])
            self._duration_sessions = n
        return self._duration_sessions

    @property
    def current_age_in_months(self):
        return helper.delta_months(self.birth_date)

    @property
    def test_types(self):
        if not hasattr(self,'_test_types'):
            t = list(set([x.test_type for x in self.session_set.all()]))
            self._test_types = t
        return self._test_types



class Teacher(models.Model):
    identifier = models.CharField(max_length= 30, unique=True)

    def __repr__(self):
        return 'teacher: ' + str(self.identifier)


class Session(models.Model):
    dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
    word_list = models.TextField(default = '')
    correct_list = models.TextField(default = '')
    pupil = models.ForeignKey(Pupil,**dargs)
    teacher = models.ForeignKey(Teacher,**dargs)
    school = models.ForeignKey(School,**dargs)
    audio_filename = models.CharField(max_length= 300) 
    identifier = models.CharField(max_length=1000, unique = True)
    duration = models.IntegerField(default=0)
    list_id = models.IntegerField(default=0)
    set_id = models.CharField(max_length = 30, default = '')
    page_id = models.IntegerField(default=0)
    condition = models.CharField(max_length= 30, default = '') 
    test_type= models.CharField(max_length= 30, default = '') 
    exercise= models.IntegerField(default=0) 
    info= models.TextField(default = '')
    correct_available = models.BooleanField(null=True)
    all_correct = models.BooleanField(null=True)
    all_incorrect = models.BooleanField(null=True)
    ncorrect = models.IntegerField(default = 0)
    nwords= models.IntegerField(default=0)
    align = models.TextField(default='')
    whisper_align = models.TextField(default='')
    dataset = models.CharField(max_length=50,default='')
    multiple_dart_correctors = models.BooleanField(default = False)
    train_dev_test = models.CharField(max_length=5,default='')
    word_time_information_available= models.BooleanField(null=True)
    kaldi_fd_confidence_list = models.TextField(default='')
    kaldi_fd_mean_confidence = models.FloatField(default=0.0)
    

    def __repr__(self):
        return self.word_list + ' ' + str(self.ncorrect)

    def whisper_json(self):
        f = '../WHISPER_DART/dart-whisper-prompts/'
        f += self.identifier.split('/')[-1].split('.')[0]
        f += '.json'
        if os.path.isfile(f):
            return json.load(open(f))
        print('could not find',f)

    @property
    def n_correctors(self):
        if not self.multiple_dart_correctors: return 1
        return len(self.teacher_to_correct_list_dict.keys())

    @property
    def teacher_to_correct_list_dict(self):
        if not self.multiple_dart_correctors: 
            d[self.teacher.identifier] = self.correct_list 
        if hasattr(self,'_teacher_to_correct_list_dict'):
            return self._teacher_to_correct_list_dict
        from utils.handle_dart_excel import group_info_on_teacher_list_set
        from utils.handle_dart_excel import session_list_to_correct_list
        d = group_info_on_teacher_list_set(self.info)
        number_keys = [k for k in d.keys() if not 'word' in k]
        o = {}
        for number_key in number_keys:
            teacher_identifier = number_key[0]
            session_list = d[number_key]
            cl = session_list_to_correct_list(session_list)
            o[teacher_identifier] = cl
        self._teacher_to_correct_list_dict = o
        return self._teacher_to_correct_list_dict

    

class Word(models.Model):
    dargs = {'on_delete':models.SET_NULL,'blank':True,'null':True}
    session= models.ForeignKey(Session,**dargs)
    index = models.IntegerField(default=0)
    correct= models.IntegerField(default=0)
    audio_url = models.CharField(max_length= 1000, default = '') 
    audio_filename = models.CharField(max_length= 1000, default = '') 
    word = models.CharField(max_length= 100, default = '') 
    gt_aligned_word = models.CharField(max_length= 100, default = '') 
    hyp_aligned_word = models.CharField(max_length= 100, default = '') 
    span = models.CharField(max_length= 100, default = '') 
    levenshtein_distance= models.IntegerField(default=0)
    levenshtein_ratio = models.FloatField(default = 0.0)
    dataset = models.CharField(max_length=50,default='')
    train_dev_test = models.CharField(max_length=5,default='')
    start_time= models.FloatField(default = 0.0)
    end_time= models.FloatField(default = 0.0)
    duration = models.FloatField(default = 0.0)
    word_time_information_available= models.BooleanField(null=True)
    whisper_info = models.TextField(default = '')
    egemap_features = models.TextField(default = '')
    kaldi_fd_confidence = models.FloatField(default = 0.0)


    class Meta:
        unique_together = ['word','session']

    def __repr__(self):
        m =  self.word + ' ' + self.hyp_aligned_word + ' ' 
        m += str(self.correct) + ' ' + str(self.index)
        return m



    
