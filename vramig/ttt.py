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

import json
from module.common import VRASession, jpp, setDebugMode
setDebugMode()
vra = VRASession('vra.vmkloud.com', 'jangh', 'David*#8090')

target = 'test1'

resources = vra.get("/provisioning/uerp/resources/compute?expand&$filter=((type eq 'VM_GUEST') and (name eq '%s') and (lifecycleState eq 'READY'))" % target)
jpp(resources['documentLinks'])
resourceLink = resources['documentLinks'][0]
resource = resources['documents'][resourceLink]
resourceName = resource['name']
jpp(resource)


name = 'ob-%s' % target
description = 'onboard test %s' % target

# Cloud Account
endpointIds = ['8967fe8c-e6e6-46b9-a3b5-d4ab9d4a053e']
# /iaas/api/cloud-account
# d['id']

# Project
projectId = '85a2bc48-f42f-4e38-b160-994f8a5f2127'
templateLink = '/blueprint/api/blueprints/b78e547c-1efc-44bd-b0f9-0f5e2a40afa5'
# /blueprint/api/blueprints
# d['selfLink']

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
rsc_payload = {
    'planLink': planLink,
    'deploymentLink': depLink,
    'resourceLink': resourceLink,
    'resourceName': resourceName,
    'ruleLinks': []
}
rsc = vra.post('/relocation/onboarding/resource', rsc_payload)
 
# Create Blueprint
bp_payload = {
    'name': name,
    'planLink': planLink,
    'deploymentLink': depLink,
    'templateLink': templateLink,
    'autoGenerate': False
}
bp = vra.post('/relocation/onboarding/blueprint', bp_payload)























