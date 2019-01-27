#!/usr/bin/python3
import requests
import configparser
from base64 import b64encode
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree


class vcloud:
    def __init__(self,config):
        self.config = config
        self.user = config['Main']['User']
        self.passwd = config['Main']['Password']
        self.host = config['Main']['Host']
        self.org = config['Main']['Org']

        self.api='https://%s/api' % self.host
        self.session_url='%s/sessions' % self.api
        self.query_url='%s/query' % self.api

        self.headers={'Accept': 'application/*+xml;version=30.0'}

        self._set_auth_token()

    def _set_auth_token(self):
        auth_str = '%s@%s:%s' % (self.user, self.org, self.passwd)
        auth=b64encode(auth_str.encode()).decode('utf-8')
        self.headers['Authorization'] = 'Basic %s' % auth
        resp = requests.post(url=self.session_url, headers=self.headers)
        del self.headers['Authorization']
        self.headers['x-vcloud-authorization'] = resp.headers['x-vcloud-authorization']

    def _getvapp(self, vapp_name):
        resp = requests.get(url=self.api+'/vApps/query?filter=name=='+vapp_name,headers=self.headers)
        xml_content = resp.text 
        root = ElementTree.fromstring(xml_content)
        for child in root:
            if 'VAppRecord' in child.tag:
                return child.attrib['href'].replace('https://vcloud.ialab.dsu.edu/api/vApp/', '')

    def createAccessSetting(self,user_href, name, accessLevel):
        xml_content = '<AccessSetting></AccessSetting>'
        AccessSetting = ElementTree.fromstring(xml_content)
        AccessSetting.tag = '{http://www.vmware.com/vcloud/v1.5}AccessSetting'
        xml_content = '<Subject href="'+user_href+'" name="'+name+'" type="application/vnd.vmware.admin.user+xml" />'
        Subject = ElementTree.fromstring(xml_content)
        Subject.tag = '{http://www.vmware.com/vcloud/v1.5}Subject'
        xml_content = '<AccessLevel>'+accessLevel+'</AccessLevel>'
        AccessLevel = ElementTree.fromstring(xml_content)
        AccessLevel.tag = '{http://www.vmware.com/vcloud/v1.5}AccessLevel'
        AccessSetting.append(Subject)
        AccessSetting.append(AccessLevel)
        return AccessSetting

    def addUserToVapp(self, vapp, member, href):
        resp = requests.get(url=self.api+'/vApp/'+vapp+'/controlAccess',headers=self.headers)
        xml_content = resp.text 
        ElementTree.register_namespace('', 'http://www.vmware.com/vcloud/v1.5' )
        root = ElementTree.fromstring(xml_content)
        newAcl = self.createAccessSetting(href, member, 'ReadOnly')
        try:
            root[1].append(newAcl)
        except IndexError:
            xml_content = '<AccessSettings></AccessSettings>'
            AccessSetting = ElementTree.fromstring(xml_content)
            AccessSetting.tag = '{http://www.vmware.com/vcloud/v1.5}AccessSettings'
            AccessSetting.append(newAcl)
            root.append(AccessSetting)
        data = ElementTree.tostring(root, encoding='utf8', method='xml' ).decode('utf-8')
        resp = requests.post(url=self.api+'/vApp/'+vapp+'/action/controlAccess',headers=self.headers, data=data)
