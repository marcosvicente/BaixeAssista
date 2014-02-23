# coding: utf-8
from main.app.models import Resume
from main.app.util import base


class ResumeInfo(object):

    def __init__(self, filename):
        try:
            self.q = Resume.objects.get(title=filename)
        except Resume.DoesNotExist:
            self.q = Resume(title=filename)

        self.filename = filename

    def update(self, **kwargs):
        """ kwargs = {}
         - videoExt; videoSize; seekPos; pending; cacheBytesTotal; 
         - cacheBytesCount; videoQuality
        """
        self.q.__dict__.update(kwargs)
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