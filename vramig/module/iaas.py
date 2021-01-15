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
            cloud_account_id = d['cloudAccountId']
            objs[d['id']] = {
                'name': d['externalRegionId'],
                'cloudAccountId': cloud_account_id,
                'cloudAccount': ca[cloud_account_id]
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
        ca = CloudAccount.read(self.role)
        regions = CloudRegion.read(self.role)
        objs = {}
        for d in data['content']:
            cloud_account_id = d['_links']['cloud-account']['href'].split(self._ca_key)[1]
            region_id = d['_links']['region']['href'].split('regions/')[1]
            objs[d['id']] = {
                'name': d['name'],
                'cloudAccountId': cloud_account_id,
                'cloudAccount': ca[cloud_account_id],
                'regionId': region_id,
                'region': regions['objs'][region_id]['name'],
                'payload': {
                    'name': d['name'],
                    'description': d['description'] if 'description' in d else '',
                    'placementPolicy': d['placementPolicy'] if 'placementPolicy' in d else '',
                    'folder': d['folder'] if 'folder' in d else '',
                    'tagsToMatch': d['tagsToMatch'] if 'tagsToMatch' in d else '',
                    'tags': d['tags'] if 'tags' in d else '',
                    'customProperties': d['customProperties'] if 'customProperties' in d['customProperties'] else {}
                }
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['cloudAccount'] + objs[x]['region'])
        }
        CloudZone.write(self.role, result)
    
    def dump_80(self):
        self._ca_key = 'endpoints/'
        self._dump()        
    def dump_81(self):
        self._ca_key = 'cloud-accounts/'
        self._dump()
    def dump_82(self):
        self._ca_key = 'cloud-accounts/'
        self._dump()
    
    def _sync(self):
        srcs = CloudZone.read('src')
        tgts = CloudZone.read('tgt')
        ca = CloudAccount.read(self.role).values()
        regions = CloudRegion.read(self.role)
        completed = 0
        for src_link in srcs['link']:
            src = srcs['objs'][src_link]
            for id, tgt in tgts['objs'].items():
                if src['name'] == tgt['name'] and src['cloudAccount'] == tgt['cloudAccount'] and src['region'] == tgt['region']:
                    src['payload']['regionId'] = tgt['regionId']
                    try: self.patch('/iaas/api/zones/' + id, src['payload'])
                    except:
                        if self._debug: print('  ! error: could not update cloud zone [%s / %s]' % (src['name'], src['cloudAccount']))
                    else:
                        if self._debug: print('  * update cloud zone [%s / %s]' % (src['name'], src['cloudAccount']))
                        completed += 1
                    break
            else:
                cloud_account_name = src['cloudAccount']
                region_name = src['region']
                for rid, region in regions['objs'].items():
                    if region['name'] == region_name and region['cloudAccount'] == cloud_account_name:
                        src['payload']['regionId'] = rid
                        break
                else:
                    if self._debug: print('  ! error: could not find region of cloud zone [%s / %s]' % (src['name'], src['cloudAccount']))
                    continue
                try: self.post('/iaas/api/zones', src['payload'])
                except:
                    if self._debug: print('  ! error: could not create cloud zone [%s / %s]' % (src['name'], src['cloudAccount']))
                else:
                    if self._debug: print('  + create cloud zone [%s / %s]' % (src['name'], src['cloudAccount']))
                    completed += 1
        print('  src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
    
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
                if src['name'] == tgt['name'] and src['externalId'] == tgt['externalId']:
                    try: self.patch('/iaas/api/fabric-computes/' + id, src['payload'])
                    except:
                        if self._debug: print('  ! error: could not set tag to fabric compute [%s / %s]' % (src['name'], src['externalId']))
                    else:
                        if self._debug: print('  * set tag to fabric compute [%s / %s]' % (src['name'], src['externalId']))
                        completed += 1
                    break
            else:
                if self._debug: print('  ! error: could not find fabric compute [%s / %s]' % (src['name'], src['externalId']))
        print('  src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
    
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
            cloud_account_id = d['_links']['cloud-accounts']['hrefs'][0].split('cloud-accounts/')[1]
            objs[d['id']] = {
                'name': d['name'],
                'cloudAccountId': cloud_account_id,
                'cloudAccount': ca[cloud_account_id]
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['cloudAccount'])
        }
        FabricNetwork.write(self.role, result)
    
    def dump_80(self): self._dump()
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()
    
#    def _sync(self):
#        srcs = FabricNetwork.read('src')
#        tgts = FabricNetwork.read('tgt')
#        completed = 0
#        for src_link in srcs['link']:
#            src = srcs['objs'][src_link]
#            for id, tgt in tgts['objs'].items():
#                if src['name'] == tgt['name'] and src['cloudAccount'] == tgt['cloudAccount']:
#                    try: self.patch('/iaas/api/fabric-networks/' + id, src['payload'])
#                    except:
#                        if self._debug: print('  ! error: could not set tag to fabric network [%s]' % src['name'])
#                    else:
#                        if self._debug: print('  * set tag to fabric network [%s]' % src['name'])
#                        completed += 1
#                    break
#            else:
#                if self._debug: print('  ! error: could not find fabric network [%s : %s]' % (src['name'], src['cloudAccount']))
#        print('  src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
#    
#    def sync_80(self): self._sync()
#    def sync_81(self): self._sync()
#    def sync_82(self): self._sync()


@register_object
class FabricNetworkvSphere(VRAOBJ):
 
    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)
     
    def _dump(self):
        data = self.get('/iaas/api/fabric-networks-vsphere?$limit=10000')
        self.printDataInfo(data)
        ca = CloudAccount.read(self.role)
        objs = {}
        for d in data['content']:
            cloud_account_id = d['_links']['cloud-accounts']['hrefs'][0].split('cloud-accounts/')[1]
            objs[d['id']] = {
                'name': d['name'],
                'cloudAccountId': cloud_account_id,
                'cloudAccount': ca[cloud_account_id],
                'payload': {
                    'cidr': d['cidr'] if 'cidr' in d else '',
                    'ipv6Cidr': d['ipv6Cidr'] if 'ipv6Cidr' in d else '',
                    'isDefault': d['isDefault'] if 'isDefault' in d else False,
                    'domain': d['domain'] if 'domain' in d else '',
                    'defaultGateway': d['defaultGateway'] if 'defaultGateway' in d else '',
                    'defaultIpv6Gateway': d['defaultIpv6Gateway'] if 'defaultIpv6Gateway' in d else '',
                    'dnsServerAddresses': d['dnsServerAddresses'] if 'dnsServerAddresses' in d else [],
                    'dnsSearchDomains': d['dnsSearchDomains'] if 'dnsSearchDomains' in d else [],
                    'tags': d['tags'] if 'tags' in d else []
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
                    except:
                        if self._debug: print('  ! error: could not set subnet to fabric network vsphere [%s / %s]' % (src['name'], src['cloudAccount']))
                    else:
                        if self._debug: print('  * set subnet to fabric network vsphere [%s / %s]' % (src['name'], src['cloudAccount']))
                        completed += 1
                    break
            else:
                if self._debug: print('  ! error: could not find fabric network vsphere [%s / %s]' % (src['name'], src['cloudAccount']))
        print('  src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
    
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
                'cloudAccountId': network['cloudAccountId'],
                'cloudAccount': network['cloudAccount'],
                'networkId': network_id,
                'network': network['name'],
                'payload': {
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
                    src['payload']['fabricNetworkId'] = tgt['networkId']
                    try: self.patch('/iaas/api/network-ip-ranges/' + id, src['payload'])
                    except:
                        if self._debug: print('  ! error: could not update ip range [%s / %s]' % (src['name'], src['cloudAccount']))
                    else:
                        if self._debug: print('  * update ip range [%s / %s]' % (src['name'], src['cloudAccount']))
                        completed += 1
                    break
            else:
                for nid, network in networks['objs'].items():
                    if src['network'] == network['name'] and src['cloudAccount'] == network['cloudAccount']:
                        src['payload']['fabricNetworkId'] = nid
                        try: self.post('/iaas/api/network-ip-ranges', src['payload'])
                        except:
                            if self._debug: print('  ! error: could not create ip range [%s / %s]' % (src['name'], src['cloudAccount']))
                        else:
                            if self._debug: print('  * create ip range [%s / %s]' % (src['name'], src['cloudAccount']))
                            completed += 1
                        break
                else:
                    if self._debug: print('  ! error: could not find fabric network of ip range [%s]' % src['name'])
        print('  src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))
     
    def sync_80(self): self._sync()
    def sync_81(self): self._sync()
    def sync_82(self): self._sync()


@register_object
class NetworkProfile(VRAOBJ):

    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)

    def _dump(self):
        data = self.get('/iaas/api/network-profiles?$limit=10000')
        self.printDataInfo(data)
        regions = CloudRegion.read(self.role)
        networks = FabricNetwork.read(self.role)
        objs = {}
        for d in data['content']:
            region_id = d['_links']['region']['href'].split('regions/')[1]
            region = regions['objs'][region_id]
            fabricNetworkIds = []
            for nid in d['_links']['fabric-networks']['hrefs']:
                network = networks['objs'][nid.split('fabric-networks/')[1]]
                fabricNetworkIds.append({
                    'name': network['name'],
                    'cloudAccount': network['cloudAccount']
                })
            obj = {
                'name': d['name'],
                'cloudAccountId': region['cloudAccountId'],
                'cloudAccount': region['cloudAccount'],
                'regionId': region_id,
                'region': region['name'],
                'payload': {
                    'name': d['name'],
                    'description': d['description'] if 'description' in d else '',
                    'isolationType': d['isolationType'] if 'isolationType' in d else '',
                    'fabricNetworkIds': fabricNetworkIds,
                    'customProperties': d['customProperties'] if 'customProperties' in d else {},
                    'tags': d['tags'] if 'tags' in d else []
                    # 'securityGroupIds': []
                    # 'loadBalancerIds': []
                }
            }
            if 'isolationNetworkDomainId' in d: obj['payload']['isolationNetworkDomainId'] = d['isolationNetworkDomainId']
            if 'isolationNetworkDomainCIDR' in d: obj['payload']['isolationNetworkDomainCIDR'] = d['isolationNetworkDomainCIDR']
            if 'isolationExternalFabricNetworkId' in d: obj['payload']['isolationExternalFabricNetworkId'] = d['isolationExternalFabricNetworkId']
            if 'isolatedNetworkCIDRPrefix' in d: obj['payload']['isolatedNetworkCIDRPrefix'] = d['isolatedNetworkCIDRPrefix']
            objs[d['id']] = obj
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['cloudAccount'] + objs[x]['region'])
        }
        NetworkProfile.write(self.role, result)

    def dump_80(self): self._dump()
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()

    def _sync(self):
        srcs = NetworkProfile.read('src')
        tgts = NetworkProfile.read('tgt')
        ca = CloudAccount.read(self.role).values()
        regions = CloudRegion.read(self.role)
        networks = FabricNetwork.read(self.role)
        completed = 0
        for src_link in srcs['link']:
            src = srcs['objs'][src_link]
            if src['cloudAccount'] not in ca:
                if self._debug: print('  ! error: could not find cloud account of network profile [%s / %s]' % (src['name'], src['cloudAccount']))
                continue
            fabricNetworkIds = []
            for n in src['payload']['fabricNetworkIds']:
                for nid, network in networks['objs'].items():
                    if n['name'] == network['name'] and n['cloudAccount'] == network['cloudAccount']:
                        fabricNetworkIds.append(nid)
                        break
                else:
                    if self._debug: print('  ! error: could not find fabric network of network profile [%s / %s]' % (src['name'], src['cloudAccount']))
            src['payload']['fabricNetworkIds'] = fabricNetworkIds
            for id, tgt in tgts['objs'].items():
                if src['name'] == tgt['name'] and src['cloudAccount'] == tgt['cloudAccount'] and src['region'] == tgt['region']:
                    src['payload']['regionId'] = tgt['regionId']
                    try: self.patch('/iaas/api/network-profiles/' + id, src['payload'])
                    except:
                        if self._debug: print('  ! error: could not create network profile [%s / %s]' % (src['name'], src['cloudAccount']))
                    else:
                        if self._debug: print('  * update network profile [%s / %s]' % (src['name'], src['cloudAccount']))
                        completed += 1
                    break
            else:
                cloud_account_name = src['cloudAccount']
                region_name = src['region']
                for rid, region in regions['objs'].items():
                    if region['name'] == region_name and region['cloudAccount'] == cloud_account_name:
                        src['payload']['regionId'] = rid
                        try: self.post('/iaas/api/network-profiles', src['payload'])
                        except:
                            if self._debug: print('  ! error: could not create network profile [%s / %s]' % (src['name'], src['cloudAccount']))
                        else:
                            if self._debug: print('  + create network profile [%s / %s]' % (src['name'], src['cloudAccount']))
                            completed += 1
                        break
                else:
                    if self._debug: print('  ! error: could not find region of network profile [%s / %s]' % (src['name'], src['cloudAccount']))
        print(' src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))

    def sync_80(self): self._sync()
    def sync_81(self): self._sync()
    def sync_82(self): self._sync()


@register_object
class FabricDatastore(VRAOBJ):

    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)

    def _dump(self):
        data = self.get('/iaas/api/fabric-vsphere-datastores?$limit=10000')
        self.printDataInfo(data)
        ca = CloudAccount.read(self.role)
        regions = CloudRegion.read(self.role)
        objs = {}
        for d in data['content']:
            cloud_account_id = d['_links']['cloud-accounts']['hrefs'][0].split('cloud-accounts/')[1]
            region_id = d['_links']['region']['href'].split('regions/')[1]
            objs[d['id']] = {
                'name': d['name'],
                'cloudAccountId': cloud_account_id,
                'cloudAccount': ca[cloud_account_id],
                'regionId': region_id,
                'region': regions['objs'][region_id]['name']
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['cloudAccount'] + objs[x]['region'])
        }
        FabricDatastore.write(self.role, result)

    def dump_80(self): self._dump()
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()


@register_object
class FabricDatastorevSphere(VRAOBJ):

    def __init__(self, src_vra, tgt_vra): VRAOBJ.__init__(self, src_vra, tgt_vra)

    def _dump(self):
        data = self.get('/iaas/api/storage-profiles-vsphere?$limit=10000')
        self.printDataInfo(data)
        regions = CloudRegion.read(self.role)
        datastores = FabricDatastore.read(self.role)
        objs = {}
        for d in data['content']:
            region_id = d['_links']['region']['href'].split('regions/')[1]
            region = regions['objs'][region_id]
            datastore_id = d['_links']['datastore']['href'].split('datastores/')[1]
            datastore = datastores['objs'][datastore_id]
            objs[d['id']] = {
                'name': d['name'],
                'cloudAccountId': region['cloudAccountId'],
                'cloudAccount': region['cloudAccount'],
                'regionId': region_id,
                'region': region['name'],
                'datastoreId': datastore_id,
                'datastore': datastore['name'],
                'payload': {
                    'name': d['name'],
                    'description': d['description'] if 'description' in d else '',
                    'defaultItem': d['defaultItem'] if 'defaultItem' in d else False,
                    'sharesLevel': d['sharesLevel'] if 'sharesLevel' in d else '',
                    'provisioningType': d['provisioningType'] if 'provisioningType' in d else '',
                    'limitIops': d['limitIops'] if 'limitIops' in d else '',
                    'shares': d['shares'] if 'shares' in d else '',
                    'diskMode': d['diskMode'] if 'diskMode' in d else '',
                    'supportsEncryption': d['supportsEncryption'] if 'supportsEncryption' in d else '',
                    'tags': d['tags'] if 'tags' in d else []
                    # 'storagePolicyId': ''
                }
            }
        result = {
            'objs': objs,
            'link': sorted(objs.keys(), key=lambda x: objs[x]['name'] + objs[x]['cloudAccount'] + objs[x]['region'])
        }
        FabricDatastorevSphere.write(self.role, result)

    def dump_80(self): self._dump()
    def dump_81(self): self._dump()
    def dump_82(self): self._dump()

    def _sync(self):
        srcs = FabricDatastorevSphere.read('src')
        tgts = FabricDatastorevSphere.read('tgt')
        regions = CloudRegion.read(self.role)
        datastores = FabricDatastore.read(self.role)
        completed = 0
        for src_link in srcs['link']:
            src = srcs['objs'][src_link]
            for id, tgt in tgts['objs'].items():
                if src['name'] == tgt['name'] and src['cloudAccount'] == tgt['cloudAccount'] and src['region'] == tgt['region'] and src['datastore'] == tgt['datastore']:
                    src['payload']['regionId'] = tgt['regionId']
                    src['payload']['datastoreId'] = tgt['datastoreId']
                    try: self.patch('/iaas/api/storage-profiles-vsphere/' + id, src['payload'])
                    except:
                        if self._debug: print('  ! error: could not update fabric datastore vsphere [%s / %s]' % (src['name'], src['cloudAccount']))
                    else:
                        if self._debug: print('  * update fabric datastore vsphere [%s / %s]' % (src['name'], src['cloudAccount']))
                        completed += 1
                    break
            else:
                cloud_account_name = src['cloudAccount']
                region_name = src['region']
                for rid, region in regions['objs'].items():
                    if region['name'] == region_name and region['cloudAccount'] == cloud_account_name:
                        src['payload']['regionId'] = rid
                        datastore_name = src['datastore']
                        for did, datastore in datastores['objs'].items():
                            if datastore['name'] == datastore_name and datastore['cloudAccount'] == cloud_account_name and datastore['region'] == region_name:
                                src['payload']['datastoreId'] = did
                                try: self.post('/iaas/api/storage-profiles-vsphere', src['payload'])
                                except:
                                    if self._debug: print('  ! error: could not create fabric datastore vsphere [%s / %s]' % (src['name'], src['cloudAccount']))
                                else:
                                    if self._debug: print('  + create fabric datastore vsphere [%s / %s]' % (src['name'], src['cloudAccount']))
                                    completed += 1
                                break
                        else:
                            if self._debug: print('  ! error: could not find datastore of fabric datastore vsphere [%s / %s]' % (src['name'], src['cloudAccount']))
                        break
                else:
                    if self._debug: print('  ! error: could not find region of fabric datastore vsphere [%s / %s]' % (src['name'], src['cloudAccount']))
        print('  src[ %d ] : tgt[ %d ] = sync[ %d ] ' % (len(srcs['link']), len(tgts['link']), completed))

    def sync_80(self): self._sync()
    def sync_81(self): self._sync()
    def sync_82(self): self._sync()





