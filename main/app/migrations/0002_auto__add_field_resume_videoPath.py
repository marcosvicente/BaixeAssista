# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding field 'Resume.videoPath'
        db.add_column('app_resume', 'videoPath',
                      self.gf('django.db.models.fields.TextField')(default=''),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Resume.videoPath'
        db.delete_column('app_resume', 'videoPath')


    models = {
        'app.browser': {
            'Meta': {'object_name': 'Browser'},
            'historysite': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lastsite': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'site': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        'app.lasturl': {
            'Meta': {'object_name': 'LastUrl'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'unique': 'True'}),
            'url': ('django.db.models.fields.TextField', [], {})
        },
        'app.resume': {
            'Meta': {'object_name': 'Resume'},
            '_pending': ('django.db.models.fields.TextField', [], {}),
            'cacheBytesCount': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'cacheBytesTotal': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'seekPos': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'title': ('django.db.models.fields.TextField', [], {}),
            'videoExt': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'videoPath': ('django.db.models.fields.TextField', [], {}),
            'videoQuality': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'videoSize': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'app.url': {
            'Meta': {'object_name': 'Url'},
            '_url': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'unique': 'True'})
        }
    }

    complete_apps = ['app']