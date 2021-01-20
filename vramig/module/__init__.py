
import json
import argparse
from .common import VRA, jps, jpp, REGISTERED_OBJECTS, setDebugMode
from .iaas import *

def execute(args, conf):
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-o', '--objects', nargs='+', help='Working Objects')
    parser.add_argument('-a', '--all-objects', nargs='?', const=True, default=False, help='Working with All Objects')
    parser.add_argument('-d', '--debug', nargs='?', const=True, default=False, help='Debug Mode')
    parser.add_argument('-u', '--url', help='src or tgt dump url')
    parser.add_argument('command', help='list, get, dump, sync')
    
    if args[0] == 'vramig': args = args[1:]
    args = parser.parse_args(args)
    
    if args.debug: setDebugMode()

    if args.command not in ['list', 'get', 'dump', 'sync']:
        print('command must be "list", "get", "dump", "sync"')
        exit(1)
    
    if args.command == 'list':
        for obj in REGISTERED_OBJECTS.keys(): print(obj)
        exit(0)
    elif args.command == 'get':
        with open('data.src.json', 'w') as fd: fd.write(jps(VRA(conf, 'src').get(args.url)))
        exit(0)
    
    if args.all_objects == False and args.objects == None:
        print('need object kind option')
        exit(1)
    elif args.all_objects:
        objs = REGISTERED_OBJECTS.keys()
    else:
        objs = args.objects
    
    if args.command == 'dump':
        for obj in objs:
            object = REGISTERED_OBJECTS[obj]
            print('┌  Dump : %-24s ─────────────────────────────┐' % obj)
            object().loadData(VRA(conf, 'src'))
            object().loadData(VRA(conf, 'tgt'))
            print('└  Dump : %-24s ─────────────────────────────┘\n' % obj)
    elif args.command == 'sync':
        for obj in objs:
            object = REGISTERED_OBJECTS[obj]
            tgt_vra = VRA(conf, 'tgt')
            print('┌  Sync : %-24s ─────────────────────────────┐' % obj)
            src = object().loadData(VRA(conf, 'src'))
            object().loadData(tgt_vra).syncData(tgt_vra, src)
            print('└  Sync : %-24s ─────────────────────────────┘\n' % obj)
    
    print('All Finished')
