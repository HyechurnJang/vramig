
import argparse
from .common import VRA, jps, jpp, REGISTERED_OBJECTS
from .iaas import *

def execute(args):
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-o', '--objects', nargs='+', help='Working Objects')
    parser.add_argument('-a', '--all-objects', nargs='?', const=True, default=False, help='Working with All Objects')
    parser.add_argument('-v', '--vra', required=True, help='vRealize Automation Hostname')
    parser.add_argument('-u', '--username', required=True, help='vRealize Automation Username')
    parser.add_argument('-p', '--password', required=True, help='vRealize Automation Password')
    parser.add_argument('-t', '--task', nargs='?', const=True, default=False, help='Common Task')
    parser.add_argument('-d', '--debug', nargs='?', const=True, default=False, help='Debug Mode')
    parser.add_argument('command', help='dump or sync')
    
    if args[0] == 'vramig': args = args[1:]
    if args == ['list']:
        for cls_name in REGISTERED_OBJECTS.keys(): print(cls_name)
        exit(0)
    args = parser.parse_args(args)
    
    if args.all_objects == False and args.task == False and args.objects == None:
        print('need one more objects')
        exit(1)
    
    if args.command not in ['dump', 'sync']:
        print('command must be "dump" or "sync"')
        exit(1)
    
    if args.all_objects:
        objs = REGISTERED_OBJECTS.values()
    elif args.task:
        objs = ['FabricCompute', 'CloudZone', 'FabricNetwork', 'FabricNetworkvSphere', 'IPRange']
    else:
        objs = args.objects
    
    vra = VRA(args.vra, args.username, args.password, args.debug)
    
    if args.command == 'dump':
        for obj in objs:
            cls = REGISTERED_OBJECTS[obj]
            print('%-24s' % cls_name, end='')
            cls(vra).dump()
            print(' --> [ DUMP ]')
    elif args.command == 'sync':
        for obj in objs:
            cls = REGISTERED_OBJECTS[obj]
            print('┌  {} Start Sync ─────────────────────┐'.format(obj))
            cls(vra).sync()
            print('└  {} Sync Successful ────────────────┘\n'.format(obj))
    
    print('Finished')
