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

from .common import VRAOBJ, register_object

@register_object
class CloudAccount(VRAOBJ):
    
    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)
    
    def _dump(self):
        data = self.get('/iaas/api/cloud-accounts?$limit=10000')
        self.printDataInfo(data)
        result = {}
        for d in data['content']: result[d['id']] = d['name']
        CloudAccount.write(self.role, result)
    
    def dump_80(self): self._dump()
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()


@register_object
class CloudRegion(VRAOBJ):
    
    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)
    
    def _dump(self):
        data = self.get('/iaas/api/regions?$limit=10000')
        self.printDataInfo(data)
        ca = CloudAccount.read(self.role)
        objs = {}
        for d in data['content']:
            objs[d['id']] = {
                'name': d['name'],
                'cloudAccount': ca[d['cloudAccountId']],
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['cloudAccount'])
        }
        CloudRegion.write(self.role, result)
        
    def dump_80(self): self._dump()        
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()


@register_object
class CloudZone(VRAOBJ):
     
    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)
    
    def _dump(self):
        data = self.get('/iaas/api/zones?$limit=10000')
        self.printDataInfo(data)
        regions = CloudRegion.read(self.role)
        objs = {}
        for d in data['content']:
            obj = {
                'name': d['name'],
                'customProperties': d['customProperties'] if 'customProperties' in d['customProperties'] else {},
                'regionId': regions['objs'][d['_links']['region']['href'].split('regions/')[1]]['name']
            }
            if 'folder' in d: obj['folder'] = d['folder']
            if 'tagsToMatch' in d: obj['tagsToMatch'] = d['tagsToMatch']
            if 'description' in d: obj['description'] = d['description']
            if 'placementPolicy' in d: obj['placementPolicy'] = d['placementPolicy']
            if 'tags' in d: obj['tags'] = sorted(d['tags'], key=lambda x: x['key'] + x['value'])
            objs[d['id']] = obj
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['regionId'])
        }
        CloudZone.write(self.role, result)
    
    def dump_80(self): self._dump()        
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()
    
    def _sync(self):
        srcs = self.__class__.read('src')
        tgts = self.__class__.read('tgt')
        regions = CloudRegion.read(self.role)
        completed = 0
        for src_link in srcs['link']:
            src = srcs['objs'][src_link]
            for tgt in tgts['objs'].values(): # find same name
                if src['name'] == tgt['name']:
                    print('│ bypass cloud zone [%s]' % src['name'])
                    completed += 1
                    break
            else: # if not exist, create cloud zone
                region_name = src['regionId']
                for id, region in regions['objs'].items():
                    if region['name'] == region_name:
                        src['regionId'] = id
                        break
                else:
                    print('│ ! error: could not find region of cloud zone [%s]' % src['name'])
                try: self.post('/iaas/api/zones', src)
                except: print('│ ! error: could not create cloud zone [%s]' % src['name'])
                else:
                    print('│ * create cloud zone [%s]' % src['name'])
                    completed += 1
        print('│\n│ src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
    
    def sync_80(self): self._sync()
    def sync_81(self): self._sync()
    def sync_82(self): self._sync()
                

@register_object
class FabricCompute(VRAOBJ):
      
    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)
     
    def dump_80(self): # /provisioning/mgmt/compute?expand
        data = self.getUerp('/provisioning/mgmt/compute?expand&$top=10000&$filter=((type%20eq%20%27VM_HOST%27)%20or%20(type%20eq%20%27ZONE%27))')
        self.printDataInfo(data)
        objs = {}
        for id, d in data['documents'].items():
            objs[id] = {
                'name': d['name'],
                'externalId': d['customProperties']['vcUuid'] if 'vcUuid' in d['customProperties'] else d['id'],
                'payload': {
                    'tags': sorted([{'key': t['key'], 'value': t['value']} for t in d['tags']] if 'tags' in d else [], key=lambda x: x['key'] + x['value'])
                }
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['externalId'])
        }
        FabricCompute.write(self.role, result)
     
    def dump_81(self):
        data = self.get('/iaas/api/fabric-computes?$limit=10000')
        self.printDataInfo(data)
        objs = {}
        for d in data['content']:
            objs[d['id']] = {
                'name': d['name'],
                'externalId': d['customProperties']['vcUuid'] if 'vcUuid' in d['customProperties'] else d['externalId'],
                'payload': {
                    'tags': sorted(d['tags'], key=lambda x: x['key'] + x['value']) if 'tags' in d else []                
                }
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['externalId'])
        }
        FabricCompute.write(self.role, result)
    
    def dump_82(self): self.dump_81()
    
    def _sync(self):
        srcs = FabricCompute.read('src')
        tgts = FabricCompute.read('tgt')
        completed = 0
        for src_link in srcs['link']:
            src = srcs['objs'][src_link]
            for id, tgt in tgts['objs'].items():
                if src['externalId'] == tgt['externalId']:
                    try: self.patch('/iaas/api/fabric-computes/' + id, src['payload'])
                    except: print('│ ! error: could not set tag to fabric compute [%s]' % src['name'])
                    else:
                        print('│ * set tag to fabric compute [%s]' % src['name'])
                        completed += 1
                    break
            else: print('│ ! error: could not find fabric compute [%s]' % src['name'])
        print('│\n│ src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
    
    def sync_81(self): self._sync()
    def sync_82(self): self._sync()


@register_object
class FabricNetwork(VRAOBJ):
     
    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)
    
    def _dump(self):
        data = self.get('/iaas/api/fabric-networks?$limit=10000')
        self.printDataInfo(data)
        ca = CloudAccount.read(self.role)
        objs = {}
        for d in data['content']:
            objs[d['id']] = {
                'name': d['name'],
                'cloudAccount': ca[d['_links']['cloud-accounts']['hrefs'][0].split('cloud-accounts/')[1]],
                'payload': {
                    'tags': sorted(d['tags'], key=lambda x: x['key'] + x['value']) if 'tags' in d else []
                }
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['cloudAccount'])
        }
        FabricNetwork.write(self.role, result)
    
    def dump_80(self): self._dump()
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()
    
    def _sync(self):
        srcs = FabricNetwork.read('src')
        tgts = FabricNetwork.read('tgt')
        completed = 0
        for src_link in srcs['link']:
            src = srcs['objs'][src_link]
            for id, tgt in tgts['objs'].items():
                if src['name'] == tgt['name'] and src['cloudAccount'] == tgt['cloudAccount']:
                    try: self.patch('/iaas/api/fabric-networks/' + id, src['payload'])
                    except: print('│ ! error: could not set tag to fabric network [%s]' % src['name'])
                    else:
                        print('│ * set tag to fabric network [%s]' % src['name'])
                        completed += 1
                    break
            else: print('│ ! error: could not find fabric network [%s]' % src['name'])
        print('│\n│ src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
    
    def sync_80(self): self._sync()
    def sync_81(self): self._sync()
    def sync_82(self): self._sync()


@register_object
class FabricNetworkvSphere(VRAOBJ):
 
    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)
     
    def _dump(self):
        data = self.get('/iaas/api/fabric-networks-vsphere?$limit=10000')
        self.printDataInfo(data)
        ca = CloudAccount.read(self.role)
        objs = {}
        for d in data['content']:
            objs[d['id']] = {
                'name': d['name'],
                'cloudAccount': ca[d['_links']['cloud-accounts']['hrefs'][0].split('cloud-accounts/')[1]],
                'payload': {
                    'cidr': d['cidr'] if 'cidr' in d else '',
                    'ipv6Cidr': d['ipv6Cidr'] if 'ipv6Cidr' in d else '',
                    'isDefault': d['isDefault'] if 'isDefault' in d else False,
                    'domain': d['domain'] if 'domain' in d else '',
                    'defaultGateway': d['defaultGateway'] if 'defaultGateway' in d else '',
                    'defaultIpv6Gateway': d['defaultIpv6Gateway'] if 'defaultIpv6Gateway' in d else '',
                    'dnsServerAddresses': d['dnsServerAddresses'] if 'dnsServerAddresses' in d else [],
                    'dnsSearchDomains': d['dnsSearchDomains'] if 'dnsSearchDomains' in d else []
                }
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['cloudAccount'])
        }
        FabricNetworkvSphere.write(self.role, result)
    
    def dump_80(self): self._dump()
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()
    
    def _sync(self):
        srcs = FabricNetworkvSphere.read('src')
        tgts = FabricNetworkvSphere.read('tgt')
        completed = 0
        for src_link in srcs['link']:
            src = srcs['objs'][src_link]
            for id, tgt in tgts['objs'].items():
                if src['name'] == tgt['name'] and src['cloudAccount'] == tgt['cloudAccount']:
                    try: self.patch('/iaas/api/fabric-networks-vsphere/' + id, src['payload'])
                    except: print('│ ! error: could not set subnet to fabric network vsphere [%s]' % src['name'])
                    else:
                        print('│ * set subnet to fabric network vsphere [%s]' % src['name'])
                        completed += 1
                    break
            else: print('│ ! error: could not find fabric network vsphere [%s]' % src['name'])
        print('│\n│ src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
    
    def sync_80(self): self._sync()
    def sync_81(self): self._sync()
    def sync_82(self): self._sync()


@register_object
class IPRange(VRAOBJ):
      
    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)
      
    def _dump(self):
        data = self.get('/iaas/api/network-ip-ranges?$limit=10000')
        self.printDataInfo(data)
        networks = FabricNetwork.read(self.role)
        objs = {}
        for d in data['content']:
            network_id = d['_links']['fabric-network']['href'].split('fabric-networks/')[1]
            network = networks['objs'][network_id]
            objs[d['id']] = {
                'name': d['name'],
                'cloudAccount': network['cloudAccount'],
                'network': network['name'],
                'payload': {
                    'fabricNetworkId': network_id,
                    'name': d['name'],
                    'ipVersion': d['ipVersion'],
                    'startIPAddress': d['startIPAddress'],
                    'endIPAddress': d['endIPAddress']
                }
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['cloudAccount'] + objs[x]['network'])
        }
        IPRange.write(self.role, result)
     
    def dump_80(self): self._dump()
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()
     
    def _sync(self):
        srcs = IPRange.read('src')
        tgts = IPRange.read('tgt')
        networks = FabricNetwork.read(self.role)
        completed = 0
        for src_link in srcs['link']:
            src = srcs['objs'][src_link]
            for id, tgt in tgts['objs'].items():
                if src['name'] == tgt['name'] and src['cloudAccount'] == tgt['cloudAccount'] and src['network'] == tgt['network']:
                    src['payload']['fabricNetworkId'] = tgt['payload']['fabricNetworkId']
                    try: self.patch('/iaas/api/network-ip-ranges/' + id, src['payload'])
                    except: print('│ ! error: could not update ip range [%s]' % src['name'])
                    else:
                        print('│ * update ip range [%s]' % src['name'])
                        completed += 1
                    break
            else:
                for id, network in networks['objs'].items():
                    if src['network'] == network['name'] and src['cloudAccount'] == network['cloudAccount']:
                        src['payload']['fabricNetworkId'] = id
                        try: self.post('/iaas/api/network-ip-ranges', src['payload'])
                        except: print('│ ! error: could not create ip range [%s]' % src['name'])
                        else:
                            print('│ * create ip range [%s]' % src['name'])
                            completed += 1
                        break
                else: print('│ ! error: could not find fabric network of ip range [%s]' % src['name'])
        print('│\n│ src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
     
    def sync_80(self): self._sync()
    def sync_81(self): self._sync()
    def sync_82(self): self._sync()
