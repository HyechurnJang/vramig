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
from .common import VRA, VRAOBJ, jps, jpp, register_object

@register_object
class CloudAccount(VRAOBJ):
    
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        data = self.get('/iaas/api/cloud-accounts')['content']
        self.data2file(data)

@register_object
class CloudZone(VRAOBJ):
     
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
     
    def dump(self):
        data = self.get('/iaas/api/zones')['content']
        self.data2file(data)
    
    def sync(self):
        data = self.file2data()
        zones = self.get('/iaas/api/zones')['content']
        regions = self.get('/iaas/api/regions')['content']
        for content in data:
            is_zone = False
            for zone in zones:
                if zone['name'] == content['name']: break
            else:
                print('cloud zone {}'.format(content['name']))
                for region in regions:
                    if content['externalRegionId'] == region['externalRegionId']:
                        regionId = region['id']
                        break
                else: raise Exception('could not find region')
                d = {'name': content['name'], 'regionId': regionId}
                if 'customProperties' in content: d['customProperties'] = content['customProperties']
                if 'folder' in content: d['folder'] = content['folder']
                if 'tagsToMatch' in content: d['tagsToMatch'] = content['tagsToMatch']
                if 'description' in content: d['description'] = content['description']
                if 'placementPolicy' in content: d['placementPolicy'] = content['placementPolicy']
                if 'tags' in content: d['tags'] = content['tags']
                self.post('/iaas/api/zones', d)

@register_object
class FabricCompute(VRAOBJ):
    
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        data = self.get('/iaas/api/fabric-computes')['content']
        self.data2file(data)
    
    def sync(self):
        data = self.file2data()
        computes = self.get('/iaas/api/fabric-computes')['content']
        for content in data:
            if 'tags' in content and content['tags']:
                print('fabric compute {}'.format(content['name']))
                externalRegionId = content['externalRegionId']
                externalId = content['externalId']
                for obj in computes:
                    if obj['externalRegionId'] == externalRegionId and obj['externalId'] == externalId:
                        self.patch('/iaas/api/fabric-computes/' + obj['id'], {
                            'tags': content['tags']
                        })
                        break
                else: raise Exception('could not find fabric compute')

@register_object
class FabricNetwork(VRAOBJ):
    
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        data = self.get('/iaas/api/fabric-networks')['content']
        self.data2file(data)
    
    def sync(self):
        data = self.file2data()
        networks = self.get('/iaas/api/fabric-networks')['content']
        for content in data:
            if 'tags' in content and content['tags']:
                print('fabric network {}'.format(content['name']))
                if 'externalRegionId' in content: # Compute Network
                    externalRegionId = content['externalRegionId']
                    externalId = content['externalId']
                    for obj in networks:
                        if obj['externalId'] == externalId:
                            if 'externalRegionId' in obj and obj['externalRegionId'] == externalRegionId:
                                self.patch('/iaas/api/fabric-networks/' + obj['id'], {
                                    'tags': content['tags']
                                })
                                break
                    else: raise Exception('could not find fabric network')
                else: # NSX Network
                    if 'path' in content['customProperties']:
                        nsx_path = content['customProperties']['path']
                        externalId = content['externalId']
                        for obj in networks:
                            if obj['externalId'] == externalId:
                                if 'path' in obj['customProperties'] and obj['customProperties']['path'] == nsx_path:
                                    self.patch('/iaas/api/fabric-networks/' + obj['id'], {
                                        'tags': content['tags']
                                    })
                                    break
                        else: raise Exception('could not find fabric network')

@register_object
class FabricNetworkvSphere(VRAOBJ):

    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        data = self.get('/iaas/api/fabric-networks-vsphere')['content']
        self.data2file(data)
    
    def sync(self):
        data = self.file2data()
        networks = self.get('/iaas/api/fabric-networks-vsphere')['content']
        for content in data:
            if 'cidr' in content:
                print('fabric network vsphere {}'.format(content['name']))
                if 'externalRegionId' in content: # Compute Network
                    externalRegionId = content['externalRegionId']
                    externalId = content['externalId']
                    for obj in networks:
                        if obj['externalId'] == externalId:
                            if 'externalRegionId' in obj and obj['externalRegionId'] == externalRegionId:
                                d = {'cidr': content['cidr']}
                                if 'domain' in content: d['domain'] = content['domain']
                                if 'defaultGateway' in content: d['defaultGateway'] = content['defaultGateway']
                                if 'dnsServerAddresses' in content: d['dnsServerAddresses'] = content['dnsServerAddresses']
                                if 'dnsSearchDomains' in content: d['dnsSearchDomains'] = content['dnsSearchDomains']
                                if 'isDefault' in content: d['isDefault'] = content['isDefault']
                                self.patch('/iaas/api/fabric-networks-vsphere/' + obj['id'], d)
                                break
                    else: raise Exception('could not find fabric network vsphere')
                else: # NSX Network
                    if '__path' in content['customProperties']:
                        nsx_path = content['customProperties']['__path']
                        externalId = content['externalId']
                        for obj in networks:
                            if obj['externalId'] == externalId:
                                if '__path' in obj['customProperties'] and obj['customProperties']['__path'] == nsx_path:
                                    d = {'cidr': content['cidr']}
                                    if 'domain' in content: d['domain'] = content['domain']
                                    if 'defaultGateway' in content: d['defaultGateway'] = content['defaultGateway']
                                    if 'dnsServerAddresses' in content: d['dnsServerAddresses'] = content['dnsServerAddresses']
                                    if 'dnsSearchDomains' in content: d['dnsSearchDomains'] = content['dnsSearchDomains']
                                    if 'isDefault' in content: d['isDefault'] = content['isDefault']
                                    self.patch('/iaas/api/fabric-networks-vsphere/' + obj['id'], d)
                                    break
                        else: raise Exception('could not find fabric network vcsphere')

@register_object
class IPRange(VRAOBJ):
    
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        data = self.get('/iaas/api/network-ip-ranges')['content']
        self.data2file(data)
    
    def sync(self):
        data = self.file2data()
        tgt_networks = self.get('/iaas/api/fabric-networks')['content']
        src_networks = self.file2data('FabricNetwork')
        for content in data:
            if 'fabric-network' in content['_links'] and 'href' in content['_links']['fabric-network']:
                fabric_network_id = content['_links']['fabric-network']['href'].split('fabric-networks/')[1]
                externalRegionId = None
                nsx_path = None
                externalId = None
                for network in src_networks:
                    if network['id'] == fabric_network_id:
                        if 'externalRegionId' in network:
                            externalRegionId = network['externalRegionId']
                            externalId = network['externalId']
                            break
                        elif 'path' in network['customProperties']:
                            nsx_path = network['customProperties']['path']
                            externalId = network['externalId']
                            break
                        break
                else: raise Exception('could not find fabric network')
                for network in tgt_networks:
                    if externalId == network['externalId']:
                        if externalRegionId and 'externalRegionId' in network and externalRegionId == network['externalRegionId']:
                            fabric_network_id = network['id']
                            break
                        elif nsx_path and 'path' in network['customProperties'] and nsx_path == network['customProperties']['path']:
                            fabric_network_id = network['id']
                            break
                else: raise Exception('could not find fabric network')
                try:
                    self.post('/iaas/api/network-ip-ranges', {
                        'fabricNetworkId': fabric_network_id,
                        'name': content['name'],
                        'ipVersion': content['ipVersion'],
                        'startIPAddress': content['startIPAddress'],
                        'endIPAddress': content['endIPAddress']
                    })
                except: print('already set ip range {}'.format(content['name']))
        
    

# @register_object
# class NetworkProfile(VRAOBJ):
#     
#     def __init__(self, vra):
#         VRAOBJ.__init__(self, vra)
#     
#     def dump(self):
#         data = self.get('/iaas/api/network-profiles')['content']
#         self.data2file(data)
#     
#     def sync(self):
#         data = self.file2data()
#         netprops = self.get('/iaas/api/network-profiles')['content']
#         regions = self.get('/iaas/api/regions')['content']
#         for content in data:
#             externalRegionId = content['externalRegionId']
#             name = content['name']
#             for obj in netprops:
#                 if externalRegionId == obj['externalRegionId'] and name == obj['name']: break
#             else:
#                 for region in regions:
#                     if content['externalRegionId'] == region['externalRegionId']:
#                         regionId = region['id']
#                         break
#                 else: raise Exception('could not find region')
#                 d = {'name' : content['name'], 'regionId': regionId}
#                 if 'description' in content: d['description'] = content['description']
#                 if 'isolationType' in content: d['isolationType'] = content['isolationType']
#                 if 'isolatedNetworkCIDRPrefix' in content: d['isolatedNetworkCIDRPrefix'] = content['isolatedNetworkCIDRPrefix']
#                 if 'isolationNetworkDomainCIDR' in content: d['isolationNetworkDomainCIDR'] = content['isolationNetworkDomainCIDR']
#                 if 'datacenterId' in content['customProperties']: d['customProperties'] = {'datacenterId' :content['isolationType']}
#                 if 'isolationType' in content: d['isolationType'] = content['isolationType']
#                 if 'isolationType' in content: d['isolationType'] = content['isolationType']
#                 if 'isolationType' in content: d['isolationType'] = content['isolationType']
#                 if 'isolationType' in content: d['isolationType'] = content['isolationType']
#                 
#                 d = {
#                     "description": "string",
#                     "isolationNetworkDomainCIDR": "10.10.10.0/24",
#                     "isolationNetworkDomainId": "1234",
#                     "tags": "[ { \"key\" : \"dev\", \"value\": \"hard\" } ]",
#                     "externalIpBlockIds": "[\"3e2bb9bc-6a6a-11ea-bc55-0242ac130003\"]",
#                     "fabricNetworkIds": "[ \"6543\" ]",
#                     "customProperties": "{ \"resourcePoolId\" : \"resource-pool-1\", \"datastoreId\" : \"StoragePod:group-p87839\", \"computeCluster\" : \"/resources/compute/1234\", \"distributedLogicalRouterStateLink\" : \"/resources/routers/1234\", \"onDemandNetworkIPAssignmentType\" : \"dynamic\"}",
#                     "regionId": "9e49",
#                     "securityGroupIds": "[ \"6545\" ]",
#                     "name": "string",
#                     "isolationExternalFabricNetworkId": "1234",
#                     "isolationType": "SUBNET",
#                     "isolatedNetworkCIDRPrefix": 24,
#                     "loadBalancerIds": "[ \"6545\" ]"
#                 }
                
            
                        
                        

































