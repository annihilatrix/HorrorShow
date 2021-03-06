# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-18 04:12
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Collection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('max_size', models.SmallIntegerField(default=25)),
                ('creation_date', models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('imdb_id', models.CharField(max_length=15, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=250)),
                ('year', models.DateField(blank=True, null=True)),
                ('rated', models.CharField(blank=True, max_length=10)),
                ('release_date', models.DateField(blank=True, null=True)),
                ('runtime', models.CharField(blank=True, max_length=15)),
                ('genre', models.CharField(blank=True, max_length=100)),
                ('plot', models.TextField(blank=True)),
                ('language', models.CharField(blank=True, max_length=50)),
                ('country', models.CharField(blank=True, max_length=50)),
                ('poster_url', models.URLField(blank=True)),
                ('poster_loc', models.FilePathField(blank=True)),
                ('imdb_url', models.URLField()),
                ('omdb_url', models.URLField()),
            ],
        ),
        migrations.AddField(
            model_name='collection',
            name='movies',
            field=models.ManyToManyField(to='movies.Movie'),
        ),
    ]
