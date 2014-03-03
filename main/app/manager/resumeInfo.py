# coding: utf-8
from main.app.models import Resume
from main.app.util import base


class ResumeInfo(object):
    objects = Resume.objects

    def __init__(self, filename):
        try:
            self.q = Resume.objects.get(title=filename)
        except Resume.DoesNotExist:
            self.q = Resume(title=filename)

        self.filename = filename

    def __getattr__(self, name):
        return getattr(self.q, name)

    def __getitem__(self, name):
        return getattr(self.q, name)

    def update(self, **kwargs):
        for field, value in kwargs.items():
            setattr(self.q, field, value)
        self.q.save()

    @property
    def query(self):
        return self.q

    @property
    def is_empty(self):
        return self.q.pk is None

    @base.LogException
    def remove(self):
        self.q.delete()