from django.db import models
from utils import helper
import json
import os

# Create your models here.

class School(models.Model):
    identifier = models.CharField(max_length= 30, unique=True)

    def __repr__(self):
        return 'school: ' + str(self.identifier)

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
    

    def __repr__(self):
        return self.word_list + ' ' + str(self.ncorrect)

    def whisper_json(self):
        f = '../WHISPER_DART/dart-whisper-prompts/'
        f += self.identifier.split('/')[-1].split('.')[0]
        f += '.json'
        if os.path.isfile(f):
            return json.load(open(f))
        print('could not find',f)

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


    class Meta:
        unique_together = ['word','session']

    def __repr__(self):
        m =  self.word + ' ' + self.hyp_aligned_word + ' ' 
        m += str(self.correct) + ' ' + str(self.index)
        return m



    
