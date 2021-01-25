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
import time
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


def ip2num(ip):
    num = 0
    for octet in ip.split('.'):
        num <<= 8
        num += int(octet)
    return num

def num2ip(num):
    return str(num >> 24) + '.' + str(num >> 16 & 255) + '.' + str(num >> 8 & 255) + '.' + str(num & 255)

def clear_onboard(vra):
    if isDebug(): print(' - clear onboard plan temporary data', end='')
    data = vra.get('/relocation/api/wo/execute-plan?$limit=10000')['documentLinks']
    for id in data: vra.delete(id)
    data = vra.get('/relocation/onboarding/blueprint?$limit=10000')['documentLinks']
    for id in data: vra.delete(id)
    data = vra.get('/relocation/onboarding/resource?$limit=10000')['documentLinks']
    for id in data: vra.delete(id)
    data = vra.get('/relocation/onboarding/deployment?$limit=10000')['documentLinks']
    for id in data: vra.delete(id)
    data = vra.get('/relocation/onboarding/plan?$limit=10000')['documentLinks']
    for id in data: vra.delete(id)
    if isDebug(): print(' [ OK ]')

@register_object
class Deployment(Object):
     
    RELATIONS = [CloudAccount, Project, Blueprint]
    LOAD_URL = '/deployment/api/deployments?expand=resources&$top=10000'
     
    def __init__(self): Object.__init__(self)
     
    def parse(self, data, accounts, projects, blueprints):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            project = projects.findID(d['projectId'])
            bp = blueprints.findID(d['blueprintId'])
            name = d['name']
            prj = project['dn']
            bp = bp['dn']
            dn = prj + '/' + name
            # Payload ##############################
            resources = []
            for resource in d['resources']:
                if 'Machine' in resource['type']:
                    resources.append(resource['properties']['resourceName'])
            # Payload ##############################
             
            map[id] = {
                'id': id, 'name': name, 'prj': prj, 'bp': bp, 'dn': dn,
                'description': d['description'] if 'description' in d else '',
                'resources' : resources
            }
            ids.append(id)
            dns[dn] = id
            count += 1
        return map, ids, dns, count
    

    def sync(self, vra, src, accounts, projects, blueprints):
        completed = 0
        endpointIds = [accounts['ids'][0]]
        for s in src.getSortedMaps():
            dn = s['dn']
            name = s['name']
            project = projects.findDN(s['prj'])
            blueprint = blueprints.findDN(s['bp'])
            if project and blueprint:
                if dn not in self['dns']:
                    projectId = project['id']
                    blueprintId = blueprint['id']
                    computeResources = []
                    for computeName in s['resources']:
                        computes = vra.get("/provisioning/uerp/resources/compute?expand&$filter=((type eq 'VM_GUEST') and (name eq '%s') and (lifecycleState eq 'READY'))" % computeName)
                        computeLink = computes['documentLinks'][0]
                        compute = computes['documents'][computeLink]
                        computeResources.append((computeLink, computeName))
                        for netifLink in compute['networkInterfaceLinks']:
                            netif = vra.get("/provisioning/uerp/resources/network-interfaces?expand&$filter=(documentSelfLink eq '%s')" % netifLink)
                            netif = netif['documents'][netif['documentLinks'][0]]
                            netifName = netif['name']
                            if 'address' not in netif:
                                print(' !', end=''); sys.stdout.flush()
                                if isDebug(): print(' could not find ip address in compute[%s] netif[%s]' % (computeName, netif['id']))
                                continue
                            address = netif['address']
                            num_address = ip2num(address)
                            subnetLink = netif['subnetLink']
                            subnets = vra.get("/provisioning/uerp/resources/sub-networks?expand&$filter=(documentSelfLink eq '%s')" % subnetLink)
                            subnet = subnets['documents'][subnets['documentLinks'][0]]
                            range = None
                            rangeLink = None
                            if 'subnetCIDR' not in subnet or subnet['subnetCIDR'] == "":
                                subnets = vra.get("/provisioning/uerp/resources/sub-networks?expand&$filter=(name eq '%s')" % subnet['name'])
                                for subnetLink in subnets['documentLinks']:
                                    subnet = subnets['documents'][subnetLink]
                                    if 'subnetCIDR' in subnet and subnet['subnetCIDR'] != '':
                                        ranges = vra.get("/provisioning/uerp/resources/subnet-ranges?expand&$filter=(subnetLink eq '%s')" % subnetLink)
                                        for rangeLink in ranges['documentLinks']:
                                            range = ranges['documents'][rangeLink]
                                            ip_stt = ip2num(range['startIPAddress'])
                                            ip_end = ip2num(range['endIPAddress'])
                                            if num_address >= ip_stt and num_address <= ip_end: break
                                        else:
                                            print(' !', end=''); sys.stdout.flush()
                                            if isDebug(): print(' could not find available ip range for compute[%s] with ip[%s]' % (computeName, address))
                                            raise Exception('could not find available ip range for compute[%s] with ip[%s]' % (computeName, address))
                                        break
                                else:
                                    print(' !', end=''); sys.stdout.flush()
                                    if isDebug(): print(' could not find available subnet for compute[%s] with ip[%s]' % (computeName, address))
                                    raise Exception('could not find available subnet for compute[%s] with ip[%s]' % (computeName, address))
                            else:
                                ranges = vra.get("/provisioning/uerp/resources/subnet-ranges?expand&$filter=(subnetLink eq '%s')" % subnetLink)
                                for rangeLink in ranges['documentLinks']:
                                    range = ranges['documents'][rangeLink]
                                    ip_stt = ip2num(range['startIPAddress'])
                                    ip_end = ip2num(range['endIPAddress'])
                                    if num_address >= ip_stt and num_address <= ip_end: break
                                else:
                                    print(' !', end=''); sys.stdout.flush()
                                    if isDebug(): print(' could not find available ip range for compute[%s] with ip[%s]' % (computeName, address))
                                    raise Exception('could not find available ip range for compute[%s] with ip[%s]' % (computeName, address))
                            
                            is_ip_updated = False
                            ip = vra.get("/provisioning/uerp/resources/ip-addresses?expand&$filter=((subnetRangeLink eq '%s') and (ipAddress eq '%s'))" % (rangeLink, address))
                            if ip['documentLinks']:
                                ip = ip['documents'][ip['documentLinks'][0]]
                                ipLink = ip['documentSelfLink']
                                if ip['ipAddressStatus'] != 'ALLOCATED':
                                    ip['ipAddressStatus'] = 'ALLOCATED'
                                    ip['connectedResourceLink'] = netifLink
                                    ip = vra.patch('/provisioning/uerp' + ipLink, ip)
                                    is_ip_updated = True
                                else:
                                    try:
                                        mac = vra.get("/provisioning/uerp/resources/network-interfaces?expand&$filter=(documentSelfLink eq '%s')" % ip['connectedResourceLink'])
                                        mac = mac['documents'][mac['documentLinks'][0]]['id']
                                    except: mac = 'unknown'
                                    print(' ! already ip allocated for compute[%s] with ip[%s] on [%s]' % (computeName, address, mac))
                                    key = input(' ! ignore ip allocation? [y|N]: ').lower()
                                    if key == 'y': continue
                                    else: raise Exception(' ! stopped')
                            else:
                                ip = vra.post('/provisioning/uerp/resources/ip-addresses', {
                                    'customProperties': {},
                                    'ipAddress': address,
                                    'ipAddressStatus': 'ALLOCATED',
                                    'subnetRangeLink': rangeLink,
                                    'connectedResourceLink': netifLink
                                })
                                ipLink = ip['documentSelfLink']
                                is_ip_updated = True
                            
                            is_netif_updated = False
                            if is_ip_updated:
                                if 'Network adapter' in netifName:
                                    index = int(netifName.split(' ')[2]) - 1;
                                    netif['name'] = subnet['name']
                                    netif['deviceIndex'] = index
                                    is_netif_updated = True
                                if 'addressLinks' not in netif or not netif['addressLinks']:
                                    netif['addressLinks'] = [ipLink]
                                    netif['address'] = address
                                    is_netif_updated = True
                                if netif['subnetLink'] != subnetLink:
                                    netif['subnetLink'] = subnetLink
                                    is_netif_updated = True
                                if is_netif_updated:
                                    vra.put('/provisioning/uerp' + netifLink, netif)
                    
                    try:
                        plan_payload = {
                            'name': name,
                            'projectId': projectId,
                            'endpointIds': endpointIds,
                            'description': s['description'],
                            'deploymentTagType': 'TAG'
                        }
                        plan = vra.post('/relocation/onboarding/plan', plan_payload)
                        planLink = plan['documentSelfLink']
                         
                        dep_payload = {
                            'name': name,
                            'planLink': planLink,
                            'description': s['description']
                        }
                        dep = vra.post('/relocation/onboarding/deployment', dep_payload)
                        depLink = dep['documentSelfLink']
                        
                        for computeResource in computeResources:
                            rsc_payload = {
                                'planLink': planLink,
                                'deploymentLink': depLink,
                                'resourceLink': computeResource[0],
                                'resourceName': computeResource[1],
                                'ruleLinks': []
                            }
                            rsc = vra.post('/relocation/onboarding/resource', rsc_payload)
                        
                        bp_payload = {
                            'name': name,
                            'planLink': planLink,
                            'deploymentLink': depLink,
                            'templateLink': '/blueprint/api/blueprints/' + blueprintId,
                            'autoGenerate': False
                        }
                        bp = vra.post('/relocation/onboarding/blueprint', bp_payload)
                        
                        ep = vra.post('/relocation/api/wo/execute-plan', {
                            'planLink': planLink
                        })
                        epLink = ep['documentSelfLink']
                    except Exception as e:
                        print(' ! onboarding is failed [%s] : %s' % (dn, str(e)))
                        clear_onboard(vra)
                        key = input(' ! ignore failure? [y|N]: ').lower()
                        if key == 'y': continue
                        else: raise Exception(' ! stopped')
                    else:
                        wait_count = 0
                        while True:
                            if (wait_count == 10):
                                print(' !', end=''); sys.stdout.flush()
                                if isDebug(): print(' could not finish onboard plan[%s]' % dn)
                                clear_onboard(vra)
                                raise Exception('could not finish onboard plan[%s]' % dn)
                            ep = vra.get(epLink)
                            stage = ep['taskInfo']['stage']
                            if stage == 'FINISHED':
                                print(' +', end=''); sys.stdout.flush()
                                if isDebug(): print(' success onboard plan[%s]' % dn)
                                clear_onboard(vra)
                                completed += 1
                                break
                            else:
                                print(' ?', end=''); sys.stdout.flush()
                            time.sleep(1)
                            wait_count += 1
                else:
                    print(' =', end=''); sys.stdout.flush()
                    if isDebug(): print(' deployment is already exist [%s]' % dn)
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find project or blueprint [%s]' % dn)
        print('')
        return completed