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
        self.data2file(self.get('/iaas/api/cloud-accounts?$limit=10000'))

@register_object
class CloudRegion(VRAOBJ):
    
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        self.data2file(self.get('/iaas/api/regions?$limit=10000'))

@register_object
class CloudZone(VRAOBJ):
     
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
     
    def dump(self):
        self.data2file(self.get('/iaas/api/zones?$limit=10000'))
    
    def sync(self):
        srcs = self.file2data()
        tgts = self.get('/iaas/api/zones?$limit=10000')['content']
        src_ca = self.getCAFromFile()
        tgt_ca = self.getCAFromRest()
        regions = self.get('/iaas/api/regions?$limit=10000')['content']
        for src in srcs:
            for tgt in tgts:
                if src['name'] == tgt['name']: break
            else:
                regionId = None
                for region in regions:
                    if src_ca[self.getCAID(src)] == tgt_ca[self.getCAID(region)] and src['externalRegionId'] == region['externalRegionId']:
                        regionId = region['id']
                        break
                else:
                    print('ERROR: could not find region %s' % src['name'])
                    continue
                data = {'name': src['name'], 'regionId': regionId}
                if 'customProperties' in src: data['customProperties'] = src['customProperties']
                if 'folder' in src: data['folder'] = src['folder']
                if 'tagsToMatch' in src: data['tagsToMatch'] = src['tagsToMatch']
                if 'description' in src: data['description'] = src['description']
                if 'placementPolicy' in src: data['placementPolicy'] = src['placementPolicy']
                if 'tags' in src: data['tags'] = src['tags']
                try:
                    self.post('/iaas/api/zones', data)
                    print('create cloud zone %s' % src['name'])
                except: print('ERROR: could not create cloud zone %s' % src['name'])
                

@register_object
class FabricCompute(VRAOBJ):
    
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        self.data2file(self.get('/iaas/api/fabric-computes?$limit=10000'))
    
#     def sync(self):
#         data = self.file2data()
#         computes = self.get('/iaas/api/fabric-computes')['content']
#         for content in data:
#             if 'tags' in content and content['tags']:
#                 print('fabric compute {}'.format(content['name']))
#                 externalRegionId = content['externalRegionId']
#                 externalId = content['externalId']
#                 for obj in computes:
#                     if obj['externalRegionId'] == externalRegionId and obj['externalId'] == externalId:
#                         self.patch('/iaas/api/fabric-computes/' + obj['id'], {
#                             'tags': content['tags']
#                         })
#                         break
#                 else: raise Exception('could not find fabric compute')

@register_object
class FabricNetwork(VRAOBJ):
    
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        self.data2file(self.get('/iaas/api/fabric-networks?$limit=10000'))
    
    def sync(self):
        srcs = self.file2data()
        tgts = self.get('/iaas/api/fabric-networks?$limit=10000')['content']
        src_ca = self.getCAFromFile()
        tgt_ca = self.getCAFromRest()
        for src in srcs:
            if 'tags' in src and src['tags']:
                for tgt in tgts:
                    if src['name'] == tgt['name'] and src_ca[self.getCAID(src)] == tgt_ca[self.getCAID(tgt)]:
                        try:
                            self.patch('/iaas/api/fabric-networks/' + tgt['id'], {
                                'tags': src['tags']
                            })
                            print('set tags to fabric network %s' % src['name'])
                        except: print('ERROR: could not set tags to fabric network %s' % src['name'])
                        break
                else: print('ERROR: could not find fabric network %s' % src['name'])

@register_object
class FabricNetworkvSphere(VRAOBJ):

    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        self.data2file(self.get('/iaas/api/fabric-networks-vsphere?$limit=10000'))
    
    def sync(self):
        srcs = self.file2data()
        tgts = self.get('/iaas/api/fabric-networks-vsphere?$limit=10000')['content']
        src_ca = self.getCAFromFile()
        tgt_ca = self.getCAFromRest()
        for src in srcs:
            if 'tags' in src and src['tags']:
                for tgt in tgts:
                    if src['name'] == tgt['name'] and src_ca[self.getCAID(src)] == tgt_ca[self.getCAID(tgt)]:
                        data = {'cidr': src['cidr']}
                        if 'domain' in src: data['domain'] = src['domain']
                        if 'defaultGateway' in src: data['defaultGateway'] = src['defaultGateway']
                        if 'dnsServerAddresses' in src: data['dnsServerAddresses'] = src['dnsServerAddresses']
                        if 'dnsSearchDomains' in src: data['dnsSearchDomains'] = src['dnsSearchDomains']
                        if 'isDefault' in src: data['isDefault'] = src['isDefault']
                        try:
                            self.patch('/iaas/api/fabric-networks-vsphere/' + tgt['id'], data)
                            print('set cidr to fabric network %s' % src['name'])
                        except: print('ERROR: could not set cidr to fabric network %s' % src['name'])
                        break
                else: print('ERROR: could not find fabric network %s' % src['name'])

@register_object
class IPRange(VRAOBJ):
    
    def __init__(self, vra):
        VRAOBJ.__init__(self, vra)
    
    def dump(self):
        self.data2file(self.get('/iaas/api/network-ip-ranges?$limit=10000'))
    
    def sync(self):
        srcs = self.file2data()
        tgts = self.get('/iaas/api/network-ip-ranges?$limit=10000')['content']
        src_nets = self.file2data('FabricNetwork')
        tgt_nets = self.get('/iaas/api/fabric-networks?$limit=10000')['content']
        src_ca = self.getCAFromFile()
        tgt_ca = self.getCAFromRest()
        for src in srcs:
            net_id = src['_links']['fabric-network']['href'].split('fabric-networks/')[1]
            for net in src_nets:
                if net['id'] == net_id:
                    src_ca_name = src_ca[self.getCAID(net)]
                    src_net_name = net['name']
                    break
            else:
                print('ERROR: could not source network %s' % src['name'])
                continue
            for net in tgt_nets:
                if net['name'] == src_net_name and tgt_ca[self.getCAID(net)] == src_ca_name:
                    net_id = net['id']
                    break
            else:
                print('ERROR: could not target network %s' % src['name'])
                continue
            full_net_id = '/iaas/api/fabric-networks/' + net_id
            for tgt in tgts:
                if src['name'] == tgt['name'] and tgt['_links']['fabric-network']['href'] == full_net_id:
                    try:
                        self.patch('/iaas/api/network-ip-ranges/' + tgt['id'], {
                            'fabricNetworkId': net_id,
                            'name': src['name'],
                            'ipVersion': src['ipVersion'],
                            'startIPAddress': src['startIPAddress'],
                            'endIPAddress': src['endIPAddress']
                        })
                        print('set ip range %s' % src['name'])
                    except: print('ERROR: could not set ip range %s' % src['name'])
                    break
            else:
                try:
                    self.post('/iaas/api/network-ip-ranges', {
                        'fabricNetworkId': net_id,
                        'name': src['name'],
                        'ipVersion': src['ipVersion'],
                        'startIPAddress': src['startIPAddress'],
                        'endIPAddress': src['endIPAddress']
                    })
                    print('set ip range %s' % src['name'])
                except: print('ERROR: could not set ip range %s' % src['name'])
