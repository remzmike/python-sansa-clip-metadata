enable_debug = False
def debug(*args):
    if enable_debug:
        print '-'.join(map(str,args))

class Item:
    def __init__(o):
        o.a = None
        o.b = None
        #wav devices - a2 b5
        #m3u - a4 b2
        #jpg - a2 b7
        #mp3 - a1 b1, a2 b1
        #ogg - a2 b1
        o.pathname = None
        o.filename = None
        o.title = None
        o.artist = None
        o.album = None
        o.f1 = None
        o.f2 = None
        o.extra = None # this is a year string for my ogg files, not sure what it is yet, replaces f1 and f2
        o.genre = None
        o.end = None # trailing 7 or 13 bytes
        # metas
        o.rating = None # known meta a
        o.metab = None
        o.metac = None
    def __str__(o):
        l = []
        l.append('{0}\{1}'.format(o.pathname, o.filename))
        l.append('{0} - {1} - {2}'.format(o.artist, o.album, o.title))
        l.append('a:{0}, b:{1}'.format(o.a, o.b))
        return ' | '.join(l)
    def uses_unicode(o):
        return o.a == 2

class SansaData:

    def __init__(o, data, resdata, mode):
        o.i = 0
        o.data = data
        o.resdata = resdata
        o.bytes = data
        o.items = []
        o.items_pending_delete = []
        o.items_invalid_b = []

    def goto_items(o):
        if mode=='clip':
            o.i = 0x27
        elif mode=='clipplus':
            o.i = 0x23
        elif mode=='clipzip':
            o.i = 0x2f

    def goto_metas(o):
        if mode=='clip':
            o.i = 0x148238
        elif mode in ['clipplus','clipzip']:
            # separate file now
            o.bytes = resdata
            o.i = 0x77d                 

    def read_all(o):
        o.read_items()
        o.read_metas()

    def read(o, count):
        result = o.bytes[o.i : o.i + count]
        o.i += count
        return result

    # read until first byte in chunk is null
    def read_to_null(o, chunksize=1, includedelim=False):
        result = ''
        while True:
            chunk = o.read(chunksize)
            if ord(chunk[0]) == 0:
                o.i -= chunksize
                o.i += 1
                break
            result += chunk
        if includedelim:
            result += '\x00'
        return result

    # Both unicode and ascii strings are written in character pairs and double null terminated.
    # The last character of ascii strings with uneven length is paired with a null byte.
    # This means ascii strings of uneven length will have three nulls after their last character.
    def read_string(o):
        s = o.read_to_null(2)
        last = o.read(1)
        assert last == '\x00'
        return s

    # returns Item
    def read_item(o):
        
        a = ord(o.read(1))
        debug('a', a) # appears to tell if item data is going to use unicode (2) or not (1)
        if a==0: # also changes to 0 when a track is pending delete
            debug('this track marked for deletion')
        
        b = ord(o.read(1)) # item type
        debug('b', b)
        
        if mode in ['clip','clipplus']:
            o.read(15)
        else:
            o.read(7)

        pathname = o.read_string()
        debug('pathname', pathname)

        marker = 'mmc:0:'
        if not pathname.startswith(marker):
            raise Exception('expected marker prefix "{0}", got "{1}", @ {2}'.format(marker, pathname, hex(o.i)))
        
        filename = o.read_string()
        debug('filename', filename)
        
        title = o.read_string()
        debug( 'title', title)
        
        artist = o.read_string()
        debug('artist', artist)
        
        album = o.read_string()
        debug('album', album)

        f1 = o.read(1)
        debug('f1', ord(f1))
        
        f2 = o.read(1)
        debug('f2', ord(f2))
        
        # this appears in my ogg files
        extra = None
        if not (ord(f1)==255 and ord(f2)==255):
            o.i -= 2
        extra = o.read_string()
        if len(extra)>0:
            debug('*extra', extra)
        
        genre = o.read_string()
        debug('genre', genre)
        
        end1 = o.read(2)
        if end1[1] == '\x00': # hax
            end2 = o.read(5)
        else:
            end2 = o.read(11)
        end = end1 + end2
        debug('end', repr(end))
        debug('- - -')

        item = Item()
        item.a = a
        item.b = b
        item.pathname = pathname
        item.filename = filename
        item.title = title
        item.artist = artist
        item.album = album
        item.f1 = f1
        item.f2 = f2
        item.extra = extra
        item.genre = genre
        item.end = end
        return item

    def read_items(o):

        o.goto_items()

        while True:
            if o.read(2) == '\x00\x00':
                break
            else:
                o.i -= 2
            item = o.read_item()
            if item.a==0:
                #print 'skipping file marked for deletion:', item.filename
                o.items_pending_delete.append(item)
            elif item.b not in [1,11]: # allow 11, audiobooks/podcast/etc, clip zip
                #print 'skipping invalid b:', item.filename, item.b
                o.items_invalid_b.append(item)
            else:
                o.items.append(item)

    def read_metas(o):

        o.goto_metas()

        metas = []
        buf = o
        metacount = 0
        #print '***', len(o.items)
        # each record is 0x80 + 3 bytes, first byte is star rating
        while True:
            four = o.read(4)
            if four[0]!='\x80':
                break
            try:
                item = o.items[metacount]
            except IndexError:
                print 'indexerror', metacount # eg. skipping items i shouldn't
            item.rating = ord(four[1])
            item.metab = four[2]
            item.metac = four[3]

            #if four[1]!='\x00':
                #print 'rating detected on meta #', metacount, ' value of', ord(four[1])
                #print ' ', item.artist, '-', item.album, '-', item.filename

            # wondering what the other meta bytes are, maybe nothing
            if four[2]!='\x00':
                print 'unusual four[2] meta detected on #', metacount, ' value of', repr(four[2])
                print ' ', item.artist, '-', item.album, '-', item.filename
            if four[3]!='\x00':
                print 'unusual four[3] meta detected on #', metacount, ' value of', repr(four[3])
                print ' ', item.artist, '-', item.album, '-', item.filename
            metacount += 1

if __name__ == '__main__':
    
    # future: unicode hammer, latscii, custom    
    import sys        
    
    # make ascii from double byte string
    def mkascii(bs):
        u = bs.decode('utf16')
        a = u.encode('ascii', 'replace')
        #a = u.encode('ascii', 'xmlcharrefreplace')
        #a = u.encode('ascii', 'backslashreplace')
        return a

    # do nothing to byte string
    def nothing(bs):
        return bs

    test = True
    if test:
        buf = SansaData('abc\x00def\x00ghi\x00\x00jkl\x00\x00\x00',None,None)
        assert buf.read(2) == 'ab'
        assert buf.read_to_null() == 'c'
        assert buf.read_to_null() == 'def'
        assert buf.read_to_null(2) == 'ghi\x00'
        assert buf.read_to_null() == 'jkl'
        assert buf.read_to_null() == ''
        assert buf.read_to_null(50) == ''

    if len(sys.argv)==1:
        print 'first param should be path to an mtable.sys file'
        sys.exit(1)
    fn = sys.argv[1] 
        
    modes = ['clip','clipplus','clipzip']
    
    if '\\sansa.clip\\' in fn:
        mode = modes[0]
    elif '\\sansa.clipplus\\' in fn:
        mode = modes[1]
    elif '\\sansa.clipzip\\' in fn:
        mode = modes[2]
    else:
        if len(sys.argv)<3:
            print 'second param should be mode string', modes
            sys.exit(2)
        mode = sys.argv[2]
    print 'mode:', mode
    assert mode in modes
      
    #fn = '7/MTABLE.SYS' # has a pending delete
    #fn = '8/MTABLE.SYS'
    #fn = '9/MTABLE.SYS' # unicode on track 640 title
    #fn = '10/MTABLE.SYS' # looks like golist is stored in unparsed section

    resfn = fn.replace('MTABLE', 'RES_INFO')
    resdata = None
    if fn.lower().endswith('.gz'):
        import gzip
        data = gzip.open(fn,'rb').read()        
        if mode != 'clip':
            resdata = gzip.open(resfn,'rb').read()
    else:
        data = file(fn,'rb').read()
        if mode != 'clip':            
            resdata = file(resfn,'rb').read()
    mt = SansaData(data, resdata, mode)
    mt.read_all()

    if True:
        for item in mt.items:
            if item.rating > 0:
                if item.uses_unicode():
                    fn = mkascii
                else:
                    fn = nothing
                print item.rating, '-', fn(item.artist), '-', fn(item.album), '-', fn(item.title), '-', item.filename
    
    # track 640 in data 9 contains unicode filename, treekeeper
    if False:
        if fn == '9/MTABLE.SYS':
            item = mt.items[640]
            print item.title

    if False:
        print '-----------'
        print 'total items', len(mt.items)