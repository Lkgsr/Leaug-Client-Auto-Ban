import asyncio
import functools
import sys

from Client import Client
from readlockfile import get_credentials


def schedule(func, args=None, kwargs=None, interval=60, *, loop):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    async def periodic_func():
        while True:
            await func(*args, **kwargs)
            await asyncio.sleep(interval, loop=loop)

    return loop.create_task(periodic_func())


if __name__ == '__main__':
    cred = get_credentials()
    create_scheduler = lambda loop: functools.partial(schedule, loop=loop)
    _id = None
    if sys.argv[1]:
        try:
            _id = int(sys.argv[1])
        except Exception as e:
            print(str(e))
        if type(_id) is int:
            loop = asyncio.new_event_loop()
            cred['loop'] = loop
            cred['champion_id'] = sys.argv[1]
            client = Client(**cred)
            schedule = create_scheduler(loop=loop)
            refresh_task = schedule(client, interval=3)
            loop.run_forever()
    print('no or wrong championId')
    exit()





