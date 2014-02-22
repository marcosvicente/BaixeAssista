# coding: utf-8
from main.app import models
from main.app.util import base


class ResumeInfo(object):
    objects = models.Resume.objects

    def __init__(self, filename):
        try:
            self.q = self.objects.get(title=filename)
        except:
            self.q = models.Resume(title=filename)

        self.filename = filename

    def update(self, **kwargs):
        """ kwargs = {}
         - videoExt; videoSize; seekPos; pending; cacheBytesTotal; 
         - cacheBytesCount; videoQuality
        """
        for field in kwargs:
            setattr(self.q, field, kwargs[field])

        self.q.save()

    def __getitem__(self, name):
        return getattr(self.q, name)

    @property
    def query(self):
        return self.q

    @property
    def isEmpty(self):
        return self.q.pk is None

    @base.LogOnError
    def remove(self):
        self.q.delete()
        
