
import json
import argparse
from .common import VRA, jps, jpp, REGISTERED_OBJECTS
from .iaas import *

def execute(args, conf):
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-o', '--objects', nargs='+', help='Working Objects')
    parser.add_argument('-p', '--process', nargs='?', const=True, default=False, help='Common Process')
    parser.add_argument('-a', '--all-objects', nargs='?', const=True, default=False, help='Working with All Objects')
    parser.add_argument('-d', '--debug', nargs='?', const=True, default=False, help='Debug Mode')
    parser.add_argument('-u', '--url', help='src or tgt dump url')
    parser.add_argument('command', help='list, src, tgt, dump, sync')
    
    if args[0] == 'vramig': args = args[1:]
    args = parser.parse_args(args)
    
    if args.command not in ['list', 'src', 'tgt', 'dump', 'sync']:
        print('command must be "list", "src", "tgt", "dump", "sync"')
        exit(1)
    
    if args.command == 'list':
        for obj in REGISTERED_OBJECTS.keys(): print(obj)
        exit(0)
    elif args.command == 'src':
        with open('data.src.json', 'w') as fd: fd.write(json.dumps(VRA(conf, 'src').get(args.url), indent=2))
        exit(0)
    elif args.command == 'tgt':
        with open('data.tgt.json', 'w') as fd: fd.write(json.dumps(VRA(conf, 'tgt').get(args.url), indent=2))
        exit(0)
    
    if args.all_objects == False and args.process == False and args.objects == None:
        print('need object kind option')
        exit(1)
    elif args.all_objects:
        objs = REGISTERED_OBJECTS.keys()
    elif args.process:
        objs = ['CloudAccount', 'FabricCompute', 'CloudZone', 'FabricNetwork', 'FabricNetworkvSphere', 'IPRange']
    else:
        objs = args.objects
    
    if args.command == 'dump':
        src_vra = VRA(conf, 'src')
        tgt_vra = VRA(conf, 'tgt')
        for obj in objs:
            print('┌  {} Dump Start ─────────────────────┐'.format(obj))
            REGISTERED_OBJECTS[obj](src_vra, tgt_vra).dump()
            print('└  {} Sync Finish ────────────────────┘\n'.format(obj))
    elif args.command == 'sync':
        tgt_vra = VRA(conf, 'tgt')
        for obj in objs:
            print('┌  {} Sync Start ─────────────────────┐'.format(obj))
            REGISTERED_OBJECTS[obj](None, tgt_vra).sync()
            print('└  {} Sync Finish ────────────────────┘\n'.format(obj))
    
    print('All Finished')
