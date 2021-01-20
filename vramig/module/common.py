# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2021. 1. 8..
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def jps(obj): return json.dumps(obj, indent=2)
def jpp(obj): print(jps(obj))

REGISTERED_OBJECTS = {}
def register_object(cls):
    REGISTERED_OBJECTS[cls.__name__] = cls
    return cls

DEBUG = {'debug': False}
def setDebugMode(): DEBUG['debug'] = True
def isDebug(): return DEBUG['debug']

class VRASession:
    
    def __init__(self, hostname, username, password):
        self._hostname = hostname
        self._base_url = 'https://' + self._hostname
        self._session = requests.Session()
        self._headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        res = self._session.post(self._base_url + '/csp/gateway/am/api/login?access_token', headers=self._headers, json={
            'username': username,
            'password': password
        }, verify=False)
        res.raise_for_status()
        auth = res.json()
        self._headers['Authorization'] = 'Bearer ' + auth['access_token']
        self._session.headers = self._headers
    
    def get(self, url):
        res = self._session.get(self._base_url + url)
        if isDebug() and res.status_code >= 400: print('  ! rest status code [%d]\n  ? %s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()
    
    def post(self, url, data):
        res = self._session.post(self._base_url + url, json=data)
        if isDebug() and res.status_code >= 400: print('  ! rest status code [%d]\n  ? %s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()
    
    def put(self, url, data):
        res = self._session.put(self._base_url + url, json=data)
        if isDebug() and res.status_code >= 400: print('  ! rest status code [%d]\n  ? %s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()
    
    def patch(self, url, data):
        res = self._session.patch(self._base_url + url, json=data)
        if isDebug() and res.status_code >= 400: print('  ! rest status code [%d]\n  ? %s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()
    
    def delete(self, url):
        res = self._session.delete(self._base_url + url)
        if isDebug() and res.status_code >= 400: print('  ! rest status code [%d]\n  ? %s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()

class VRA(VRASession):
    
    def __init__(self, conf, role):
        VRASession.__init__(self, conf[role]['hostname'], conf[role]['username'], conf[role]['password'])
        self.role = role
        self.ver = conf[role]['version']


class Object(dict):
    
    RELATIONS = []
    LOAD_URL = ''
    
    def __init__(self):
        dict.__init__(self)
    
    def get(self, url): return self.vra.get(url)
    def post(self, url, data): return self.vra.post(url, data)
    def put(self, url, data): return self.vra.put(url, data)
    def patch(self, url, data): return self.vra.patch(url, data)
    def delete(self, url): return self.vra.delete(url)
    
    def dump(self, role):
        with open(self.__class__.__name__ + '.%s.json' % role, 'w') as fd: fd.write(jps(self))
    
    @classmethod
    def loadFile(cls, role, object=None):
        if not object: object = cls
        with open(object.__name__ + '.%s.json' % role, 'r') as fd: data = fd.read()
        data = json.loads(data)
        o = object()
        o.role = role
        o['map'] = data['map']
        o['ids'] = data['ids']
        o['dns'] = data['dns']
        o['count'] = data['count']
        return o
    
    def loadData(self, vra):
        self.vra = vra
        self.role = vra.role
        self.ver = vra.ver
        data = vra.get(self.__class__.LOAD_URL)
        if 'numberOfElements' in data and 'totalElements' in data:
            print('  %s : %4d / %-4d' % (vra.role, data['numberOfElements'], data['totalElements']), end='')
        elif 'totalCount' in data:
            print('  %s : %4d / %-4d' % (vra.role, data['documentCount'], data['totalCount']), end='')
        elif isinstance(data, list):
            print('  %s : %4d / %-4d' % (vra.role, len(data), len(data)), end='')
        rels = [ object.loadFile(vra.role) for object in self.__class__.RELATIONS ]
        self['map'], self['ids'], self['dns'], self['count'] = self.parse(data, *rels)
        print(' => %d' % self['count'])
        self.dump(vra.role)
        return self
        
    def syncData(self, vra, src):
        rels = [ object.loadFile(vra.role) for object in self.__class__.RELATIONS ]
        completed = self.sync(vra, src, *rels)
        if completed:
            print('  %d objects synced' % completed)
            self.loadData(vra)
        return self
    
    def findID(self, id):
        try: return self['map'][id]
        except:
            if isDebug(): print(' ! could not find data with id(%s)' % id)
            return None
    
    def findDN(self, dn):
        try:
            id = self['dns'][dn]
            return self['map'][id]
        except:
            if isDebug(): print(' ! could not find data with dn(%s)' % dn)
        return None
    
    def getMaps(self):
        return self['map'].values()
    
    def getIDMaps(self):
        return self['map'].items()
    
    def getSortedMaps(self):
        return sorted(self['map'].values(), key=lambda x: x['dn'])
    
    def getSortedIDMaps(self):
        return sorted(self['map'].items(), key=lambda x: x[1]['dn'])
    
    # Interfaces
    def parse(self, data, *rels): pass
    def sync(self, vra, src, *rels): return 0
        
