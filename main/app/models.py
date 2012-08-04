from django.db import models

########################################################################

# Create your models here.
class Url( models.Model ):
	title = models.TextField("Title", unique=True)
	url = models.TextField("Url")
	
	def __unicode__(self):
		return self.title
	
########################################################################
class LastUrl( models.Model ):
	title = models.TextField("Title", unique=True)
	url = models.TextField("Url")
	
	def __unicode__(self):
		return self.title
	
########################################################################
class Resume( models.Model ):
	title = models.TextField("Title")
	streamDownBytes = models.PositiveIntegerField("Stream downloaded bytes")
	streamQuality = models.PositiveIntegerField("Stream quality")
	streamSize = models.PositiveIntegerField("Stream size")
	resumePosition = models.PositiveIntegerField("Resume position")
	streamExt = models.CharField("Stream extension", max_length=50)
	resumeBLocks = models.TextField("Stream resume block")
	sendBytes = models.PositiveIntegerField("Stream size")

	def __unicode__(self):
		return self.title
	
########################################################################
class Browser( models.Model ):
	site = models.TextField("Site", null=True)
	lastsite = models.TextField("Last site", null=True)
	historysite = models.TextField("History site", null=True)
	
	def __unicode__(self):
		return (self.site or self.lastsite or self.historysite)
