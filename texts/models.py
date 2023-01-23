from django.db import models

# Create your models here.

class School(models.Model):
    identifier = models.CharField(max_length= 30, unique=True)

    def __repr__(self):
        return 'school: ' + str(self.identifier)

class Pupil(models.Model):
    identifier = models.CharField(max_length= 30, unique=True)

    def __repr__(self):
        return 'pupil: ' + str(self.identifier)

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
    dataset = models.CharField(max_length=50,default='')
    multiple_dart_correctors = models.BooleanField(default = False)

    def __repr__(self):
        return self.word_list + ' ' + str(self.ncorrect)


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


    class Meta:
        unique_together = ['word','session']

    def __repr__(self):
        m =  self.word + ' ' + self.hyp_aligned_word + ' ' 
        m += str(self.correct) + ' ' + str(self.index)
        return m



    
