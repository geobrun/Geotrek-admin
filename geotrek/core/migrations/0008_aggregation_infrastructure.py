# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-12-03 10:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('infrastructure', '0007_create_infra_signa'),
        ('core', '0007_auto_20181220_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name=b'PathAggregation',
            name='topo_object',
            field=models.ForeignKey(db_column=b'evenement', on_delete=django.db.models.deletion.CASCADE, related_name='aggregations', to='core.Topology', verbose_name='Topology'),
        ),
        migrations.AlterField(
            model_name=b'PathAggregation',
            name='topo_object',
            field=models.ForeignKey(db_column=b'evenement', on_delete=django.db.models.deletion.CASCADE, related_name='aggregations', to='core.Topology', verbose_name='Topology'),
        ),
    ]
