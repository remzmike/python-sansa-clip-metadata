# eg. D:\Code.Github\python-sansa-clip-metadata>c:\python\python massparse.py C:\sansa.clipplus\
from __future__ import division

import os, sys

import sansa
from sansa import mkascii

def go(dpath):
    songs = {}
    for root, dirs, files in os.walk(dpath):
        for fn in files:
            if 'MTABLE.SYS' in fn:
                fpath = os.path.join(root, fn)
                items = sansa.get_rated_songs(fpath)
                for item in items:
                    if item.rating > 3:
                        key = '{artist}\\{album}\\{title}'.format(**item.__dict__)
                        songs.setdefault(key, [])
                        songs[key].append(item.rating)
    return songs

if __name__=='__main__':
    dpath = sys.argv[1]

    songs = go(dpath)

    f = file('_output_.txt', 'wb')
    for key, ratings in songs.items():
        f.write(key)
        avg = sum(ratings)/len(ratings)
        f.write('{} {{{}}}\n'.format(key, avg))
    f.close()