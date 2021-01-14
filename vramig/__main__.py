# -*- coding: utf-8 -*-
'''
  ____  ___   ____________  ___  ___  ____     _________________
 / __ \/ _ | / __/  _/ __/ / _ \/ _ \/ __ \__ / / __/ ___/_  __/
/ /_/ / __ |_\ \_/ /_\ \  / ___/ , _/ /_/ / // / _// /__  / /   
\____/_/ |_/___/___/___/ /_/  /_/|_|\____/\___/___/\___/ /_/    
         Operational Aid Source for Infra-Structure 

Created on 2021. 1. 11..
@author: Hye-Churn Jang, CMBU Specialist in Korea, VMware [jangh@vmware.com]
'''

import sys
import module
from config import SRC_VRA_HOSTNAME, SRC_VRA_USERNAME, SRC_VRA_PASSWORD, SRC_VRA_VERSION, TGT_VRA_HOSTNAME, TGT_VRA_USERNAME, TGT_VRA_PASSWORD, TGT_VRA_VERSION

module.execute(sys.argv, {
    'src': {
        'hostname': SRC_VRA_HOSTNAME,
        'username': SRC_VRA_USERNAME,
        'password': SRC_VRA_PASSWORD,
        'version': SRC_VRA_VERSION
    },
    'tgt': {
        'hostname': TGT_VRA_HOSTNAME,
        'username': TGT_VRA_USERNAME,
        'password': TGT_VRA_PASSWORD,
        'version': TGT_VRA_VERSION
    }
})