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

class VRA:
    
    def __init__(self, conf, role, debug=False):
        self._debug = debug
        self._version = conf[role]['version']
        self._hostname = conf[role]['hostname']
        self._base_url = 'https://' + self._hostname
        self._session = requests.Session()
        self._headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        res = self._session.post(self._base_url + '/csp/gateway/am/api/login?access_token', headers=self._headers, json={
            'username': conf[role]['username'],
            'password': conf[role]['password']
        }, verify=False)
        res.raise_for_status()
        auth = res.json()
        self._headers['Authorization'] = 'Bearer ' + auth['access_token']
        self._session.headers = self._headers
    
    def get(self, url):
        res = self._session.get(self._base_url + url)
        if(self._debug): print('DEBUG STATUS CODE : %d\n%s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()
    
    def getUerp(self, url):
        res = self._session.get(self._base_url + '/provisioning/uerp' + url)
        if(self._debug): print('DEBUG STATUS CODE : %d\n%s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()
    
    def post(self, url, data):
        res = self._session.post(self._base_url + url, json=data)
        if(self._debug): print('DEBUG STATUS CODE : %d\n%s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()
    
    def put(self, url, data):
        res = self._session.put(self._base_url + url, json=data)
        if(self._debug): print('DEBUG STATUS CODE : %d\n%s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()
    
    def patch(self, url, data):
        res = self._session.patch(self._base_url + url, json=data)
        if(self._debug): print('DEBUG STATUS CODE : %d\n%s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()
    
    def delete(self, url):
        res = self._session.delete(self._base_url + url)
        if(self._debug): print('DEBUG STATUS CODE : %d\n%s' % (res.status_code, res.text))
        res.raise_for_status()
        return res.json()

class VRAOBJ:
    
    def __init__(self, src_vra, tgt_vra):
        self.role = None
        self._vra = None
        self._src_vra = src_vra
        self._tgt_vra = tgt_vra
        self._model = self.__class__.__name__
    
    def setSrc(self):
        self.role = 'src'
        self._vra = self._src_vra
    
    def setTgt(self):
        self.role = 'tgt'
        self._vra = self._tgt_vra
    
    def get(self, url): return self._vra.get(url)
    def getUerp(self, url): return self._vra.getUerp(url)
    def post(self, url, data): return self._vra.post(url, data)
    def put(self, url, data): return self._vra.put(url, data)
    def patch(self, url, data): return self._vra.patch(url, data)
    def delete(self, url): return self._vra.delete(url)
    
    def printDataInfo(self, data):
        if 'numberOfElements' in data and 'totalElements' in data:
            print('│ %s : %4d / %-4d' % (self.role, data['numberOfElements'], data['totalElements']))
        elif 'totalCount' in data:
            print('│ %s : %4d / %-4d' % (self.role, data['documentCount'], data['totalCount']))
    
    @classmethod
    def write(cls, role, data):
        with open(cls.__name__ + '.%s.json' % role, 'w') as fd: fd.write(jps(data))
    
    @classmethod
    def read(cls, role):
        with open(cls.__name__ + '.%s.json' % role, 'r') as fd: return json.loads(fd.read())
    
    def dump(self):
        self.setSrc()
        if self._vra._version == '8.0': self.dump_80()
        elif self._vra._version == '8.1': self.dump_81()
        elif self._vra._version == '8.2': self.dump_82()
        self.setTgt()
        if self._vra._version == '8.0': self.dump_80()
        elif self._vra._version == '8.1': self.dump_81()
        elif self._vra._version == '8.2': self.dump_82()
        
    def dump_80(self): pass
    def dump_81(self): pass
    def dump_82(self): pass
    
    def sync(self):
        self.setTgt()
        if self._vra._version == '8.0': self.sync_80()
        elif self._vra._version == '8.1': self.sync_81()
        elif self._vra._version == '8.2': self.sync_82()
        
    def sync_80(self): pass
    def sync_81(self): pass
    def sync_82(self): pass
