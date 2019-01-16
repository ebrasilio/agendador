# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2018-02-06 15:19
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0008_alter_user_username_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Atividade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=30)),
                ('descricao', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Equipamento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.TextField()),
                ('descricao', models.TextField()),
                ('bloqueado', models.BooleanField(default=False)),
                ('invisivel', models.BooleanField(default=False)),
                ('localizacao', models.TextField()),
                ('fotoLink', models.URLField(blank=True)),
                ('patrimonio', models.PositiveIntegerField()),
                ('atividadesPermitidas', models.ManyToManyField(to='agenda.Atividade')),
                ('grupos', models.ManyToManyField(blank=True, to='auth.Group')),
                ('responsavel', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EspacoFisico',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.TextField()),
                ('descricao', models.TextField()),
                ('bloqueado', models.BooleanField(default=False)),
                ('invisivel', models.BooleanField(default=False)),
                ('localizacao', models.TextField()),
                ('fotoLink', models.URLField(blank=True)),
                ('capacidade', models.PositiveSmallIntegerField()),
                ('atividadesPermitidas', models.ManyToManyField(to='agenda.Atividade')),
                ('grupos', models.ManyToManyField(blank=True, to='auth.Group')),
                ('responsavel', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReservaEquipamento',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[(b'A', b'Aprovado'), (b'D', b'Desaprovado'), (b'E', b'Esperando')], default=b'E', max_length=1)),
                ('data', models.DateField()),
                ('horaInicio', models.TimeField()),
                ('horaFim', models.TimeField()),
                ('dataReserva', models.DateTimeField(auto_now_add=True)),
                ('ramal', models.PositiveIntegerField()),
                ('finalidade', models.TextField()),
                ('atividade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='agenda.Atividade')),
                ('locavel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='agenda.Equipamento')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReservaEspacoFisico',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(choices=[(b'A', b'Aprovado'), (b'D', b'Desaprovado'), (b'E', b'Esperando')], default=b'E', max_length=1)),
                ('data', models.DateField()),
                ('horaInicio', models.TimeField()),
                ('horaFim', models.TimeField()),
                ('dataReserva', models.DateTimeField(auto_now_add=True)),
                ('ramal', models.PositiveIntegerField()),
                ('finalidade', models.TextField()),
                ('atividade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='agenda.Atividade')),
                ('locavel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='agenda.EspacoFisico')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Unidade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sigla', models.CharField(max_length=20, unique=True)),
                ('nome', models.TextField()),
                ('descricao', models.TextField()),
                ('logoLink', models.URLField(blank=True)),
                ('grupos', models.ManyToManyField(blank=True, to='auth.Group')),
                ('responsavel', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
                ('unidadePai', models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.CASCADE, to='agenda.Unidade')),
            ],
        ),
        migrations.AddField(
            model_name='espacofisico',
            name='unidade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='agenda.Unidade'),
        ),
        migrations.AddField(
            model_name='equipamento',
            name='unidade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='agenda.Unidade'),
        ),
    ]
