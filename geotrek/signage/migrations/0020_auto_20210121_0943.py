# Generated by Django 3.1.5 on 2021-01-21 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signage', '0019_auto_20201117_1302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='signage',
            name='publication_date',
            field=models.DateField(blank=True, editable=False, null=True, verbose_name='Publication date'),
        ),
        migrations.AlterField(
            model_name='signage',
            name='published',
            field=models.BooleanField(default=False, help_text='Visible on Geotrek-rando', verbose_name='Published'),
        ),
        migrations.AlterField(
            model_name='signagetype',
            name='pictogram',
            field=models.FileField(blank=True, max_length=512, null=True, upload_to='upload', verbose_name='Pictogram'),
        ),
    ]
