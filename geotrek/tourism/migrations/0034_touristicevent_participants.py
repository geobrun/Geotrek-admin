# Generated by Django 3.2.15 on 2022-09-28 08:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tourism', '0033_auto_20220929_0840'),
    ]

    operations = [
        migrations.CreateModel(
            name='TouristicEventParticipantCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=255, verbose_name='Label')),
                ('order', models.PositiveSmallIntegerField(blank=True, default=None, null=True, verbose_name='Display order')),
            ],
            options={
                'verbose_name': 'Participant category',
                'verbose_name_plural': 'Participant categories',
                'ordering': ['order', 'label'],
            },
        ),
        migrations.CreateModel(
            name='TouristicEventParticipantCount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('count', models.PositiveIntegerField(verbose_name='Number of participants')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='tourism.touristiceventparticipantcategory', verbose_name='Category')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='participants', to='tourism.touristicevent', verbose_name='Touristic event')),
            ],
        ),
    ]