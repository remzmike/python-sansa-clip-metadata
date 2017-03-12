# eg. D:\Code.Github\python-sansa-clip-metadata>c:\python\python massparse.py C:\sansa.clipplus\
from __future__ import division

import os, sys, codecs

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
            #break # for debug
    return songs

if __name__=='__main__':
    dpath = sys.argv[1]

    songs = go(dpath)

    # love this unicode stuff, too much fun, no problems, would unicode again 10/10
    #f = codecs.open('_output_.txt', 'wb', 'utf-8-sig')
    f = open('_output_.txt', 'wb')
    for key, ratings in songs.items():
        avg = sum(ratings)/len(ratings)
        line = '{} {{{}}}\n'.format(key, avg)
        #f.write(line.encode('utf8'))
        f.write(line)
    f.close()