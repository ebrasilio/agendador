# -*- coding: utf-8 -*-
"""CAS authentication backend"""
from __future__ import unicode_literals

import datetime

from django.utils.six.moves import urllib_parse
from django.utils.six.moves.urllib_request import urlopen, Request
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.conf import settings

from uuid import uuid4

from django_cas_ng.signals import cas_user_authenticated

User = get_user_model()

__all__ = ['CASBackend']


def _verify_cas1(ticket, service):
    """Verifies CAS 1.0 authentication ticket.

    Returns username on success and None on failure.
    """

    params = [('ticket', ticket), ('service', service)]
    url = (urllib_parse.urljoin(settings.CAS_SERVER_URL, 'validate') + '?' +
           urllib_parse.urlencode(params))
    page = urlopen(url)
    try:
        verified = page.readline().strip()
        if verified == 'yes':
            return page.readline().strip(), None
        else:
            return None, None
    finally:
        page.close()


def _verify_cas2(ticket, service):
    """Verifies CAS 2.0+ XML-based authentication ticket.

    Returns username on success and None on failure.
    """
    try:
        from xml.etree import ElementTree
    except ImportError:
        from elementtree import ElementTree

    params = [('ticket', ticket), ('service', service)]
    url = (urllib_parse.urljoin(settings.CAS_SERVER_URL, 'serviceValidate') + '?' +
           urllib_parse.urlencode(params))
    page = urlopen(url)
    try:
        response = page.read()
        tree = ElementTree.fromstring(response)
        if tree[0].tag.endswith('authenticationSuccess'):
            return tree[0][0].text, None
        else:
            return None, None
    finally:
        page.close()


def get_cas3_verification_response(ticket, service):
    params = [('ticket', ticket), ('service', service)]
    base_url = urllib_parse.urljoin(settings.CAS_SERVER_URL, 'proxyValidate')
    url = base_url + '?' + urllib_parse.urlencode(params)
    page = urlopen(url)
    return page.read()


def verify_cas3_response(response):
    user = None
    attributes = {}

    try:
        from xml.etree import ElementTree
    except ImportError:
        from elementtree import ElementTree

    tree = ElementTree.fromstring(response)

    if tree[0].tag.endswith('authenticationSuccess'):
        for element in tree[0]:
            if element.tag.endswith('user'):
                user = element.text
            elif element.tag.endswith('attributes'):
                for attribute in element:
                    tag = attribute.tag.split("}").pop()
                    if tag in attributes:
                        if isinstance(attributes[tag], list):
                            attributes[tag].append(attribute.text)
                        else:
                            attributes[tag] = [attributes[tag]]
                            attributes[tag].append(attribute.text)
                    else:
                        attributes[tag] = attribute.text

    return user, attributes


def _verify_cas3(ticket, service):
    """Verifies CAS 3.0+ XML-based authentication ticket and returns extended attributes.

    Returns username on success and None on failure.
    """
    response = get_cas3_verification_response(ticket, service)
    return verify_cas3_response(response)


SAML_ASSERTION_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
<SOAP-ENV:Header/>
<SOAP-ENV:Body>
<samlp:Request xmlns:samlp="urn:oasis:names:tc:SAML:1.0:protocol"
MajorVersion="1"
MinorVersion="1"
RequestID="{request_id}"
IssueInstant="{timestamp}">
<samlp:AssertionArtifact>{ticket}</samlp:AssertionArtifact></samlp:Request>
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>"""


def get_saml_assertion(ticket):
    """
    http://www.jasig.org/cas/protocol#samlvalidate-cas-3.0

    SAML request values:

    RequestID [REQUIRED]:
        unique identifier for the request
    IssueInstant [REQUIRED]:
        timestamp of the request
    samlp:AssertionArtifact [REQUIRED]:
        the valid CAS Service Ticket obtained as a response parameter at login.
    """
    # RequestID [REQUIRED] - unique identifier for the request
    request_id = uuid4()

    # e.g. 2014-06-02T09:21:03.071189
    timestamp = datetime.datetime.now().isoformat()

    return SAML_ASSERTION_TEMPLATE.format(
        request_id=request_id,
        timestamp=timestamp,
        ticket=ticket,
    )


SAML_1_0_NS = 'urn:oasis:names:tc:SAML:1.0:'
SAML_1_0_PROTOCOL_NS = '{' + SAML_1_0_NS + 'protocol' + '}'
SAML_1_0_ASSERTION_NS = '{' + SAML_1_0_NS + 'assertion' + '}'


def _verify_cas2_saml(ticket, service):
    """Verifies CAS 3.0+ XML-based authentication ticket and returns extended attributes.

    @date: 2011-11-30
    @author: Carlos Gonzalez Vila <carlewis@gmail.com>

    Returns username and attributes on success and None,None on failure.
    """

    try:
        from xml.etree import ElementTree
    except ImportError:
        from elementtree import ElementTree

    # We do the SAML validation
    headers = {
        'soapaction': 'http://www.oasis-open.org/committees/security',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'accept': 'text/xml',
        'connection': 'keep-alive',
        'content-type': 'text/xml; charset=utf-8',
    }
    params = [('TARGET', service)]

    saml_validat_url = urllib_parse.urljoin(
        settings.CAS_SERVER_URL, 'samlValidate',
    )

    url = Request(
        saml_validat_url + '?' + urllib_parse.urlencode(params),
        '',
        headers,
    )
    page = urlopen(url, data=get_saml_assertion(ticket))

    try:
        user = None
        attributes = {}
        response = page.read()
        tree = ElementTree.fromstring(response)
        # Find the authentication status
        success = tree.find('.//' + SAML_1_0_PROTOCOL_NS + 'StatusCode')
        if success is not None and success.attrib['Value'] == 'samlp:Success':
            # User is validated
            attrs = tree.findall('.//' + SAML_1_0_ASSERTION_NS + 'Attribute')
            for at in attrs:
                if 'uid' in list(at.attrib.values()):
                    user = at.find(SAML_1_0_ASSERTION_NS + 'AttributeValue').text
                    attributes['uid'] = user
                    values = at.findall(SAML_1_0_ASSERTION_NS + 'AttributeValue')
                    if len(values) > 1:
                        values_array = []
                        for v in values:
                            values_array.append(v.text)
                            attributes[at.attrib['AttributeName']] = values_array
                    else:
                        attributes[at.attrib['AttributeName']] = values[0].text
        return user, attributes
    finally:
        page.close()

def _verify_cas3_saml(ticket, service):
    """CAS3 + SAML"""

    try:
        from xml.etree import ElementTree
    except ImportError:
        from elementtree import ElementTree

    # We do the SAML validation
    headers = {
        'soapaction': 'http://www.oasis-open.org/committees/security',
        'cache-control': 'no-cache',
        'pragma': 'no-cache',
        'accept': 'text/xml',
        'connection': 'keep-alive',
        'content-type': 'text/xml; charset=utf-8',
    }
    params = [('ticket', ticket), ('service', service), ('TARGET', service)]

    saml_validat_url = urllib_parse.urljoin(
        settings.CAS_SERVER_URL, 'samlValidate',
    )
    # teste
    #saml_validat_url = urllib_parse.urljoin(settings.CAS_SERVER_URL, 'proxyValidate',)

    url = Request(
        saml_validat_url + '?' + urllib_parse.urlencode(params),
        '',
        headers,
    )
    page = urlopen(url, data=get_saml_assertion(ticket))

    try:
        user = None
        attributes = {}
        response = page.read()#.replace('\n','')
        #response = response.encode("utf-8")
        tree = ElementTree.fromstring(response)
        #print response
        # Find the authentication status
        success = tree.find('.//' + SAML_1_0_PROTOCOL_NS + 'StatusCode')
        if success is not None and success.attrib['Value'] == 'saml1p:Success':
            # User is validated
            attrs = tree.findall('.//' + SAML_1_0_ASSERTION_NS + 'Attribute')
            for at in attrs:
                attributes[at.attrib['AttributeName']] = at.find(SAML_1_0_ASSERTION_NS + 'AttributeValue').text
                """
                if 'login' in list(at.attrib.values()):
                    user = at.find(SAML_1_0_ASSERTION_NS + 'AttributeValue').text
                    attributes['login'] = user
                    #user = attributes['idPessoa']
                    values = at.findall(SAML_1_0_ASSERTION_NS + 'AttributeValue')
                    if len(values) > 1:
                        values_array = []
                        for v in values:
                            values_array.append(v.text)
                            attributes[at.attrib['AttributeName']] = values_array
                    else:
                        attributes[at.attrib['AttributeName']] = values[0].text
                """
        return attributes['login'], attributes
    finally:
        page.close()



_PROTOCOLS = {
    '1': _verify_cas1,
    '2': _verify_cas2,
    '3': _verify_cas3,
    'CAS_2_SAML_1_0': _verify_cas2_saml,
}


if settings.CAS_VERSION not in _PROTOCOLS:
    raise ValueError('Unsupported CAS_VERSION %r' % settings.CAS_VERSION)

_verify = _PROTOCOLS[settings.CAS_VERSION]


class CASBackend(object):
    """CAS authentication backend"""

    def authenticate(self, ticket, service, request):
        """Verifies CAS ticket and gets or creates User object"""
        #username, attributes = _verify(ticket, service)
        username, attributes = _verify_cas3_saml(ticket, service)

        if attributes:
            request.session['attributes'] = attributes
        if not username:
            return None
        try:
            user = User.objects.get(username=username)
            created = False
        except User.DoesNotExist:
            # check if we want to create new users, if we don't fail auth
            create = getattr(settings, 'CAS_CREATE_USER', True)
            if not create:
                return None
            # user will have an "unusable" password
            user = User.objects.create_user(username, attributes["email"], '')
            user.first_name = attributes["personName"]
            user.last_name = attributes["idPessoa"]
            user.save()
            created = True

            # add user to default permission group


        # send the `cas_user_authenticated` signal
        cas_user_authenticated.send(
            sender=self,
            user=user,
            created=created,
            attributes=attributes,
            ticket=ticket,
            service=service,
        )
        return user

    def get_user(self, user_id):
        """Retrieve the user's entry in the User model if it exists"""

        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def give_permissions(self, group):
        # physical space permissions
        add_physical_space_reserve = Permission.objects.filter(codename='add_reservaespacofisico')
        for permission in add_physical_space_reserve:
            group.permissions.add(permission)
        change_physical_space_reserve = Permission.objects.filter(codename='change_reservaespacofisico')
        for permission in change_physical_space_reserve:
            group.permissions.add(permission)
        delete_physical_space_reserve = Permission.objects.filter(codename='delete_reservaespacofisico')
        for permission in delete_physical_space_reserve:
            group.permissions.add(permission)

        # equipment permissions
        add_equipment_reserve = Permission.objects.filter(codename='add_reservaequipamento', name='Can add reserva equipamento')
        for permission in add_equipment_reserve:
            group.permissions.add(permission)
        change_equipment_reserve = Permission.objects.filter(codename='change_reservaequipamento', name='Can change reserva equipamento')
        for permission in change_equipment_reserve:
            group.permissions.add(permission)
        delete_equipment_reserve = Permission.objects.filter(codename='delete_reservaequipamento', name='Can delete reserva equipamento')
        for permission in delete_equipment_reserve:
            group.permissions.add(permission)

        # services permissions
        add_service_reserve = Permission.objects.filter(codename='add_reservaservico')
        for permission in add_service_reserve:
            group.permissions.add(permission)
        change_service_reserve = Permission.objects.filter(codename='change_reservaservico')
        for permission in change_service_reserve:
            group.permissions.add(permission)
        delete_service_reserve = Permission.objects.filter(codename='delete_reservaservico')
        for permission in delete_service_reserve:
            group.permissions.add(permission)
        return group
