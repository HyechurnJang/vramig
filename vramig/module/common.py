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

class VRA:
    
    def __init__(self, hostname, username, password, debug=False):
        self._hostname = hostname
        self._debug = debug
        self._base_url = 'https://' + hostname
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
        res.raise_for_status()
        return res.json()
    
    def getUerp(self, url):
        res = self._session.get(self._base_url + '/provisioning/uerp' + url)
        res.raise_for_status()
        return res.json()
    
    def post(self, url, data):
        res = self._session.post(self._base_url + url, json=data)
        res.raise_for_status()
        return res.json()
    
    def put(self, url, data):
        res = self._session.put(self._base_url + url, json=data)
        res.raise_for_status()
        return res.json()
    
    def patch(self, url, data):
        res = self._session.patch(self._base_url + url, json=data)
        res.raise_for_status()
        return res.json()
    
    def delete(self, url):
        res = self._session.delete(self._base_url + url)
        res.raise_for_status()
        return res.json()

class VRAOBJ:
    
    def __init__(self, vra):
        self._vra = vra
        self._file_name = self.__class__.__name__ + '.json'
    
    def get(self, url): return self._vra.get(url)
    def getUerp(self, url): return self._vra.getUerp(url)
    def post(self, url, data): return self._vra.post(url, data)
    def put(self, url, data): return self._vra.put(url, data)
    def patch(self, url, data): return self._vra.patch(url, data)
    def delete(self, url): return self._vra.post(url)
    
    def data2file(self, data):
        data = jps(data)
        with open(self._file_name, 'w') as fd: fd.write(data)
        if (self._vra._debug): print(data)
    
    def file2data(self, model=None):
        if model != None:
            with open(model + '.json', 'r') as fd: return json.loads(fd.read())
        else:
            with open(self._file_name, 'r') as fd: return json.loads(fd.read())
    
    def dump(self): pass
    def sync(self): pass
