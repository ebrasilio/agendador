# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-04-10 16:25
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('agenda', '0007_auto_20180322_1904'),
    ]

    operations = [
        migrations.AlterField(
            model_name='equipamento',
            name='antecedenciaMaxima',
            field=models.PositiveIntegerField(default=0, verbose_name=b'Anteced\xc3\xaancia m\xc3\xa1xima'),
        ),
        migrations.AlterField(
            model_name='equipamento',
            name='antecedenciaMinima',
            field=models.PositiveSmallIntegerField(default=0, verbose_name=b'Anteced\xc3\xaancia m\xc3\xadnima'),
        ),
        migrations.AlterField(
            model_name='equipamento',
            name='patrimonio',
            field=models.CharField(max_length=100, verbose_name=b'Patrim\xc3\xb4nio'),
        ),
        migrations.AlterField(
            model_name='equipamento',
            name='unidade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agenda.Unidade'),
        ),
        migrations.AlterField(
            model_name='espacofisico',
            name='antecedenciaMaxima',
            field=models.PositiveIntegerField(default=0, verbose_name=b'Anteced\xc3\xaancia m\xc3\xa1xima'),
        ),
        migrations.AlterField(
            model_name='espacofisico',
            name='antecedenciaMinima',
            field=models.PositiveSmallIntegerField(default=0, verbose_name=b'Anteced\xc3\xaancia m\xc3\xadnima'),
        ),
        migrations.AlterField(
            model_name='espacofisico',
            name='unidade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agenda.Unidade'),
        ),
        migrations.AlterField(
            model_name='reservaequipamento',
            name='atividade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agenda.Atividade'),
        ),
        migrations.AlterField(
            model_name='reservaequipamento',
            name='locavel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agenda.Equipamento', verbose_name=b'Loc\xc3\xa1vel'),
        ),
        migrations.AlterField(
            model_name='reservaequipamento',
            name='recorrencia',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='agenda.ReservaRecorrente'),
        ),
        migrations.AlterField(
            model_name='reservaequipamento',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name=b'Usu\xc3\xa1rio'),
        ),
        migrations.AlterField(
            model_name='reservaespacofisico',
            name='atividade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agenda.Atividade'),
        ),
        migrations.AlterField(
            model_name='reservaespacofisico',
            name='locavel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agenda.EspacoFisico', verbose_name=b'Loc\xc3\xa1vel'),
        ),
        migrations.AlterField(
            model_name='reservaespacofisico',
            name='recorrencia',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='agenda.ReservaRecorrente'),
        ),
        migrations.AlterField(
            model_name='reservaespacofisico',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name=b'Usu\xc3\xa1rio'),
        ),
        migrations.AlterField(
            model_name='reservaservico',
            name='atividade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agenda.Atividade'),
        ),
        migrations.AlterField(
            model_name='reservaservico',
            name='locavel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agenda.Servico', verbose_name=b'Loc\xc3\xa1vel'),
        ),
        migrations.AlterField(
            model_name='reservaservico',
            name='recorrencia',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.PROTECT, to='agenda.ReservaRecorrente'),
        ),
        migrations.AlterField(
            model_name='reservaservico',
            name='usuario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name=b'Usu\xc3\xa1rio'),
        ),
        migrations.AlterField(
            model_name='servico',
            name='antecedenciaMaxima',
            field=models.PositiveIntegerField(default=0, verbose_name=b'Anteced\xc3\xaancia m\xc3\xa1xima'),
        ),
        migrations.AlterField(
            model_name='servico',
            name='antecedenciaMinima',
            field=models.PositiveSmallIntegerField(default=0, verbose_name=b'Anteced\xc3\xaancia m\xc3\xadnima'),
        ),
        migrations.AlterField(
            model_name='servico',
            name='unidade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='agenda.Unidade'),
        ),
        migrations.AlterField(
            model_name='unidade',
            name='unidadePai',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.PROTECT, to='agenda.Unidade', verbose_name=b'Unidade pai'),
        ),
    ]