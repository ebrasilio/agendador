# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404, render_to_response
from django.utils.safestring import mark_safe
import time
import calendar
from datetime import date, datetime, timedelta
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.core.context_processors import csrf
from django.forms.models import modelformset_factory
from django.template import RequestContext
from django.core.context_processors import csrf
from agenda.models import *
from agenda.forms import FormReserva
from django import forms

mnames = "Janeiro Fevereiro Março Abril Maio Junho Julho Agosto Setembro Outubro Novembro Dezembro"
labinfo = "alcibia.maia alcides.milton ramon.rdm alexandra.boing arakawa.aline alyne.cardoso angela.rbs celia.campos claudia.colussi claudia.regina danielle.antes elaine.santos lemos.senna eleonora.dorsi felipe.daltoe francilene.vieira francis.tourinho fulvio.nedel janaina.neves joao.bastos juliana.balbinot j.gazzola karina.mary keyla.n l.bernardes luciana.m.rosa maria.assis elena.guanilo maria.isabel rita.pimenta terezinha.zeferino patricia.di.pietro patricia.haas renata.scharlach roberta.costa rodrigo.alves.lima rogerio.gondak selma.regina suely.grosseman v.m.laura"
mnames = mnames.split()


def index(request):
	titulo = "Agendador de espaço físico do CCS"
	corpo = "Bem vindo ao Agendador de espaço físico do CCS"
	return render_to_response("index.html",{'corpo':corpo,"titulo":titulo})

def sobre(request):
	titulo = "Requisitos do Agendador CCS"
	return render_to_response("sobre.html", {'titulo':titulo})

def main(request, espaco=None ,year=None):
    """Main listing, years and months; three years per page."""
    # prev / next years
    if year: year = int(year)
    else:    year = time.localtime()[0]

    nowy, nowm = time.localtime()[:2]
    lst = []
    
    # create a list of months for each year, indicating ones that contain entries and current
    for y in [year, year+1, year+2]:
        mlst = []
        for n, month in enumerate(mnames):
            entry = current = False   # are there entry(s) for this month; current month?
            #entries = Entry.objects.filter(date__year=y, date__month=n+1)
            #if not _show_users(request):
            #    entries = entries.filter(creator=request.user)
            """
            if entries:
                entry = True
            if y == nowy and n+1 == nowm:
                current = True
            mlst.append(dict(n=n+1, name=month, entry=entry, current=current))
            """
            if y == nowy and n+1 == nowm:
                current = True
            mlst.append(dict(n=n+1, name=month, current=current))
        lst.append((y, mlst))
    
    espacosfisicos = EspacoFisico.objects.all()
    espacofisico = EspacoFisico.objects.filter(id=espaco)

    return render_to_response("main.html", dict(espaco=espacofisico, years=lst, user=request.user, year=year, espacosfisicos=espacosfisicos))

def month(request, espaco, year, month, change=None):
    """Listing of days in `month`."""
    espaco, year, month = int(espaco), int(year), int(month)

    # apply next / previous change
    if change in ("next", "prev"):
        now, mdelta = date(year, month, 15), timedelta(days=31)
        if change == "next":   mod = mdelta
        elif change == "prev": mod = -mdelta

        year, month = (now+mod).timetuple()[:2]

    # init variables
    cal = calendar.Calendar()
    month_days = cal.itermonthdays(year, month)
    nyear, nmonth, nday = time.localtime()[:3]
    lst = [[]]
    week = 0
    #entries = False
    #entries = Reserva.objects.filter(dataUsoInicio__year=year, dataUsoInicio__month=month, dataUsoInicio__day=day)
    # make month lists containing list of days for each week
    # each day tuple will contain list of entries and 'current' indicator
    for day in month_days:
        entries = current = False   # are there entries for this day; current day?
        if day:
        	entries = Reserva.objects.filter(data__year=year, data__month=month, data__day=day, espacoFisico=espaco)
        	##entries.filter(dataUsoInicio__day=day)
        	#entries = Entry.objects.filter(year=year, date__month=month, date__day=day)
            #entries = Reserva.objects.filter(dataUsoInicio=datetime(year,month,day))
           	#if not _show_users(request):
            #    entries = entries.filter(creator=request.user)
        if day == nday and year == nyear and month == nmonth:
            current = True

        lst[week].append((day, entries, current))
        if len(lst[week]) == 7:
            lst.append([])
            week += 1
    espacofisico = EspacoFisico.objects.get(id=espaco)
    return render_to_response("month.html", dict(espaco=espacofisico, year=year, month=month, user=request.user, month_days=lst, mname=mnames[month-1]))


def dia(request, espaco, year, month, day):
    """Entries for the day."""
    nyear, nmonth, nday = time.localtime()[:3]
    espacofisico = EspacoFisico.objects.get(id=espaco)
    reservas = Reserva.objects.filter(data__year=year, data__month=month, data__day=day, espacoFisico=espaco).order_by("horaInicio")
    return render_to_response("dia.html", dict(reservas=reservas, espaco=espacofisico, anovisualizacao=year ,mesvisualizacao=month))
    """
    ## 	ANTIGO ##
    EntriesFormset = modelformset_factory(Entry, extra=1, exclude=("creator", "date"), can_delete=True)

    if request.method == 'POST':
        formset = EntriesFormset(request.POST)
        if formset.is_valid():
            # add current user and date to each entry & save
            entries = formset.save(commit=False)
            for entry in entries:
                entry.creator = request.user
                entry.date = date(int(year), int(month), int(day))
                entry.save()
            return HttpResponseRedirect(reverse("dbe.cal.views.month", args=(year, month)))

    else:
        # display formset for existing enties and one extra form
        formset = EntriesFormset(queryset=Entry.objects.filter(date__year=year, date__month=month, date__day=day, creator="1"))
        return render_to_response("dia.html", add_csrf(request, entries=formset, year=year, month=month, day=day))
"""

def add_csrf(request, ** kwargs):
    """Add CSRF and user to dictionary."""
    d = dict(user=request.user, ** kwargs)
    d.update(csrf(request))
    return d

def espacos(request):
	espacos1 = EspacoFisico.objects.order_by("nome").all()
	ano = time.localtime()[0]
	mes = time.localtime()[1]
	return render_to_response("espacos.html", {'ano': ano, 'mes': mes, 'espacos': espacos1})

@login_required
def addreserva(request):
    usuario = request.user.username
    dados = request.session.get('attributes')
    if request.method == "POST":
        request.POST = request.POST.copy()
        request.POST['estado'] = 1
        request.POST['usuario'] = request.user.id
        form = FormReserva(request.POST, request.FILES)
        if form.is_valid():
            form.fields['usuario'] = forms.CharField(initial=request.user.id)
            
            """Bloqueia as salas da pos"""
            if ( request.POST['espacoFisico']=='7' or
                 request.POST['espacoFisico']=='8' or
                 request.POST['espacoFisico']=='9' or
                 request.POST['espacoFisico']== '10'):
                return render_to_response("salvo.html",{'mensagem':"Erro: Salas pos graduação estão temporariamente bloqueadas. "})

            if ((not request.user.username in labinfo) and (request.POST['espacoFisico']=='3')):
                return render_to_response("salvo.html",{'mensagem':"Erro: Você não realizaou o curso para utilizar o labinfo "})
            
            if form.choque():
                return render_to_response("salvo.html",{'mensagem':"Erro: Já existe reserva neste horário"})
            form.save()
            return render_to_response("salvo.html",{'mensagem': "Reserva realizada com sucesso!"})
    else:
        form = FormReserva()
        form.fields['usuario'].widget = forms.HiddenInput()
        form.fields['estado'].widget = forms.HiddenInput()
        form.fields['dataReserva'].widget = forms.HiddenInput()
    return render_to_response("addreserva.html", {'form': form, "usuario": usuario, 'dados': dados }, context_instance=RequestContext(request))