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

import sys
import json
from .common import Object, register_object, isDebug, jps, jpp
   
@register_object
class CloudAccount(Object):
    
    RELATIONS = []
    LOAD_URL = '/iaas/api/cloud-accounts?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, *rels):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['name']
            map[id] = name
            ids.append(id)
            dns[name] = id
            count += 1
        return map, ids, dns, count


@register_object
class CloudRegion(Object):
    
    RELATIONS = [CloudAccount]
    LOAD_URL = '/iaas/api/regions?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, accounts):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['externalRegionId']
            ca = accounts.findID(d['cloudAccountId'])
            dn = ca + '/' + name
            map[id] = {'id': id, 'name': name, 'ca': ca, 'dn': dn}
            ids.append(id)
            dns[dn] = id
            count += 1
        return map, ids, dns, count
    

@register_object
class FabricCompute(Object):
    
    RELATIONS = [CloudAccount, CloudRegion]
    LOAD_URL = '/provisioning/mgmt/compute?expand&$top=10000&$filter=((type%20eq%20%27VM_HOST%27)%20or%20(type%20eq%20%27ZONE%27))'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, accounts, regions):
        map, ids, dns, count = {}, [], {}, 0
        for id, d in data['documents'].items():
            id = id.split('/compute/')[1]
            name = d['name']
            ca = accounts.findDN(d['endpoints'][0]['name'])
            rg = regions.findDN(ca + '/' + d['regionId'])['name']
            dn = ca + '/' + rg + '/' + name
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'rg': rg, 'dn': dn,
                'payload': {
                    'tags': sorted([{'key': t['key'], 'value': t['value']} for t in d['tags']] if 'tags' in d else [], key=lambda x: x['key'] + x['value'])
                }
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count
    
    def sync(self, vra, src, accounts, regions):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            t = self.findDN(dn)
            if t == None:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find fabric compute dn [%s]' % dn)
                continue
            try: vra.patch('/iaas/api/fabric-computes/' + t['id'], s['payload'])
            except Exception as e:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not set tag to fabric compute [%s]' % dn)
            else:
                print(' *', end=''); sys.stdout.flush()
                if isDebug(): print(' set tag to fabric compute [%s]' % dn)
                completed += 1
        print('')
        return completed


@register_object
class CloudZone(Object):
    
    RELATIONS = [CloudRegion]
    LOAD_URL = '/iaas/api/zones?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, regions):
        map, ids, dns, count = {}, [], {}, 0
        if self.ver == 80: self.delimeter = 'endpoints/'
        else: self.delimeter = 'cloud-accounts/'
        for d in data['content']:
            id = d['id']
            name = d['name']
            region = regions.findID(d['_links']['region']['href'].split('regions/')[1])
            ca = region['ca']
            rg = region['name']
            dn = ca + '/' + rg + '/' + name
            # Payload ##############################
            payload = {'name': name}
            if 'description' in d: payload['description'] = d['description']
            if 'placementPolicy' in d: payload['placementPolicy'] = d['placementPolicy']
            if 'folder' in d: payload['folder'] = d['folder']
            if 'tagsToMatch' in d: payload['tagsToMatch'] = d['tagsToMatch']
            if 'tags' in d: payload['tags'] = d['tags']
            if 'customProperties' in d: payload['customProperties'] = d['customProperties']
            # Payload ##############################
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'rg': rg, 'dn': dn,
                'payload': payload
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count
    
    def sync(self, vra, src, regions):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            region = regions.findDN(s['ca'] + '/' + s['rg'])
            if region:
                s['payload']['regionId'] = region['id']
                t = self.findDN(dn)
                if t == None: # Create
                    try: vra.post('/iaas/api/zones', s['payload'])
                    except Exception as e:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not create cloud zone [%s]' % dn)
                    else:
                        print(' +', end=''); sys.stdout.flush()
                        if isDebug(): print(' create cloud zone [%s]' % dn)
                        completed += 1
                else: # Update
                    try: vra.patch('/iaas/api/zones/' + t['id'], s['payload'])
                    except:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not update cloud zone [%s]' % dn)
                    else:
                        print(' *', end=''); sys.stdout.flush()
                        if isDebug(): print(' update cloud zone [%s]' % dn)
                        completed += 1
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find region of cloud zone [%s]' % dn)
        print('')
        return completed


@register_object
class NetworkDomain(Object):
    
    RELATIONS = [CloudAccount]
    LOAD_URL = '/iaas/api/network-domains?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, accounts):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['name']
            ca = accounts.findID(d['_links']['cloud-accounts']['hrefs'][0].split('cloud-accounts/')[1])
            dn = ca + '/' + name
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'dn': dn
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count
    

@register_object
class FabricNetwork(Object):
    
    RELATIONS = [CloudAccount]
    LOAD_URL = '/iaas/api/fabric-networks?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, accounts):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['name']
            ca = accounts.findID(d['_links']['cloud-accounts']['hrefs'][0].split('cloud-accounts/')[1])
            dn = ca + '/' + name
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'dn': dn
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count


@register_object
class FabricNetworkvSphere(Object):
    
    RELATIONS = [CloudAccount]
    LOAD_URL = '/iaas/api/fabric-networks-vsphere?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, accounts):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['name']
            ca = accounts.findID(d['_links']['cloud-accounts']['hrefs'][0].split('cloud-accounts/')[1])
            dn = ca + '/' + name
            # Payload ##############################
            payload = {}
            if 'cidr' in d: payload['cidr'] = d['cidr']
            if 'ipv6Cidr' in d: payload['ipv6Cidr'] = d['ipv6Cidr']
            if 'isDefault' in d: payload['isDefault'] = d['isDefault']
            if 'domain' in d: payload['domain'] = d['domain']
            if 'defaultGateway' in d: payload['defaultGateway'] = d['defaultGateway']
            if 'defaultIpv6Gateway' in d: payload['defaultIpv6Gateway'] = d['defaultIpv6Gateway']
            if 'dnsServerAddresses' in d: payload['dnsServerAddresses'] = d['dnsServerAddresses']
            if 'dnsSearchDomains' in d: payload['dnsSearchDomains'] = d['dnsSearchDomains']
            if 'tags' in d: payload['tags'] = d['tags']
            # Payload ##############################
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'dn': dn,
                'payload': payload
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count
    
    def sync(self, vra, src, accounts):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            t = self.findDN(dn)
            if t:
                try: vra.patch('/iaas/api/fabric-networks-vsphere/' + t['id'], s['payload'])
                except Exception as e:
                    print(' !', end=''); sys.stdout.flush()
                    if isDebug(): print(' could not update to fabric network vsphere [%s]' % dn)
                else:
                    print(' *', end=''); sys.stdout.flush()
                    if isDebug(): print(' update fabric network vsphere [%s]' % dn)
                    completed += 1
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find fabric network vsphere [%s]' % dn)
        print('')
        return completed
    

@register_object
class IPRange(Object):
    
    RELATIONS = [FabricNetwork]
    LOAD_URL = '/iaas/api/network-ip-ranges?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, networks):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['name']
            network = networks.findID(d['_links']['fabric-network']['href'].split('fabric-networks/')[1])
            ca = network['ca']
            net = network['name']
            dn = ca + '/' + net + '/' + name
            # Payload ##############################
            payload = {'name': name}
            if 'description' in d: pyaload['description'] = d['description']
            if 'ipVersion' in d: payload['ipVersion'] = d['ipVersion']
            if 'startIPAddress' in d: payload['startIPAddress'] = d['startIPAddress']
            if 'endIPAddress' in d: payload['endIPAddress'] = d['endIPAddress']
            # Payload ##############################
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'net': net, 'dn': dn,
                'payload': payload
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count
    
    def sync(self, vra, src, networks):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            network = networks.findDN(s['ca'] + '/' + s['net'])
            if network:
                s['payload']['fabricNetworkId'] = network['id']
                t = self.findDN(dn)
                if t == None: # Create
                    try: vra.post('/iaas/api/network-ip-ranges', s['payload'])
                    except Exception as e:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not create ip range [%s]' % dn)
                    else:
                        print(' +', end=''); sys.stdout.flush()
                        if isDebug(): print(' create ip range [%s]' % dn)
                        completed += 1
                else: # Update
                    try: vra.patch('/iaas/api/network-ip-ranges/' + t['id'], s['payload'])
                    except:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not update ip range [%s]' % dn)
                    else:
                        print(' *', end=''); sys.stdout.flush()
                        if isDebug(): print(' update ip range [%s]' % dn)
                        completed += 1
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find network of ip range [%s]' % dn)
        print('')
        return completed


@register_object
class NetworkProfile(Object):
    
    RELATIONS = [CloudRegion, NetworkDomain, FabricNetwork]
    LOAD_URL = '/iaas/api/network-profiles?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, regions, domains, networks):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            if 'fabric-networks' not in d['_links'] and 'network-domains' not in d['_links']: continue;
            id = d['id']
            name = d['name']
            region = regions.findID(d['_links']['region']['href'].split('regions/')[1])
            ca = region['ca']
            rg = region['name']
            dn = ca + '/' + rg + '/' + name
            # Payload ##############################
            dom_dn = None
            if 'network-domains' in d['_links']:
                dom_dn = domains.findID(d['_links']['network-domains']['href'].split('network-domains/')[1])['dn']
            net_dns = []
            if 'fabric-networks' in d['_links']:
                for net_id in d['_links']['fabric-networks']['hrefs']:
                    try: net_dns.append(networks.findID(net_id.split('fabric-networks/')[1])['dn'])
                    except: pass
            exn_dn = None
            if 'isolated-external-fabric-networks' in d['_links']:
                exn_dn = networks.findID(d['_links']['isolated-external-fabric-networks']['href'].split('fabric-networks/')[1])['dn']
            payload = {'name': name}
            if 'description' in d: payload['description'] = d['description']
            if 'isolationType' in d: payload['isolationType'] = d['isolationType']
#             if 'customProperties' in d: payload['customProperties'] = d['customProperties']
            if 'tags' in d: payload['tags'] = d['tags']
            if 'isolationNetworkDomainCIDR' in d: payload['isolationNetworkDomainCIDR'] = d['isolationNetworkDomainCIDR']
            if 'isolatedNetworkCIDRPrefix' in d: payload['isolatedNetworkCIDRPrefix'] = d['isolatedNetworkCIDRPrefix']
            # Payload ##############################
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'rg': rg, 'dn': dn,
                'dom_dn': dom_dn,
                'net_dns': net_dns,
                'exn_dn': exn_dn,
                'payload': payload
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count
    
    def sync(self, vra, src, regions, domains, networks):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            region = regions.findDN(s['ca'] + '/' + s['rg'])
            if region:
                s['payload']['regionId'] = region['id']
                fabricNetworkIds = []
                for net_dn in s['net_dns']:
                    network = networks.findDN(net_dn)
                    if network:
                        fabricNetworkIds.append(network['id'])
                    else:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not find network of network profile [%s]' % dn)
                s['payload']['fabricNetworkIds'] = fabricNetworkIds
                if s['dom_dn']: s['payload']['isolationNetworkDomainId'] = domains.findDN(s['dom_dn'])['id']
                if s['exn_dn']: s['payload']['isolationExternalFabricNetworkId'] = networks.findDN(s['exn_dn'])['id']
                t = self.findDN(dn)
                if t == None: # Create
                    try: vra.post('/iaas/api/network-profiles', s['payload'])
                    except Exception as e:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not create network profile [%s]' % dn)
                    else:
                        print(' +', end=''); sys.stdout.flush()
                        if isDebug(): print(' create network profile [%s]' % dn)
                        completed += 1
                else: # Update
                    try: vra.patch('/iaas/api/network-profiles/' + t['id'], s['payload'])
                    except:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not update network profile [%s]' % dn)
                    else:
                        print(' *', end=''); sys.stdout.flush()
                        if isDebug(): print(' update network profile [%s]' % dn)
                        completed += 1
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find region of network profile [%s]' % dn)
        print('')
        return completed


@register_object
class FabricDatastore(Object): # storage-descriptions
    
    RELATIONS = [CloudRegion]
    LOAD_URL = '/iaas/api/fabric-vsphere-datastores?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, regions):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['name']
            region = regions.findID(d['_links']['region']['href'].split('regions/')[1])
            ca = region['ca']
            rg = region['name']
            dn = ca + '/' + rg + '/' + name
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'rg': rg, 'dn': dn
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count


@register_object
class StorageProfilevSphere(Object):
    
    RELATIONS = [CloudRegion]
    LOAD_URL = '/iaas/api/storage-profiles-vsphere?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, regions):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['name']
            region = regions.findID(d['_links']['region']['href'].split('regions/')[1])
            ca = region['ca']
            rg = region['name']
            dn = ca + '/' + rg + '/' + name
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'rg': rg, 'dn': dn,
                'tags': d['tags'] if 'tags' in d else []
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count


@register_object
class StorageProfile(Object):
    
    RELATIONS = [CloudAccount, CloudRegion, StorageProfilevSphere, FabricDatastore]
    LOAD_URL = '/provisioning/mgmt/storage-profile?expand&$top=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, accounts, regions, vsprofs, datastores):
        map, ids, dns, count = {}, [], {}, 0
        for sp in data['documents'].values():
            region = regions.findID(sp['endpointLinks'][0].split('endpoints/')[1])
            ca = region['ca']
            rg = region['name']
            rg_dn = ca + '/' + rg
            for d in sp['storageItems']:
                if 'storageDescriptionLink' not in d: continue
                id = d['id']
                name = d['name']
                dn = ca + '/' + rg + '/' + name
                # Payload ##############################
                tags = vsprofs.findDN(dn)['tags']
                stg_dn = datastores.findID(d['storageDescriptionLink'].split('storage-descriptions/')[1])['dn']
                payload = {'name': name, 'cloudAccountType': 'vsphere'}
                if 'description' in d: payload['desc'] = d['description']
                if 'defaultItem' in d: payload['defaultItem'] = d['defaultItem']
                if 'supportsEncryption' in d: payload['supportsEncryption'] = d['supportsEncryption']
                if 'diskProperties' in d: payload['customProperties'] = d['diskProperties']
                # Payload ##############################
                map[id] = {
                    'id': id, 'name': name, 'ca': ca, 'rg': rg, 'dn': dn,
                    'rg_dn': rg_dn,
                    'stg_dn': stg_dn,
                    'tags': tags,
                    'payload': payload
                }
                ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count
    
    def sync(self, vra, src, accounts, regions, vsprofs, datastores):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            region = regions.findDN(s['rg_dn'])
            if region:
                if self.ver in [80, 81]: s['payload']['provisioningRegionLink'] = '/provisioning/resuorces/provisioning-regions/' + region['id']
                else: s['payload']['provisioningRegionLink'] = '/provisioning/resources/' + region['id']
                s['payload']['provisioningRegionLink'] = '/provisioning/resources/' + region['id']
                s['payload']['storageDescriptionLink'] = '/resources/storage-descriptions/' + datastores.findDN(s['stg_dn'])['id']
                if s['tags']:
                    r = vra.post('/provisioning/uerp/provisioning/mgmt/tag-assignment', {'tagsToAssign': s['tags']})
                    s['payload']['tagLinks'] = r['tagLinks'] if 'tagLinks' in r else []
                t = self.findDN(dn)
                if t == None: # Create
                    try: vra.post('/provisioning/uerp/provisioning/mgmt/flat-storage-profile', s['payload'])
                    except Exception as e:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not create storage profile [%s]' % dn)
                    else:
                        print(' +', end=''); sys.stdout.flush()
                        if isDebug(): print(' create storage profile [%s]' % dn)
                        completed += 1
                else: # Update
                    try: vra.put('/provisioning/uerp/provisioning/mgmt/flat-storage-profile/' + t['id'], s['payload'])
                    except:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not update storage profile [%s]' % dn)
                    else:
                        print(' *', end=''); sys.stdout.flush()
                        if isDebug(): print(' update storage profile [%s]' % dn)
                        completed += 1
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find region of storage profile [%s]' % dn)
        print('')
        return completed


@register_object
class FlavorProfile(Object):
    
    RELATIONS = [CloudRegion]
    LOAD_URL = '/iaas/api/flavor-profiles?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, regions):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['name']
            region = regions.findID(d['_links']['region']['href'].split('regions/')[1])
            ca = region['ca']
            rg = region['name']
            dn = ca + '/' + rg
            # Payload ##############################
            flavor_mapping = d['flavorMappings']['mapping'] if 'flavorMappings' in d and 'mapping' in d['flavorMappings'] else {}
            payload = {'name': dn, 'flavorMapping': flavor_mapping}
            if 'description' in d: payload['description'] = d['description']
            # Payload ##############################
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'rg': rg, 'dn': dn,
                'payload': payload
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count

    def sync(self, vra, src, regions):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            region = regions.findDN(s['dn'])
            if region:
                s['payload']['regionId'] = region['id']
                t = self.findDN(dn)
                if t == None: # Create
                    try: vra.post('/iaas/api/flavor-profiles', s['payload'])
                    except Exception as e:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not create flavor profile [%s]' % dn)
                    else:
                        print(' +', end=''); sys.stdout.flush()
                        if isDebug(): print(' create flavor profile [%s]' % dn)
                        completed += 1
                else: # Update
                    try: vra.patch('/iaas/api/flavor-profiles/' + t['id'], s['payload'])
                    except:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not update flavor profile [%s]' % dn)
                    else:
                        print(' *', end=''); sys.stdout.flush()
                        if isDebug(): print(' update flavor profile [%s]' % dn)
                        completed += 1
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find region of flavor profile [%s]' % dn)
        print('')
        return completed
    

@register_object
class FabricImage(Object):
    
    RELATIONS = [CloudAccount]
    LOAD_URL = '/provisioning/uerp/provisioning/mgmt/image?expand&$top=10000&$filter=(endpointType ne \'aws\')'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, accounts):
        map, ids, dns, count = {}, [], {}, 0
        for id, d in data['documents'].items():
            id = id.split('images/')[1]
            name = d['name']
            ca = accounts.findID(d['endpointLink'].split('endpoints/')[1])
            rg = d['regionId']
            dn = ca + '/' + rg + '/' + name
            mo = d['customProperties']['__moref']
            map[id] = {
                'id': id, 'name': name, 'ca': ca, 'rg': rg, 'dn': dn, 'mo': mo
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count


@register_object
class ImageProfile(Object):
    
    RELATIONS = [CloudRegion, FabricImage]
    LOAD_URL = '/profisioning/uerp/provisioning/mgmt/image-names?view=list'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, regions, images):
        map, ids, dns, count = {}, [], {}, 0
        if self.ver in [80, 81]: self.delimeter = 'provisioning-regions/'
        else: self.delimeter = 'resources/'
        if self.role == 'tgt':
            imgprofs = self.get('/iaas/api/image-profiles?limit=10000')['content']
        for d in data:
            for id, mig in d['imageMapping'].items():
                region_id = id.split(self.delimeter)[1]
                img_id = img['imageLink'].split('images/')[1]
                image = images.findID(img_id)
                if self.role == 'tgt':
                    for imgprof in imgprofs:
                        if imgprof['_links']['region']['href'].split('regions/')[1] == region_id:
                            id = imgprof['id']
                            break
                    else: id = region_id
                if image:
                    if id in map:
                        mappings = map['id']['mappings']
                        mappings[d['name']] = image['dn']
                    else:
                        region = regions.findID(region_id)
                        dn = region['dn']
                        mappings = {}
                        mappings[d['name']] = image['dn']
                        map[id] = {
                            'id': id,
                            'name': region['name'],
                            'ca': region['ca'],
                            'rg': region['name'],
                            'dn': dn,
                            'mappings': mappings,
                            'payload': {'name': dn}
                        }
                        ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count
    
    def sync(self, vra, src, regions, images):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            region = regions.findDN(s['dn'])
            if region:
                s['payload']['regionId'] = region['id']
                mappings = {}
                for key, img_dn in s['mappings'].items():
                    image = images.findDN(img_dn)
                    mappings[key] = {'id': image['id'], 'name': image['name']}
                s['payload']['imageMapping'] = mappings
                t = self.findDN(dn)
                if t == None: # Create
                    try: vra.post('/iaas/api/image-profiles', s['payload'])
                    except Exception as e:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not create image profile [%s]' % dn)
                    else:
                        print(' +', end=''); sys.stdout.flush()
                        if isDebug(): print(' create image profile [%s]' % dn)
                        completed += 1
                else: # Update
                    try: vra.patch('/iaas/api/image-profiles/' + t['id'], s['payload'])
                    except:
                        print(' !', end=''); sys.stdout.flush()
                        if isDebug(): print(' could not update image profile [%s]' % dn)
                    else:
                        print(' *', end=''); sys.stdout.flush()
                        if isDebug(): print(' update image profile [%s]' % dn)
                        completed += 1
            else:
                print(' !', end=''); sys.stdout.flush()
                if isDebug(): print(' could not find region of image profile [%s]' % dn)
        print('')
        return completed
    
    
@register_object
class Project(Object):
    
    RELATIONS = [CloudZone]
    LOAD_URL = '/iaas/api/projects?$limit=10000'
    
    def __init__(self): Object.__init__(self)
    
    def parse(self, data, zones):
        map, ids, dns, count = {}, [], {}, 0
        for d in data['content']:
            id = d['id']
            name = d['name']
            dn = name
            # Payload ##############################
            for z in d['zones']: z['zoneId'] = zones.findID(z['zoneId'])['dn']
            payload = {'name': name}
            if 'description' in d: payload['description'] = d['description']
            if 'administrators' in d: payload['administrators'] = d['administrators']
            if 'members' in d: payload['members'] = d['members']
            if 'viewers' in d: payload['viewers'] = d['viewers']
            if 'machineNamingTemplate' in d: payload['machineNamingTemplate'] = d['machineNamingTemplate']
            if 'sharedResources' in d: payload['sharedResources'] = d['sharedResources']
            if 'operationTimeout' in d: payload['operationTimeout'] = d['operationTimeout']
            if 'constraints' in d: payload['constraints'] = d['constraints']
            if 'zones' in d: payload['zoneAssignmentConfigurations'] = d['zones']
            # Payload ##############################
            map[id] = {
                'id': id, 'name': name, 'dn': dn,
                'payload': payload
            }
            ids.append(id); dns[dn] = id; count += 1
        return map, ids, dns, count
    
    def sync(self, vra, src, zones):
        completed = 0
        for s in src.getSortedMaps():
            dn = s['dn']
            del_zones = []
            for z in s['payload']['zoneAssignmentConfigurations']:
                try: z['zoneId'] = zones.findDN(z['zoneId'])['id']
                except: del_zones.append(z)
            for del_zone in del_zones:
              s['payload']['zoneAssignmentConfigurations'].remove(z)
            t = self.findDN(dn)
            if t == None: # Create
                try: vra.post('/iaas/api/projects', s['payload'])
                except Exception as e:
                    print(' !', end=''); sys.stdout.flush()
                    if isDebug(): print(' could not create project [%s]' % dn)
                else:
                    print(' +', end=''); sys.stdout.flush()
                    if isDebug(): print(' create project [%s]' % dn)
                    completed += 1
            else: # Update
                try: vra.patch('/iaas/api/projects/' + t['id'], s['payload'])
                except:
                    print(' !', end=''); sys.stdout.flush()
                    if isDebug(): print(' could not update project [%s]' % dn)
                else:
                    print(' *', end=''); sys.stdout.flush()
                    if isDebug(): print(' update project [%s]' % dn)
                    completed += 1
        print('')
        return completed


