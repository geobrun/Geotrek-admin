# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2020-02-28 17:30
from __future__ import unicode_literals


from django.db import migrations
import mimetypes


def forward(apps, schema_editor):
    AttachmentModel = apps.get_model('common', 'Attachment')
    for attachment in AttachmentModel.objects.all():
        mt = mimetypes.guess_type(attachment.attachment_file.name, strict=True)[0]
        if mt is not None and mt.split('/')[0].startswith('image'):
            attachment.is_image = True
            attachment.save()


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0010_attachment_is_image'),
    ]

    operations = [
        migrations.RunPython(forward),
    ]