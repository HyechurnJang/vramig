# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2021. 1. 25..
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

import sys
import json
from .common import Object, register_object, isDebug, jps, jpp
from .iaas import *

@register_object
class Blueprint(Object):
    
    RELATIONS = [Project]
    LOAD_URL = '/blueprint/api/blueprints?$top=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, projects):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            detail = self.get('/blueprint/api/blueprints/' + id)
            name = d['name']
            project = projects.findID(d['projectId'])
            prj = project['name']
            dn = project['dn'] + '/' + name
            # Payload ##############################
            payload = {'name': name}
            if 'description' in detail: payload['description'] = detail['description']
            if 'content' in detail: payload['content'] = detail['content']
            if 'requestScopeOrg' in detail: payload['requestScopeOrg'] = detail['requestScopeOrg']
            # Payload ##############################
            map[id] = {
                'id': id, 'name': name, 'prj': prj, 'dn': dn,
                'payload': payload}
            ids.append(id)
            dns[dn] = id
            count += 1
        return map, ids, dns, count
    
    def sync(self, vra, src, projects):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            project = projects.findDN(s['prj'])
            if project:
                s['payload']['projectId'] = project['id']
                t = self.findDN(dn)
                if t == None: # Create
                    try: vra.post('/blueprint/api/blueprints', s['payload'])
                    except Exception as e:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not create blueprint [%s]' % dn)
                    else:
                        print(' +', end=''); sys.stdout.flush()
                        if isDebug(): print(' create blueprint [%s]' % dn)
                        completed += 1
                else: # Update
                    try: vra.put('/blueprint/api/blueprints/' + t['id'], s['payload'])
                    except:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not update blueprint [%s]' % dn)
                    else:
                        print(' *', end=''); sys.stdout.flush()
                        if isDebug(): print(' update blueprint [%s]' % dn)
                        completed += 1
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find project of blueprint [%s]' % dn)
        print('')
        return completed

@register_object
class Deployment(Object):
     
    RELATIONS = [Project, Blueprint]
    LOAD_URL = '/deployment/api/deployments?$top=10000'
     
    def __init__(self): Object.__init__(self)
     
    def parse(self, data, projects, blueprints):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            detail = self.get('/deployment/api/deployments/' + id + '/resources?$top=10000')
            project = projects.findID(d['projectId'])
            bp = blueprints.findID(d['blueprintId'])
            name = d['name']
            prj = project['name']
            dn = prj + '/' + name
            desc = d['description'] if 'description' in d else ''
            map[id] = {
                'id': id, 'name': name, 'prj': prj, 'dn': dn, 'description': desc,
                'content' : detail['content']
            }
            ids.append(id)
            dns[dn] = id
            count += 1
        return map, ids, dns, count