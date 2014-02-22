# -*- coding: utf-8 -*-
from south.db import db
from south.v2 import SchemaMigration


class Migration(SchemaMigration):
    def forwards(self, orm):
        # Adding model 'LastUrl'
        db.create_table('app_lasturl', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.TextField')(unique=True)),
            ('url', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('app', ['LastUrl'])

        # Adding model 'Url'
        db.create_table('app_url', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.TextField')(unique=True)),
            ('_url', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('app', ['Url'])

        # Adding model 'Resume'
        db.create_table('app_resume', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.TextField')()),
            ('videoExt', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('videoSize', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('seekPos', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('_pending', self.gf('django.db.models.fields.TextField')()),
            ('videoQuality', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('cacheBytesTotal', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('cacheBytesCount', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('app', ['Resume'])

        # Adding model 'Browser'
        db.create_table('app_browser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('site', self.gf('django.db.models.fields.TextField')(null=True)),
            ('lastsite', self.gf('django.db.models.fields.TextField')(null=True)),
            ('historysite', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('app', ['Browser'])


    def backwards(self, orm):
        # Deleting model 'LastUrl'
        db.delete_table('app_lasturl')

        # Deleting model 'Url'
        db.delete_table('app_url')

        # Deleting model 'Resume'
        db.delete_table('app_resume')

        # Deleting model 'Browser'
        db.delete_table('app_browser')


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