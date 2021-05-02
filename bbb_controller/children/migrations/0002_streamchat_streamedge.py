# Generated by Django 3.1.7 on 2021-05-02 18:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('children', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StreamChat',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(default='', max_length=255)),
                ('secret', models.CharField(default='', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StreamEdge',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(default='', max_length=255)),
                ('secret', models.CharField(default='', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]