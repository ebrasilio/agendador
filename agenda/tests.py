from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.contrib.admin.sites import AdminSite
from datetime import datetime
from datetime import timedelta

from .forms import *
from .models import *
from .admin import *

class MockRequest:
    pass
request = MockRequest()
class AdminViewPermissionsTests(TestCase):

    def create_preset(self):
        # Create users with different prioritys
        # Also gives them all permissions and staff so they can see admin page
        permissions = Permission.objects.all()
        common = User.objects.create_user('common', password='a')
        common.is_staff=True
        common.user_permissions.set(permissions)
        common.save()
        item_responsable = User.objects.create_user('item_responsable', password='a')
        item_responsable.is_staff=True
        item_responsable.user_permissions.set(permissions)
        item_responsable.save()
        sub_unit_responsable = User.objects.create_user('sub_unit_responsable', password='a')
        sub_unit_responsable.is_staff=True
        sub_unit_responsable.user_permissions.set(permissions)
        sub_unit_responsable.save()
        unit_responsable = User.objects.create_user('unit_responsable', password='a')
        unit_responsable.is_staff=True
        unit_responsable.user_permissions.set(permissions)
        unit_responsable.save()
        superuser = User.objects.create_user('superuser', password='a')
        superuser.is_superuser=True
        superuser.is_staff=True
        superuser.save()

        # Create units to their respective responsable
        parentUnit = Unidade.objects.create(sigla='pu', nome='parent unit', descricao='test')
        parentUnit.save()
        parentUnit.responsavel.add(unit_responsable)
        childUnit = Unidade.objects.create(sigla='cu', nome='child unit', unidadePai=parentUnit, descricao='test')
        parentUnit.save()
        childUnit.responsavel.add(sub_unit_responsable)

        # Create a room and a equipment for each user (except common)
        room0 = EspacoFisico.objects.create(nome='room0', descricao='test', unidade=childUnit, capacidade=0)
        room0.save()
        room0.responsavel.add(item_responsable)
        equipment0 = Equipamento.objects.create(nome='equipment0', descricao='test', unidade=childUnit, patrimonio=0)
        equipment0.save()
        equipment0.responsavel.add(item_responsable)
        room1 = EspacoFisico.objects.create(nome='room1', descricao='test', unidade=childUnit, capacidade=0)
        room1.save()
        room1.responsavel.add(sub_unit_responsable)
        equipment1 = Equipamento.objects.create(nome='equipment1', descricao='test', unidade=childUnit, patrimonio=0)
        equipment1.save()
        equipment1.responsavel.add(sub_unit_responsable)
        room2 = EspacoFisico.objects.create(nome='room2', descricao='test', unidade=parentUnit, capacidade=0)
        room2.save()
        room2.responsavel.add(unit_responsable)
        equipment2 = Equipamento.objects.create(nome='equipment2', descricao='test', unidade=parentUnit, patrimonio=0)
        equipment2.save()
        equipment2.responsavel.add(unit_responsable)

        # Create a activitie (required for reserve)
        activitie = Atividade.objects.create(nome='activitie', descricao='default')

        # Create a reserve for both room and equipment for each user
        reserve_room0 = ReservaEspacoFisico.objects.create(data='1000-10-10', horaInicio='00:00', horaFim='00:00', atividade=activitie, usuario=common, ramal=0, finalidade='t', locavel=room0)
        reserve_room0.save()
        reserve_equipment0 = ReservaEquipamento.objects.create(data='1000-10-10', horaInicio='00:00', horaFim='00:00', atividade=activitie, usuario=common, ramal=0, finalidade='t', locavel=equipment0)
        reserve_equipment0.save()
        reserve_room1 = ReservaEspacoFisico.objects.create(data='1000-10-10', horaInicio='00:00', horaFim='00:00', atividade=activitie, usuario=item_responsable, ramal=0, finalidade='t', locavel=room1)
        reserve_room1.save()
        reserve_equipment1 = ReservaEquipamento.objects.create(data='1000-10-10', horaInicio='00:00', horaFim='00:00', atividade=activitie, usuario=item_responsable, ramal=0, finalidade='t', locavel=equipment1)
        reserve_equipment1.save()
        reserve_room2 = ReservaEspacoFisico.objects.create(data='1000-10-10', horaInicio='00:00', horaFim='00:00', atividade=activitie, usuario=sub_unit_responsable, ramal=0, finalidade='t', locavel=room2)
        reserve_room2.save()
        reserve_equipment2 = ReservaEquipamento.objects.create(data='1000-10-10', horaInicio='00:00', horaFim='00:00', atividade=activitie, usuario=sub_unit_responsable, ramal=0, finalidade='t', locavel=equipment2)
        reserve_equipment2.save()

        return {'rooms': [room0, room1, room2],
                'equipments': [equipment0, equipment1, equipment2],
                'room_reserves': [reserve_room0, reserve_room1, reserve_room2],
                'equipment_reserves': [reserve_equipment0, reserve_equipment1, reserve_equipment2]}

    def check_items(self, user, items, room=True, equipment=True):
        request.user = user
        if room:
            ma = EspacoFisicoAdmin(EspacoFisico, AdminSite())
            rooms = list(ma.get_queryset(request))
            self.assertItemsEqual(rooms, items['rooms'])
        if equipment:
            ma = EquipamentoAdmin(Equipamento, AdminSite())
            equipments = list(ma.get_queryset(request))
            self.assertItemsEqual(equipments, items['equipments'])
        ma  = ReservaEspacoFisicoAdmin(ReservaEspacoFisico, AdminSite())
        room_reserves = list(ma.get_queryset(request))
        self.assertItemsEqual(room_reserves, items['room_reserves'])
        ma = ReservaEquipamentoAdmin(ReservaEquipamento, AdminSite())
        equipment_reserves = list(ma.get_queryset(request))
        self.assertItemsEqual(equipment_reserves, items['equipment_reserves'])

    def test_admin_view_filter(self):
        print 'TESTING ADMIN VIEW FILTER'
        items = self.create_preset()

        # First superuser, he must see everything in items
        user = User.objects.get(username='superuser')
        self.check_items(user, items)
        print '-SUPERUSER CASE PASS'

        # Unit_responsable also must see every item, even though he's not responsable for reserves
        user = User.objects.get(username='unit_responsable')
        self.check_items(user, items)
        print '-UNIT RESPONSABLE CASE PASS'

        # Sub_unit_responsable must be able to see everything but room and equipment 2
        user = User.objects.get(username='sub_unit_responsable')
        request.user = user
        ma = EspacoFisicoAdmin(EspacoFisico, AdminSite())
        rooms = list(ma.get_queryset(request))
        self.assertEqual(2, len(rooms))
        temp = list(items['rooms'])
        temp.pop()
        self.assertItemsEqual(temp, rooms)
        ma = EquipamentoAdmin(Equipamento, AdminSite())
        equipments = list(ma.get_queryset(request))
        self.assertEqual(2, len(equipments))
        temp = list(items['equipments'])
        temp.pop()
        self.assertItemsEqual(temp, equipments)
        self.check_items(user, items, room=False, equipment=False)
        print '-SUB UNIT RESPONSABLE CASE PASS'

        # Item responsable can only see rooms and equipments 0 and reserves 0 and 1
        user = User.objects.get(username='item_responsable')
        request.user = user
        ma = EspacoFisicoAdmin(EspacoFisico, AdminSite())
        rooms = list(ma.get_queryset(request))
        self.assertEqual(1, len(rooms))
        temp = list(items['rooms'])
        temp.pop()
        temp.pop()
        self.assertItemsEqual(temp, rooms)
        ma = EquipamentoAdmin(Equipamento, AdminSite())
        equipments = list(ma.get_queryset(request))
        self.assertEqual(1, len(equipments))
        temp = list(items['equipments'])
        temp.pop()
        temp.pop()
        self.assertItemsEqual(temp, equipments)
        ma = ReservaEspacoFisicoAdmin(ReservaEspacoFisico, AdminSite())
        room_reserves = list(ma.get_queryset(request))
        self.assertEqual(2, len(room_reserves))
        temp = list(items['room_reserves'])
        temp.pop()
        self.assertItemsEqual(temp, room_reserves)
        ma = ReservaEquipamentoAdmin(ReservaEquipamento, AdminSite())
        equipment_reserves = list(ma.get_queryset(request))
        self.assertEqual(2, len(equipment_reserves))
        temp = list(items['equipment_reserves'])
        temp.pop()
        self.assertItemsEqual(temp, equipment_reserves)
        print '-ITEM RESPONSABLE CASE PASS'

        # Common user can only see reserves 0
        user = User.objects.get(username='common')
        request.user = user
        ma = EspacoFisicoAdmin(EspacoFisico,AdminSite())
        rooms = list(ma.get_queryset(request))
        self.assertEqual(0, len(rooms))
        ma = EquipamentoAdmin(Equipamento, AdminSite())
        equipments = list(ma.get_queryset(request))
        self.assertEqual(0, len(equipments))
        ma = ReservaEquipamentoAdmin(ReservaEquipamento, AdminSite())
        equipment_reserves = list(ma.get_queryset(request))
        self.assertEqual(1, len(equipment_reserves))
        temp = list(items['equipment_reserves'])
        temp.pop()
        temp.pop()
        self.assertItemsEqual(temp, equipment_reserves)
        ma = ReservaEspacoFisicoAdmin(ReservaEspacoFisico, AdminSite())
        room_reserves = list(ma.get_queryset(request))
        self.assertEqual(1, len(room_reserves))
        temp = list(items['room_reserves'])
        temp.pop()
        temp.pop()
        self.assertItemsEqual(temp, room_reserves)
        print '-COMMON USER CASE PASS'

class UserFilterTests(TestCase):
    def createPreset(self):
        # Create one superuser to be responsable for everything
        superuser = User.objects.create(username='superuser', password='a')
        # Create the units in a binary tree fashion
        root = Unidade.objects.create(sigla='rt', nome='root', descricao='test')
        root.save()
        root.responsavel.add(superuser)
        child_left = Unidade.objects.create(sigla='cl', nome='child_left', unidadePai=root, descricao='test')
        child_left.save()
        child_left.responsavel.add(superuser)
        child_left.responsavel.add(superuser)
        child_left_left = Unidade.objects.create(sigla='cll', nome='child_left_left', unidadePai=child_left, descricao='q')
        child_left_left.save()
        child_left_left.responsavel.add(superuser)
        child_left_right = Unidade.objects.create(sigla='clr', nome='child_left_right', unidadePai=child_left, descricao='')
        child_left_right.save()
        child_left_right.responsavel.add(superuser)
        child_right = Unidade.objects.create(sigla='cr', nome='child_right', unidadePai=root, descricao='q')
        child_right.save()
        child_left_right.responsavel.add(superuser)
        child_right_left = Unidade.objects.create(sigla='crl', nome='child_right_left', unidadePai=child_right, descricao='q')
        child_right_left.save()
        child_right_left.responsavel.add(superuser)
        child_right_right = Unidade.objects.create(sigla='crr', nome='child_right_right', unidadePai=child_right, descricao='q')
        child_right_right.save()
        child_right_right.responsavel.add(superuser)
        child_right_right_left = Unidade.objects.create(sigla='crrl', nome='child_right_right_left', unidadePai=child_right_right, descricao='q')
        child_right_right_left.save()
        child_right_right_left.responsavel.add(superuser)

        # Create equipments and places with different characteristics in "leaf" units
        invisible_place = EspacoFisico.objects.create(nome='inivisible_place', descricao='q', unidade=child_left_left, invisivel=True, localizacao='q', capacidade=1)
        invisible_place.save()
        invisible_equipment = Equipamento.objects.create(nome='invisible_equipment', descricao='q', unidade=child_left_left, invisivel=True, localizacao='q', patrimonio=3)
        invisible_equipment.save()
        group_place = EspacoFisico.objects.create(nome='group_place', descricao='q', unidade=child_left_left, localizacao='q', capacidade=2)
        group_place.save()
        group_equipment = Equipamento.objects.create(nome='group_equipment', descricao='q', unidade=child_left_left, localizacao='q', patrimonio=2)
        group_equipment.save()
        place0 = EspacoFisico.objects.create(nome='place0', descricao='q', unidade=child_left_right, localizacao='q', capacidade=2)
        place0.save()
        equipment0 = Equipamento.objects.create(nome='equipment0', descricao='q', unidade=child_left_right, localizacao='q', patrimonio=2)
        equipment0.save()
        place1 = EspacoFisico.objects.create(nome='place1', descricao='q', unidade=child_right_left, localizacao='q', capacidade=2)
        place1.save()
        equipment1 = Equipamento.objects.create(nome='equipment1', descricao='q', unidade=child_right_left, localizacao='q', patrimonio=1)
        equipment1.save()
        place2 = EspacoFisico.objects.create(nome='place2', descricao='q', unidade=child_right_right_left, localizacao='q', capacidade=2)
        place2.save()
        equipment2 = Equipamento.objects.create(nome='equipment2', descricao='q', unidade=child_right_right_left, localizacao='q', patrimonio=2)
        equipment2.save()
        blocked_place = EspacoFisico.objects.create(nome='blocked_place', descricao='q', unidade=child_right_right, bloqueado=True, localizacao='q', capacidade=2)
        blocked_place.save()
        blocked_equipment = Equipamento.objects.create(nome='blocked_equipment', descricao='q', unidade=child_right_right, bloqueado=True, localizacao=2, patrimonio=2)
        blocked_equipment.save()

        # Create common users
        root_user = User.objects.create(username='root_user', password='a')
        root_user.save()
        child_left_user = User.objects.create(username='child_left_user', password='a')
        child_left_user.save()
        root_group_user = User.objects.create(username='root_group_user', password='a')
        root_group_user.save()

        # Creat unit groups and add people, units and place/equiptment to it
        group_x = Group.objects.create(name='group_x')
        group_x.unidade_set.add(root)
        group_x.user_set.add(root_user)
        root.grupos.add(group_x)
        group_x.user_set.add(root_group_user)

        group_y = Group.objects.create(name='group_y')
        group_y.unidade_set.add(child_left)
        group_y.user_set.add(child_left_user)
        child_left.grupos.add(group_y)

        child_right_right.grupos.add(group_x)
        child_right_right.grupos.add(group_y)
        group_x.unidade_set.add(child_right_right)
        group_y.unidade_set.add(child_right_right)

        permission = Group.objects.create(name='permission')
        permission.espacofisico_set.add(group_place)
        group_place.grupos.add(permission)
        permission.equipamento_set.add(group_equipment)
        group_equipment.grupos.add(permission)
        permission.user_set.add(root_group_user)

        return {
            'places': [invisible_place, group_place, place0, place1, place2, blocked_place],
            'equipments': [invisible_equipment, group_equipment, equipment0, equipment1, equipment2, blocked_equipment]
        }

    def makeChecks(self, items, user, pop_items):
        # pop items user shouldn't see
        places = list(items['places'])
        equipments = list(items['equipments'])
        for item in pop_items:
            places.pop(item)
            equipments.pop(item)

        # Create user, get options and compare
        user = User.objects.get(username=user)
        request.user = user
        ma = EspacoFisicoAdmin(EspacoFisico, AdminSite())
        bd_places = list(ma.get_queryset(request))
        self.assertItemsEqual(bd_places, places)
        ma = EquipamentoAdmin(Equipamento, AdminSite())
        bd_equipments = list(ma.get_queryset(request))
        self.assertItemsEqual(bd_equipments, equipments)

    def test_user_groups_filter(self):
        items = self.createPreset()

        print '-TESTING GROUP FILTERS'

        # Superuser must see everything since he's responsable
        self.makeChecks(items, 'superuser', [])
        # Root user (whithout group) must see item 2, 3 and blocked
        self.makeChecks(items, 'root_user', [0, 0, 0])
        # Child_left user must see item 1, 3 and blocked
        self.makeChecks(items, 'child_left_user', [0, 0, 1])
        # root_group_user must see item 2, 3, blocked and group
        self.makeChecks(items, 'root_group_user', [0, 1])

        print '-GROUP FILTERS PASS'

class ReserveFormests(TestCase):

    def create_preset(self):

        # create models
        activitie = Atividade.objects.create(nome='activitie', descricao='default')
        activitie.save()
        responsable = User.objects.create_user('responsable', password='a')
        responsable.save()
        unit = Unidade.objects.create(sigla='pru', nome='unit', descricao='test')
        unit.save()
        physical_space = EspacoFisico.objects.create(nome='physical_space', descricao='q', unidade=unit, bloqueado=False, localizacao='q', capacidade=2)
        physical_space.responsavel.add(responsable)
        physical_space.atividadesPermitidas.add(activitie)
        physical_space.save()
        equipment = Equipamento.objects.create(nome='equipment', descricao='q', unidade=unit, localizacao='q', patrimonio=2)
        equipment.responsavel.add(responsable)
        equipment.atividadesPermitidas.add(activitie)
        equipment.save()
        no_permission_user = User.objects.create_user('no_permission_user', password='a')
        no_permission_user.save()
        permission_user = User.objects.create_user('permission_user', password='a')
        permission_user.save()

        # give permissions so users can create stuff
        permissions = Permission.objects.all()
        responsable.user_permissions.set(permissions)
        responsable.save()
        no_permission_user.user_permissions.set(permissions)
        no_permission_user.save()
        permission_user.user_permissions.set(permissions)
        permission_user.save()

        # create a group to the unit
        group = Group.objects.create(name='group')
        unit.grupos.add(group)
        group.user_set.add(permission_user)
        unit.save()
        group.save()

    def create_form(self, reserve_type, form_type, status, date, recurrent, ending_date, starting_time, ending_time, reservable, user, instance=None):
        date = datetime.strptime(date, '%d/%m/%Y').date()
        if ending_date:
            ending_date = datetime.strptime(ending_date, '%d/%m/%Y').date()
        starting_time = datetime.strptime(starting_time, '%H:%M').time()
        ending_time = datetime.strptime(ending_time, '%H:%M').time()
        activitie = Atividade.objects.get(nome='activitie')
        ramal = 6
        reason = 'test'
        request.user = user
        request.session = dict()
        def a(a):
            return ''
        request.build_absolute_uri = a
        form = form_type(data={
            'estado': status,
            'data': date,
            'recorrente': recurrent,
            'dataFim': ending_date,
            'horaInicio': starting_time,
            'horaFim': ending_time,
            'locavel': reservable.pk,
            'atividade': activitie.pk,
            'usuario': user.pk,
            'ramal': ramal,
            'finalidade': reason,
        }, initial={'recorrente': recurrent}, request=request, instance=instance)
        return form

    def test_create_reserve_form(self):
        print '-TESTING RESERVE FORM'
        self.create_preset()
        responsable = User.objects.get(username='responsable')
        permission_user = User.objects.get(username='permission_user')
        no_permission_user = User.objects.get(username='no_permission_user')
        physical_space = EspacoFisico.objects.get(nome='physical_space')
        equipment = Equipamento.objects.get(nome='equipment')

        self.status_test(responsable, permission_user, no_permission_user, physical_space, equipment)
        self.recurrent_reserve_test(responsable, permission_user, no_permission_user, physical_space, equipment)
        print '-RESERVE FORM TEST PASSED'

    def status_test(self, responsable, permission_user, no_permission_user, physical_space, equipment):
        print '--TESTING AUTO APPROVE'
        # Test responsable making reserve
        form = self.create_form(ReservaEspacoFisico, ReservaEspacoFisicoAdminForm, 'E', '18/06/9999', False, None, '00:01', '00:02', physical_space, responsable)
        form.save()
        instance = ReservaEspacoFisico.objects.all()[0]
        self.assertEqual(instance.estado, 'A')
        instance.delete()
        form = self.create_form(ReservaEquipamento, ReservaEquipamentoAdminForm, 'E', '18/06/9999', False, None, '00:01', '00:02', equipment, responsable)
        form.save()
        instance = ReservaEquipamento.objects.all()[0]
        self.assertEqual(instance.estado, 'A')
        instance.delete()

        # Test user in group making reserve
        form = self.create_form(ReservaEspacoFisico, ReservaEspacoFisicoAdminForm, 'E', '18/06/9999', False, None, '00:01', '00:02', physical_space, permission_user)
        form.save()
        instance = ReservaEspacoFisico.objects.all()[0]
        self.assertEqual(instance.estado, 'A')
        instance.delete()
        form = self.create_form(ReservaEquipamento, ReservaEquipamentoAdminForm, 'E', '18/06/9999', False, None, '00:01', '00:02', equipment, permission_user)
        form.save()
        instance = ReservaEquipamento.objects.all()[0]
        self.assertEqual(instance.estado, 'A')
        instance.delete()

        # Test user not in group making reserve
        form = self.create_form(ReservaEspacoFisico, ReservaEspacoFisicoAdminForm, 'E', '18/06/9999', False, None, '00:01', '00:02', physical_space, no_permission_user)
        form.save()
        instance = ReservaEspacoFisico.objects.all()[0]
        self.assertEqual(instance.estado, 'E')
        instance.delete()
        form = self.create_form(ReservaEquipamento, ReservaEquipamentoAdminForm, 'E', '18/06/9999', False, None, '00:01', '00:02', equipment, no_permission_user)
        form.save()
        instance = ReservaEquipamento.objects.all()[0]
        self.assertEqual(instance.estado, 'E')
        instance.delete()

        print '--AUTO APPROVE TEST PASSED'

    def recurrent_reserve_test(self, responsable, permission_user, no_permission_user, physical_space, equipment):
        # create a recurrent reserve
        print '--TESTING CREATE RECURRENT RESERVE'
        form = self.create_form(ReservaEspacoFisico, ReservaEspacoFisicoAdminForm, 'E', '01/06/9999', True, '22/06/9999', '00:01', '00:02', physical_space, no_permission_user)
        form.save()
        query = ReservaEspacoFisico.objects.all()
        self.assertEqual(len(query), 4)
        current_date = datetime.strptime('01/06/9999', '%d/%m/%Y').date()
        for reserve in query:
            self.assertEqual(reserve.data, current_date)
            current_date = current_date + timedelta(days=7)
        form = self.create_form(ReservaEquipamento, ReservaEquipamentoAdminForm, 'E', '01/06/9999', True, '22/06/9999', '00:01', '00:02', equipment, no_permission_user)
        form.save()
        query = ReservaEquipamento.objects.all()
        self.assertEqual(len(query), 4)
        current_date = datetime.strptime('01/06/9999', '%d/%m/%Y').date()
        for reserve in query:
            self.assertEqual(reserve.data, current_date)
            current_date = current_date + timedelta(days=7)
        print '--CREATE RECURRENT RESERVE TEST PASSED'

        # edit one reserve must aplly to all
        print '--TESTING EDIT RECURRENT RESERVE'
        instance = ReservaEspacoFisico.objects.all()[0]
        form = self.create_form(ReservaEspacoFisico, ReservaEspacoFisicoAdminForm, 'A', '01/06/9999', True, '22/06/9999', '00:01', '00:02', physical_space, no_permission_user, instance)
        form.is_valid()
        form.save()
        query = ReservaEspacoFisico.objects.all()
        for reserve in query:
            self.assertEqual(reserve.estado, 'A')
        instance = ReservaEquipamento.objects.all()[0]
        form = self.create_form(ReservaEquipamento, ReservaEquipamentoAdminForm, 'A', '01/06/9999', True, '22/06/9999', '00:01', '00:02', equipment, no_permission_user, instance)
        form.is_valid()
        form.save()
        query = ReservaEquipamento.objects.all()
        for reserve in query:
            self.assertEqual(reserve.estado, 'A')
        print '--EDIT RECURRENT RESERVE TEST PASSED'