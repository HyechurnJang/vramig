# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2021. 1. 14..
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

import sys
import json
from module.common import VRASession, jpp, setDebugMode, isDebug
setDebugMode()

def ip2num(ip):
    num = 0
    for octet in ip.split('.'):
        num <<= 8
        num += int(octet)
    return num

def num2ip(num):
    return str(num >> 24) + '.' + str(num >> 16 & 255) + '.' + str(num >> 8 & 255) + '.' + str(num & 255)

vra = VRASession('vra.vmkloud.com', 'jangh', 'David*#8090')

ns = 'test'
vms = ['test2', 'test3']
bp = '[TEST] Custom.Script'
name = 'ob-%s' % ns
description = 'onboard test %s' % ns

# Cloud Account
endpointIds = ['8967fe8c-e6e6-46b9-a3b5-d4ab9d4a053e']
# /iaas/api/cloud-account
# d['id']

# Project
projectId = '85a2bc48-f42f-4e38-b160-994f8a5f2127'

# Get Resources

# Get Blueprint
blueprints = vra.get("/blueprint/api/blueprints?&search=Dynamic")
blueprint = blueprints['content'][0]
blueprintLink = blueprint['selfLink']

#############################################################
# Create Plan
plan_payload = {
    'name': name,
    'projectId': projectId,
    'endpointIds': endpointIds,
    'description': description,
    'deploymentTagType': 'TAG'
}
plan = vra.post('/relocation/onboarding/plan', plan_payload)
planLink = plan['documentSelfLink']
 
# Create Deployment
dep_payload = {
    'name': name,
    'planLink': planLink,
    'description': description
}
dep = vra.post('/relocation/onboarding/deployment', dep_payload)
depLink = dep['documentSelfLink']
 
# Create Resource
resources = []
for vm in vms:
    computes = vra.get("/provisioning/uerp/resources/compute?expand&$filter=((type eq 'VM_GUEST') and (name eq '%s') and (lifecycleState eq 'READY'))" % vm)
    computeLink = computes['documentLinks'][0]
    compute = computes['documents'][computeLink]
    computeName = compute['name']
    
    print(computeName)
    
    for netifLink in compute['networkInterfaceLinks']:
        netif = vra.get("/provisioning/uerp/resources/network-interfaces?expand&$filter=(documentSelfLink eq '%s')" % netifLink)
        netif = netif['documents'][netif['documentLinks'][0]]
        netifName = netif['name']
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
                        if isDebug(): print(' could not find available ip range')
                        raise Exception('could not find available ip range')
                    break
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find available subnet')
                raise Exception('could not find available subnet')
        else:
            ranges = vra.get("/provisioning/uerp/resources/subnet-ranges?expand&$filter=(subnetLink eq '%s')" % subnetLink)
            for rangeLink in ranges['documentLinks']:
                range = ranges['documents'][rangeLink]
                ip_stt = ip2num(range['startIPAddress'])
                ip_end = ip2num(range['endIPAddress'])
                if num_address >= ip_stt and num_address <= ip_end: break
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find available ip range')
                raise Exception('could not find available ip range')
        
        print(netifName)
        print(subnet['name'])
        print(range['name'])
        
        ip = vra.get("/provisioning/uerp/resources/ip-addresses?expand&$filter=((subnetRangeLink eq '%s') and (ipAddress eq '%s'))" % (rangeLink, address))
        if ip['documentLinks']:
            ip = ip['documents'][ip['documentLinks'][0]]
            ipLink = ip['documentSelfLink']
            if ip['ipAddressStatus'] != 'ALLOCATED':
                ip['ipAddressStatus'] = 'ALLOCATED'
                ip['connectedResourceLink'] = netifLink
                ip = vra.patch('/provisioning/uerp' + ipLink, ip)
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' already ip allocated')
        else:
            ip = vra.post('/provisioning/uerp/resources/ip-addresses', {
                'customProperties': {},
                'ipAddress': address,
                'ipAddressStatus': 'ALLOCATED',
                'subnetRangeLink': rangeLink,
                'connectedResourceLink': netifLink
            })
            ipLink = ip['documentSelfLink']
            break
                    
        is_netif_updated = False
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
            
        print('VM[%s] NETIF[%s][%d] : %s' % (name, netif['name'], netif['deviceIndex'], address))
    
    rsc_payload = {
        'planLink': planLink,
        'deploymentLink': depLink,
        'resourceLink': computeLink,
        'resourceName': computeName,
        'ruleLinks': []
    }
    rsc = vra.post('/relocation/onboarding/resource', rsc_payload)
 
# Create Blueprint
bp_payload = {
    'name': name,
    'planLink': planLink,
    'deploymentLink': depLink,
    'templateLink': blueprintLink,
    'autoGenerate': False
}
bp = vra.post('/relocation/onboarding/blueprint', bp_payload)























