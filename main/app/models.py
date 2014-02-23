import pickle
import base64

from django.db import models

from main.app.manager.urls import UrlBase


class LastUrl(models.Model):
    title = models.TextField("Title", unique=True)
    url = models.TextField("Url")

    def __str__(self):
        return self.title


class Url(models.Model, UrlBase):
    title = models.TextField("Title", unique=True)
    _url = models.TextField("Url")

    @property
    def url(self):
        return self.formatUrl(self._url)

    @url.setter
    def url(self, data):
        self._url = self.shortUrl(data)

    def __str__(self):
        return self.title


class Resume(models.Model):
    title = models.TextField("Title")

    videoExt = models.CharField("Stream extension", max_length=50)
    videoSize = models.PositiveIntegerField("Stream size")
    seekPos = models.PositiveIntegerField("Resume position")
    _pending = models.TextField("Stream resume block")
    videoQuality = models.PositiveIntegerField("Video quality")
    cacheBytesTotal = models.PositiveIntegerField("Stream downloaded bytes")
    cacheBytesCount = models.PositiveIntegerField("Stream size")
    videoPath = models.TextField("Video location")

    @property
    def pending(self):
        if self._pending:
            data = base64.b64decode(self._pending)
            data = pickle.loads(data)
        else:
            data = []
        return data

    @pending.setter
    def pending(self, data):
        data = base64.b64encode(pickle.dumps(data))
        self._pending = str(data, encoding='utf-8')

    @property
    def isCompleteDown(self):
        return self.cacheBytesCount >= (self.videoSize - 50)

    def __str__(self):
        return self.title


class Browser(models.Model):
    site = models.TextField("Site", null=True)
    lastsite = models.TextField("Last site", null=True)
    historysite = models.TextField("History site", null=True)

    def __str__(self):
        return self.site or self.lastsite or self.historysite
