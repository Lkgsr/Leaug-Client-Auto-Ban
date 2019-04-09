import os
path_to_lol = 'C:\Riot Games\League of Legends'


def get_credentials(path_to_lock_file=path_to_lol):
    for entry in os.listdir(path_to_lol):
        if entry == 'lockfile':
            with open(path_to_lol+f'\{entry}', 'r') as lockfile:
                args = lockfile.readline().split(':')
                credentials = {'process': args[0], 'pid': args[1], 'port': args[2], 'password': args[3],
                               'protocol': args[4]}
            return credentials
    print('Start The Client Pleas')
    exit()
