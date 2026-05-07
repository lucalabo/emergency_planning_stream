import pickle
import time
import sys
from functools import cache

from cache import Cache
from clingohelper import ClingoHelper

if __name__ == '__main__':
    if len(sys.argv) < 2:
        try:
            import os
            cache = pickle.load(
                open('cache.pkl',
                    'rb'))
            print(f'interceptions {cache.interceptions}')
            print(f'low_prio_violation {cache.low_prio_violation}')
            print(f'high_prio_violation {cache.high_prio_violation}')
            print(f'packages_received {cache.time}')
            exit(0)
        except EOFError:
            cache = Cache()
    package = sys.argv[1]
    cache_size = 18
    low_prio = [0,2]
    high_prio = [3]
    prefixes = ['/localhost', '/movie', '/news', '/gov']
    low_prio_age = 10
    high_prio_age = 20
    horizon = 3

    # read cache
    try:
        cache = pickle.load(
            open(
                'src/ndnSIM/NFD'
                '/daemon/table/framework/cache.pkl',
                'rb'))
    except EOFError:
        cache = Cache()
    #todo this shouldn't be new every step
    clingo = ClingoHelper(cache_size, horizon, low_prio_age, high_prio_age, prefixes, low_prio, high_prio)
    # add package to cache

    package_removed = ""
    if package in cache.packages:
        index = cache.packages.index(package)
        cache.last_used[index] = cache.time
    else:
        if len(cache.packages) < cache_size:
            cache.packages.append(package)
            cache.last_used.append(cache.time)
            cache.added.append(cache.time)
        elif len(cache.packages) == cache_size:

            for i, c in enumerate(cache.packages):
                for l in low_prio:
                    if c.startswith(prefixes[l]):
                        age = cache.time - cache.added[i]
                        if age > low_prio_age:
                            cache.low_prio_violation += 1

            action = clingo.get_action(cache, package)

            action_compare = cache.last_used.index(min(list(cache.last_used)))

            # uncomment next line to default to LRU w/o framework
            #action = action_compare

            for h in high_prio:
                if cache.packages[action].startswith(prefixes[h]):
                    age = cache.time - cache.added[action]
                    if age < high_prio_age:
                        cache.high_prio_violation += 1

            if action != action_compare:
                cache.interceptions += 1
                pass

            if action < cache_size:
                package_removed = str(cache.packages[action])
                cache.packages[action] = package
                cache.last_used[action] = cache.time
                cache.added[action] = cache.time

    # save cache for next iteration
    cache.time += 1

    pickle.dump(cache,
                open(
                    'src/ndnSIM'
                    '/NFD/daemon/table/framework/cache.pkl',
                    'wb'))

    f = open(
        "src/ndnSIM/NFD/daemon"
        "/table/framework/cache.txt",
        "w")
    f.write(package_removed)
    f.close()
