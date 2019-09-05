# -*- coding: utf-8 -*-
from django.shortcuts import render, get_object_or_404, render_to_response, redirect
from django.utils.safestring import mark_safe
import time, calendar
from datetime import date, datetime, timedelta
from django.db.models.functions import Lower
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse, HttpResponseNotFound
from django.forms.models import modelformset_factory
from django.template import RequestContext, Library
from django.views.decorators import csrf
from agenda.models import *
from agenda.forms import ReservaEspacoFisicoAdminForm, RegisterForm, EstatisticaForm
from django import forms
from django.contrib.admin.sites import AdminSite
from django.contrib.flatpages.models import FlatPage
from django.contrib.auth import login, authenticate
from django.shortcuts import render, redirect
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from datetime import date
import admin
from forms import *

from material.frontend.views import ModelViewSet

from django.contrib.admin.models import LogEntry

month_names = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
unidade_default = 'ufsc'

def index(request, unidade=None):

    # get unit
    try:  # try to get given unit
        unidade = Unidade.objects.get(sigla__iexact=unidade)
    # no given unit. check if unit was given in the domain
    except Unidade.DoesNotExist:
        typed_url = request.build_absolute_uri()
        splitted_url = typed_url.split('.')
        unidade = None
        for url_part in splitted_url:  # check url for unit
            lower_root = unidade_default.lower()  # the programmer may have put uppercase in root. Lets avoid errors
            if url_part != lower_root:  # skip root unit, since it may be part of the domain
                try:
                    unidade = Unidade.objects.get(sigla__iexact=url_part)
                    break
                except:
                    pass  # url_part was not an unit. that's ok
        # no unit found
        if not unidade:
            try:
                unidade = Unidade.objects.get(sigla__iexact=unidade_default)  # get root unit
            except Unidade.DoesNotExist:
                return render_to_response("agenda/index.html")  # can't find unit to load. render blank

    if request.method == 'POST':
        search_form = SearchFilterForm(request.POST)
        if search_form.is_valid():
            data = search_form.cleaned_data['data'].strftime('%d%m%Y')
            horaInicio = search_form.cleaned_data['horaInicio'].strftime('%H%M')
            horaFim = search_form.cleaned_data['horaFim'].strftime('%H%M')
            tipo = search_form.cleaned_data['tipo']
            return redirect('/filtro_locavel_disponivel/' + str(unidade.id) + '/' + tipo +'/' + data + '/' + horaInicio + '/' + horaFim + '/')
        elif search_form.data['tipo'] == 'f':
            search_f = search_form
            search_e = SearchFilterForm(tipo='e')
            search_s = SearchFilterForm(tipo='s')
        elif search_form.data['tipo'] == 'e':
            search_f = SearchFilterForm(tipo='f')
            search_e = search_form
            search_s = SearchFilterForm(tipo='s')
        elif search_form.data['tipo'] == 's':
            search_f = SearchFilterForm(tipo='f')
            search_e = SearchFilterForm(tipo='e')
            search_s = search_form

    else:
        search_f = SearchFilterForm(tipo='f')
        search_e = SearchFilterForm(tipo='e')
        search_s = SearchFilterForm(tipo='s')
    #titulo = "Agendador UFSC"
    #corpo = "Bem vindo ao Agendador de espaços físicos e equipamentos da UFSC"



    unidades = Unidade.objects.filter(unidadePai=unidade)

    espacosFisicos = EspacoFisico.objects.filter(unidade=unidade).filter(invisivel=False).order_by(Lower("nome"))
    equipamentos = Equipamento.objects.filter(unidade=unidade).filter(invisivel=False).order_by(Lower("nome"))
    servicos = Servico.objects.filter(unidade=unidade).filter(invisivel=False).order_by(Lower("nome"))

    year = time.localtime()[0]
    current_year, current_month = time.localtime()[:2]
    lst = []
    # create a list of months for each year, indicating ones that contain entries and current
    for y in [year, year+1]:
        month_list = []
        for n, month in enumerate(month_names):
            if (n + 1) >= current_month or y != year:
                month_list.append(dict(n=n+1, name=month_names[n]))
        lst.append((y, month_list))

    return render(
        request,
        "agenda/index.html",
        dict(
            unidade=unidade, unidades=unidades,
            espacosfisicos=espacosFisicos, equipamentos=equipamentos, servicos=servicos,
            years=lst, user=request.user, search_f=search_f, search_e=search_e, search_s=search_s
            )
        )

def sobre(request):
    total_espacos = EspacoFisico.objects.all()
    reservas_fisico_mes = dict()
    for i in range(12):
        reservas_fisico_mes[i+1] = len(ReservaEspacoFisico.objects.filter(data__month=(i+1), estado='A'))

    print(len(total_espacos))
    print(reservas_fisico_mes)
    return render(request, "agenda/sobre.html")


def estatisticas(request):
    unidadesN=Unidade.objects.all().count()
    equipamentosN=Equipamento.objects.all().count()
    espacosfisicosN=EspacoFisico.objects.all().count()
    servicosN=Servico.objects.all().count()

    if request.user:
        if request.user.groups.filter(name="responsable").count() or request.user.is_superuser:
            show_user_stats = True
        else:
            show_user_stats = False
    else:
        show_user_stats = False

    form = EstatisticaForm(usr=None)
    if request.user.is_authenticated():
        form = EstatisticaForm(usr=request.user)
        if request.method == "POST":
            form = EstatisticaForm(request.user, request.POST)
            if form.is_valid():
                reservas_equips = None
                reservas_espfis = None
                reservas_e = []
                reservas_ef = []
                horas_e = []
                horas_ef= []
                usuario = form.cleaned_data.get("usuario")
                eq = request.POST.get("choice_1")
                ef = request.POST.get("choice_2")
                periodo_inicio = form.cleaned_data.get("periodo_inicio")
                periodo_fim = form.cleaned_data.get("periodo_fim")
                equipamento_choose = form.cleaned_data.get("equipamento_choose")
                espacofisico_choose = form.cleaned_data.get("espacofisico_choose")

                if not usuario :
                    usuario = User.objects.all()

                if eq == "equipamento":
                    #todas as reservas feitas pelo usuário que foram aceitas.
                    reservas_equips = ReservaEquipamento.objects.filter(estado="A", usuario__in=usuario, data__gte=periodo_inicio, data__lte=periodo_fim)
                    if equipamento_choose and reservas_equips:
                        reservas_equips = reservas_equips.filter(locavel__in=equipamento_choose)

                    if not equipamento_choose:
                        equipamento_choose = Equipamento.objects.all()

                    #agrupar em um dicionario as reservas por equipamento.
                    for equip in equipamento_choose:
                        reservas_e.append((equip.nome, reservas_equips.filter(locavel=equip)))
                        segundosTotal = 0
                        for reserva in reservas_equips.filter(locavel=equip):
                            segundosInicio = (reserva.horaInicio.hour*60 + reserva.horaInicio.minute) * 60 + reserva.horaInicio.second
                            segundosFim = (reserva.horaFim.hour*60+reserva.horaFim.minute) * 60 + reserva.horaFim.second
                            segundosTotal += segundosFim - segundosInicio
                        horas_e.append((equip.nome, str(timedelta(seconds=segundosTotal))))
                if ef == "espacofisico":
                    #todas as reservas feitas pelo usuário que foram aceitas.
                    reservas_espfis = ReservaEspacoFisico.objects.filter(estado="A", usuario__in=usuario, data__gte=periodo_inicio, data__lte=periodo_fim)
                    if espacofisico_choose and reservas_espfis:
                        reservas_espfis = reservas_espfis.filter(locavel__in=espacofisico_choose)
                    if not espacofisico_choose:
                        espacofisico_choose = EspacoFisico.objects.all()
                    for espfis in espacofisico_choose:
                        reservas_ef.append((espfis.nome, reservas_espfis.filter(locavel=espfis)))
                        segundosTotal = 0
                        for reserva in reservas_espfis.filter(locavel=espfis):
                            segundosInicio = (reserva.horaInicio.hour*60 + reserva.horaInicio.minute) * 60 + reserva.horaInicio.second
                            segundosFim = (reserva.horaFim.hour*60+reserva.horaFim.minute) * 60 + reserva.horaFim.second
                            segundosTotal += segundosFim - segundosInicio
                        horas_ef.append((espfis.nome, str(timedelta(seconds=segundosTotal))))
                return render(request, "agenda/estatistica_results.html", {"reservas_e":reservas_e, "reservas_ef":reservas_ef, "horas_e":horas_e, "horas_ef":horas_ef})
    return render(request, "agenda/estatisticas.html", {"form":form, "show_per_user_statistics":show_user_stats,"unidades":unidadesN, "equipamentos":equipamentosN, "espacosfisicos":espacosfisicosN, "servicos":servicosN})

def manutencao(request):
    return render(request, "agenda/manutencao.html")

def normal_registration(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect("index")
    else:
        form = RegisterForm()
    return render(request, "agenda/registrar.html", {"form":form})

def reset_pw_request(request):
    message = ""
    status = ""
    if request.method == "POST":
        # aqui tinha que enviar o email pro cara com um token, tem que gerar um token etcc.#
        email = request.POST['email']
        if (email == ""):
            message = "Campo email é obrigatório"
            status = "fail"
        else:
            try:
                match = User.objects.get(email=email)
            except User.DoesNotExist:
                message = "Não existe usuário com esse email."
                status = "fail"
                return render(request, "agenda/pwreset_request.html", {"message":message, "status":status})

            token_string = get_random_string(length=32)
            recovT = RecoveryToken(token=token_string, user=match)
            recovT.save()
            base_url = request.build_absolute_uri('/')
            url = "%saccounts/resetpw/%s" % (base_url, recovT.token)
            text = render_to_string("agenda/pwreset_email.html", {"link":url})
            # esse send mail só vai funcionar se o email lá estiver configurado certinho no settings.py#
            send_mail("Redefinição de senha", "", settings.EMAIL_HOST_USER, [email], html_message=text)
            message = "Um email foi enviado com um link para realizar a (re)definição da sua senha."
            status = "success"

    return render(request,"agenda/pwreset_request.html", {"message":message, "status":status})

def reset_pw(request, token):
    status = "Ok"
    try:
        recoveryToken = RecoveryToken.objects.get(token=token)
    except RecoveryToken.DoesNotExist:
        status = "Bad Token"
        return render(request, "agenda/pwreset.html", {"message":"", "status":status})

    errorMsg = ""
    if request.method == "POST":
        pw1 = request.POST["senha1"]
        pw2 = request.POST["senha2"]
        if (pw1 == pw2):
            status = "Done"
            recoveryToken.user.set_password(pw1)
            recoveryToken.user.save()
            recoveryToken.used=True
            recoveryToken.save()
            return render(request, "agenda/pwreset.html", {"message":"", "status":status})
        else:
            errorMsg = "A confirmação deve ser igual a senha digitada. "

    if recoveryToken.used==True:
        status = "Bad Token"
        return render(request, "agenda/pwreset.html", {"message":"", "status":status})
    else:
        return render(request, "agenda/pwreset.html", {"message":errorMsg, "status":status})

def ano(request, unidade=None ,year=None):
    # prev / next years
    if year: year = int(year)
    else:    year = time.localtime()[0]
    nowy, nowm = time.localtime()[:2]
    lst = []
    # create a list of months for each year, indicating ones that contain entries and current
    for y in [year, year+1]:
        mlst = []
        for n, month in enumerate(month_names):
            entry = current = False
            if y == nowy and n+1 == nowm:
                current = True
            mlst.append(dict(n=n+1, name=month, current=current))
        lst.append((y, mlst))

    espacosfisicos = EspacoFisico.objects.filter(unidade=unidade)

    return render_to_response("ano.html", dict(years=lst, user=request.user, year=year, espacosfisicos=espacosfisicos))

def locavel(request, tipo=None, locavel=None):
    specific = dict()
    if tipo == 'e':
        locavel = Equipamento.objects.get(id=locavel)
        specific['patrimonio'] = locavel.patrimonio
    elif tipo == 'f':
        locavel = EspacoFisico.objects.get(id=locavel)
        specific['capacidade'] = locavel.capacidade
    else:
        locavel = Servico.objects.get(id=locavel)
        profissionais = locavel.profissionais.all()
        names = list()
        for profissional in profissionais:
            names.append(profissional.first_name)
        specific['profissionais envolvidos'] = (", ").join(names)
    atividadesPermitidas = locavel.atividadesPermitidas.all()
    atividades = list()
    for atividade in atividadesPermitidas:
        atividades.append(atividade.nome)
    specific['atividades permitidas'] = (", ").join(atividades)
    if locavel.invisivel:
        return HttpResponseNotFound()
    responsaveis = locavel.responsavel.all()
    grupos = locavel.grupos.all()
    ret = request.META.get('HTTP_REFERER')
    return render(request, 'agenda/locavel.html',
                dict(tipo=tipo, locavel=locavel, responsaveis=responsaveis,
                    grupos=grupos, specific=specific, ret=ret))

def mes(request, tipo=None, espaco=None, year=None, month=None, change=None):
    if not month and not year:
        today = datetime.today()
        year = today.year
        month = today.month

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
    for day in month_days:
        entries = current = False
        if day:
            if tipo=="e":
                entries = ReservaEquipamento.objects.filter(data__year=year, data__month=month, data__day=day, locavel=espaco, estado="A")
            elif tipo == "f":
                entries = ReservaEspacoFisico.objects.filter(data__year=year, data__month=month, data__day=day, locavel=espaco, estado="A")
            elif tipo == "s":
                entries = ReservaServico.objects.filter(data__year=year, data__month=month, data__day=day, locavel=espaco, estado="A")

        if day == nday and year == nyear and month == nmonth:
            current = True

        lst[week].append((day, entries, current))
        if len(lst[week]) == 7:
            lst.append([])
            week += 1
    if(tipo=="e"):
        reservable = Equipamento.objects.get(id=espaco)
    elif tipo == 'f':
        reservable = EspacoFisico.objects.get(id=espaco)
    else:
        reservable = Servico.objects.get(id=espaco)
    return render(
            request,
            "agenda/mes.html",
            dict(
                espaco=reservable, year=year, month=month,
                user=request.user, month_days=lst, mname=month_names[month-1],
                tipo=tipo
                ))

def dia(request, espaco, year, month, day):
    """Entries for the day."""
    nyear, nmonth, nday = time.localtime()[:3]
    espacofisico = EspacoFisico.objects.get(id=espaco)
    reservas = ReservaEspacoFisico.objects.filter(data__year=year, data__month=month, data__day=day, espacoFisico=espaco).order_by("horaInicio")
    return render(request, "agenda/dia.html", dict(reservas=reservas, espaco=espacofisico, anovisualizacao=year ,mesvisualizacao=month, dia=day))


def espacos(request):
	espacos1 = EspacoFisico.objects.order_by("nome").all()
	ano = time.localtime()[0]
	mes = time.localtime()[1]
	return render(
            request,
            "agenda/espacos.html",
            dict(ano=ano, mes=mes, espacos=espacos1
                ))

def equipamentos(request):
    espacos1 = Equipamento.objects.order_by("nome").all()
    ano = time.localtime()[0]
    mes = time.localtime()[1]
    return render_to_response("espacos.html", {'ano': ano, 'mes': mes, 'espacos': espacos1})

def intermediaria(request):
    id_reservable = request.GET['id']
    data_numero = request.GET['data']
    try:
        horaInicio = request.GET['horaInicio']
        horaFim = request.GET['horaFim']
    except:
        horaInicio = None
        horaFim = None
    request.session['id_reservable'] = id_reservable
    data_string = str(data_numero)
    data = data_string[0]+data_string[1]+'/'+data_string[2]+data_string[3]+'/'+data_string[4]+data_string[5]+data_string[6]+data_string[7]
    request.session['data'] = data
    if horaInicio and horaFim:
        horaInicio = horaInicio[:2]+':'+horaInicio[2:]
        horaFim = horaFim[:2]+':'+horaFim[2:]
    request.session['horaInicio'] = horaInicio
    request.session['horaFim'] = horaFim
    data = {'success': True}
    return JsonResponse(data)

def filtroLocavelDisponivel(request, unit, tipo, sData, sHoraInicio, sHoraFim):
    data = datetime.strptime(sData, '%d%m%Y')
    horaInicio = datetime.strptime(sHoraInicio, '%H%M').time()
    horaFim = datetime.strptime(sHoraFim, '%H%M').time()
    atividade_dummy = Atividade.objects.create(nome='dummy', descricao='dummy')
    unit = Unidade.objects.get(id=unit)
    if tipo == 'f':
        query = unit.espacofisico_set.all()
        tipo_reserva = ReservaEspacoFisico
    elif tipo == 'e':
        query = unit.equipamento_set.all()
        tipo_reserva = ReservaEquipamento
    elif tipo == 's':
        query = unit.servico_set.all()
        tipo_reserva = ReservaServico

    dummy_user = User.objects.create(username='dummy_user')
    for locavel in query:
        reserva_dummy = tipo_reserva.objects.create(data=data, horaInicio=horaInicio, horaFim=horaFim, atividade=atividade_dummy, usuario=dummy_user, ramal=1, finalidade='1', locavel=locavel)
        error = dict()
        reserva_dummy.verificaChoque(error)
        if bool(error) or (locavel.invisivel and not(request.user.is_superuser or request.user in locavel.responsavel.all())):
            query = query.exclude(id=locavel.id)
        reserva_dummy.delete()

    dummy_user.delete()
    atividade_dummy.delete()
    return render(request, "agenda/search_result.html", dict(query=query, data=sData, horaInicio=sHoraInicio, horaFim=sHoraFim, tipo=tipo))

@login_required
def get_atividade_set(request):
    if request.method == 'POST':
        tipo = request.POST['title']
        locavel = request.POST['locavel']
        if unicode('espaço físico', 'utf-8') in tipo:
            locavel = EspacoFisico.objects.get(nome=locavel)
            ma = admin.EspacoFisicoAdmin(EspacoFisico, AdminSite())
        elif 'equipamento' in tipo:
            locavel = Equipamento.objects.get(nome=locavel)
            ma = admin.EquipamentoAdmin(Equipamento, AdminSite())
        elif unicode('serviço', 'utf-8') in tipo:
            locavel = Servico.objects.get(nome=locavel)
            ma = admin.ServicoAdmin(Servico, AdminSite())
        query = ma.get_queryset(request)
        if locavel in query:
            atividades = locavel.atividadesPermitidas.all()
            n = list()
            i = list()
            for atividade in atividades:
                n.append(atividade.nome)
                i.append(atividade.id)
            data = {'atividades': n, 'ids': i}
            return JsonResponse(data)
    return HttpResponseNotFound()

@login_required
def get_pending_reserves(request):

    def check_conflicts(reserves, starting_time, ending_time):
        conflict_ids = list()
        conflict_names = list()
        for r in reserves:
            if  (
                (r.estado == 'E') and
                (
                (ending_time  > r.horaInicio and ending_time < r.horaFim) or
                (starting_time > r.horaInicio and starting_time < r.horaFim ) or
                (starting_time == r.horaInicio and ending_time == r.horaFim) or
                (r.horaInicio > starting_time and r.horaInicio < ending_time) or
                (starting_time < r.horaFim < ending_time)
                )
                ):
                conflict_ids.append(r.id)
                conflict_names.append(r.usuario.username)
        return (conflict_ids,conflict_names)

    if request.method != 'POST':
        return HttpResponseNotFound()

    #get request variables
    reservable_type = request.POST['reservable_type']
    reservable_name = request.POST['reservable_name']
    current_reserve_id = request.POST['current_reserve_id']
    date = request.POST['date']
    date = datetime.strptime(date, '%d/%m/%Y').date()
    starting_time = request.POST['starting_time']
    starting_time = datetime.strptime(starting_time, '%H:%M').time()
    ending_time = request.POST['ending_time']
    ending_time = datetime.strptime(ending_time, '%H:%M').time()
    if unicode('espaço físico', 'utf-8') in reservable_type:
        reservable = EspacoFisico.objects.get(nome=reservable_name)
        reserve_set = reservable.reservaespacofisico_set
    elif 'equipamento' in reservable_type:
        reservable = Equipamento.objects.get(nome=reservable_name)
        reserve_set = reservable.reservaequipamento_set
    elif unicode('serviço', 'utf-8') in reservable_type:
        reservable = Servico.objects.filter(data=date)
        reserve_set = reservable.reservaservico_set

    # get conflicting reserves
    conflict_reserves_ids = list()
    conflict_reserves_names = list()

    if 'ending_date' in request.POST:
        ending_date = request.POST['ending_date']
        ending_date = datetime.strptime(ending_date, '%d/%m/%Y').date()
        checked_week_days = request.POST.getlist('checked_week_days[]')
        checked_week_days = map(int, checked_week_days)
        current_reserve = reserve_set.get(id=current_reserve_id)

        recurrent_reserve = current_reserve.recorrencia.get_reserves()
        aux_date = recurrent_reserve[0].data
        recurrent_reserve_ids = [x.id for x in recurrent_reserve]
        while ending_date >= aux_date:
            reserves = reserve_set.filter(data=aux_date).exclude(id=current_reserve_id)
            for _id in recurrent_reserve_ids:
                reserves = reserves.exclude(id=_id)
            if aux_date.weekday() in checked_week_days:
                conflict_reserves_ids_aux, conflict_reserves_names_aux = check_conflicts(reserves, starting_time, ending_time)
                conflict_reserves_ids = conflict_reserves_ids + conflict_reserves_ids_aux
                conflict_reserves_names = conflict_reserves_names + conflict_reserves_names_aux
            aux_date += timedelta(days=1)
    else:   # a non recurrent reserve is being made case
            # no ending_date was passed as element of the request

        if current_reserve_id != "NaN":
            reserves = reserve_set.filter(data=date).exclude(id=current_reserve_id)
            conflict_reserves_ids, conflict_reserves_names = check_conflicts(reserves, starting_time, ending_time)
        else:
            pass

    if conflict_reserves_ids and conflict_reserves_names:
        data = {'conflict_reserves': True, 'conflict_reserves_ids': conflict_reserves_ids, 'conflict_reserves_names': conflict_reserves_names}
    else:
        data = {'conflict_reserves': False}
    return JsonResponse(data)

def faq(request):
    if request.method == 'GET':
        faq_pages = FlatPage.objects.filter(url__icontains='faq')
        return render(request, "agenda/faq.html", dict(pages=faq_pages))
    elif request.method == 'POST':
        filter_type = request.POST['filterType']
        filter_text = request.POST['filter']
        if 'title-filter' == filter_type:
            query = FlatPage.objects.filter(url__contains='faq', title__icontains=filter_text)
        elif 'content-filter' == filter_type: # have the words typed, not necessarily in order
            filter_text = filter_text.split(' ')
            query = FlatPage.objects.filter(url__contains='faq', content__icontains=filter_text[0])  # get a base query
            filter_text.pop(0)  #remove first, since it's already been filtered
            for word in filter_text:  # filter the remaining words
                query = query.filter(content__icontains=word)
        faq_items = list()
        for query_item in query:
            faq_items.append(query_item.title)
        data = {'faqItems': faq_items}
        return JsonResponse(data)

def _calendar(request, tipo=None, espaco=None, year=None, month=None, change=None):
    if not month and not year:
        today = datetime.today()
        year = today.year
        month = today.month

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
    for day in month_days:
        entries = current = False
        if day:
            if tipo=="e":
                entries = ReservaEquipamento.objects.filter(data__year=year, data__month=month, data__day=day, locavel=espaco, estado="A")
            elif tipo == "f":
                entries = ReservaEspacoFisico.objects.filter(data__year=year, data__month=month, data__day=day, locavel=espaco, estado="A")
            elif tipo == "s":
                entries = ReservaServico.objects.filter(data__year=year, data__month=month, data__day=day, locavel=espaco, estado="A")

        if day == nday and year == nyear and month == nmonth:
            current = True

        lst[week].append((day, entries, current))
        if len(lst[week]) == 7:
            lst.append([])
            week += 1
    if(tipo=="e"):
        reservable = Equipamento.objects.get(id=espaco)
    elif tipo == 'f':
        reservable = EspacoFisico.objects.get(id=espaco)
    else:
        reservable = Servico.objects.get(id=espaco)
    return render(
            request,
            "agenda/calendar.html",
            dict(
                espaco=reservable, year=year, month=month,
                user=request.user, month_days=lst, mname=month_names[month-1],
                tipo=tipo
                ))
def login_email(request, template_name=None):
    if request.POST:
        email = request.POST['email']
        password = request.POST['password']
        next = request.POST["next"]
        try:
            username = User.objects.filter(email=email.lower())[0].username
        except:
            username = None

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request,user)
        else:
            return HttpResponseRedirect("Invalid username or password")
        if next:
            return redirect(next)
    return render(request,"agenda/login.html", {'next': request.GET.get("next", "")})
