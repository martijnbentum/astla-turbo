from django.db import models

# Create your models here.

class Audio:
    filename = models.CharField(max_length= 1000, unique=True)
    duration = models.IntegerField(default=0)
    url = models.CharField(max_length=1000)

class Pupil:
    identifier = models.CharField(max_length= 30, unique=True)
    school_identifier = models.CharField(max_length= 30, unique=True)

class Wordlist:
    identifier = models.CharField(max_length=30, unique = True)
    page = models.IntegerField(default=0)

    
