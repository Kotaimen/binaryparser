""" iTunsDB - iTunes Music Library
See http://www.ipodlinux.org/wiki/ITunesDB_

"""

import io
import sys, os, os.path
sys.path.insert(0, '../src')
from binaryparser import *

def _struct_size_check(context):
    if context.__EndOfData - context.__StartOfData == context.TotalLength:
        return True
    else:
        print (context.TotalLength, context.__EndOfData - context.__StartOfData)
        return False


# Data Object ------------------------------------------------------------------

MHOD = Structure('DatabaseObject',
    Anchor('__StartOfData'),

    Dump(Constant(String('HeaderIdentifier', 4), 'mhod')),
    ULInt32('HeaderLength'),
    ULInt32('TotalLength'),
    Embed(Union('Type',
        Enum(ULInt32('Type'),
             TITLE=1,
             LOCATION=2,
             ALBUM=3,
             ARTIST=4,
             GENRE=5,
             FILETYPE=6,
             EQ_SETTING=7,
             COMMENT=8,
             PODCAST_CATEGORY=9,
             COMPOSER=12,
             GROUPING=13,
             DESCRIPTION_TEXT=14,
             TITLE_FOR_SORTING=17,
             ALBUM_FOR_SORTING=28,
             ALBUM_ARTIST_FOR_SORTING=29,
             COMPOSER_FOR_SORTING=30,
             _default='UNKNOWN'
             ),
        ULInt32('IntType'),
        )),
    Padding(4),
    Padding(4),
    Anchor('__StartOfPadding'),

    IfElse(lambda c: c.Type != 'UNKNOWN',
        Embed(Structure('StringObject',
            ULInt32('Position'),
            ULInt32('Length'),
            Padding(4),
            Padding(4),
            String('String', lambda c: c.Length, encoding='utf_16_le'),
            )),
        Bytes('Data', lambda c: c.TotalLength - (c.__StartOfPadding - c.__StartOfData)
              ),
    ),
    Anchor('__EndOfData'),
    Assertion(_struct_size_check, 'data size mismatch'),
    )

# TrackItem --------------------------------------------------------------------

MHIT = Structure('TrackItem',
    Anchor('__StartOfData'),

    Dump(Constant(String('HeaderIdentifier', 4), 'mhit')),
    ULInt32('HeaderLength'),
    ULInt32('TotalLength'),

    ULInt32('NumberOfStrings'),
    ULInt32('UniqueID'),
    Boolean(ULInt32('Visible')),
    String('FileType', 4),
    UInt8('Type1'),
    UInt8('Type2'),
    Boolean(UInt8('Compilation')),
    Boolean(UInt8('Rating')),
    ULInt32('LastModifiedTime'),
    ULInt32('TrackSize'),
    ULInt32('TrackLength'),
    ULInt32('TrackNumber'),
    ULInt32('TotalTracks'),
    ULInt32('Year'),
    ULInt32('BitRate'),
    ULInt32('SampleRate'),
    LInt32('Volume'),
    ULInt32('StartTime'),
    ULInt32('StopTime'),
    ULInt32('SoundCheck'),
    ULInt32('PlayCount'),
    ULInt32('PlayCount2'),
    ULInt32('LastPlayedTime'),
    ULInt32('DiscNumber'),
    ULInt32('TotalDiscs'),
    ULInt32('UserID'),
    ULInt32('DateAdded'),
    ULInt32('BookmarkTime'),
    ULInt64('DBID'),
    Boolean(UInt8('Checked')),
    UInt8('ApplicationRating'),
    ULInt16('BPM'),
    ULInt16('ArtworkCount'),
    Padding(2),
    ULInt32('ArtworkSize'),
    Padding(4),
    ULInt32('SampleRate2'),
    ULInt32('DateReleased'),
    Padding(2),
    ULInt16('ExplicitFlag'),
    Padding(4),
    Padding(4),
    ULInt32('SkipCount'),
    ULInt32('LastSkipped'),
    Boolean(UInt8('HasArtwork')),
    Boolean(UInt8('SkipWhenShuffling')),
    Boolean(UInt8('RememberPlaybackPosition')),
    Boolean(UInt8('Flag4')),
    ULInt64('DBI2'),
    Boolean(UInt8('LyricsFlag')),
    Boolean(UInt8('MovieFileFlag')),
    Boolean(UInt8('PlayedMark')),
    Padding(1),
    Padding(4),
    ULInt32('PreGap'),
    ULInt64('SampleCount'),
    Padding(4),
    ULInt32('PostGap'),
    Padding(4),
    Enum(ULInt32('MediaType'),
        AUDIO_VIDEO=0x0,
        AUDIO=0x1,
        VIDEO=0x2,
        PODCAST=0x4,
        VIDEO_PODCAST=0x6,
        AUDIOBOOK=0x8,
        MUSIC_VIDEO=0x20,
        TV_SHOW=0x40,
        TV_SHOW2=0x60,
        ),
    ULInt32('SeasonNumber'),
    ULInt32('EpsiodeNumber'),
    Padding(4),  # unk31
    Padding(4),
    Padding(4),
    Padding(4),
    Padding(4),
    Padding(4),
    Padding(4),  # unk37
    ULInt32('GaplessData'),
    Padding(4),  # unk38
    Boolean(ULInt16('GaplessTrackFlag')),
    Boolean(ULInt16('GaplessAlbumFlag')),
    Padding(20),  # unk39
    Padding(4),
    Padding(4),
    Padding(4),
    Padding(4),
    Padding(4),  # unk44
    ULInt16('AlbumID'),
    Padding(4),
    ULInt32('ArtistID'),

    Anchor('__StartOfHeaderPadding'),
    Padding(lambda c: c.HeaderLength - (c.__StartOfHeaderPadding - c.__StartOfData)),

#    Anchor('__StartOfDataPadding'),
#    Padding(lambda c: c.TotalLength - (c.__StartOfDataPadding - c.__StartOfData), name='Padding'),
    Array('DatabaseObjects', MHOD, lambda c: c.NumberOfStrings),
    Anchor('__EndOfData'),
    Assertion(_struct_size_check, 'data size mismatch'),
)

# TrackList --------------------------------------------------------------------

MHLT = Structure('TrackList',
    Anchor('__StartOfData'),

    Dump(Constant(String('HeaderIdentifier', 4), 'mhlt')),
    ULInt32('HeaderLength'),
    ULInt32('NumberOfSongs'),
    Anchor('__StartOfHeaderPadding'),
    Padding(lambda c: c.HeaderLength - (c.__StartOfHeaderPadding - c.__StartOfData)),
    Array('Tracks',
        MHIT, lambda c: c.NumberOfSongs
        ),
    Anchor('__EndOfData'),
)

# Database ---------------------------------------------------------------------

MHSD = Structure('DataSet',
    Anchor('__StartOfData'),

    Constant(String('HeaderIdentifier', 4), 'mhsd'),
    ULInt32('HeaderLength'),
    ULInt32('TotalLength'),
    Enum(ULInt32('Type'),
        TRACKLIST=1,
#        PLAYLIST=2,
        _default='PADDING',
        ),
    Anchor('__StartOfHeaderPadding'),
    Padding(lambda c: c.HeaderLength - (c.__StartOfHeaderPadding - c.__StartOfData)),
    Anchor('__StartOfDataPadding'),
    Switch(lambda c: c.Type, {
        'PADDING' : Padding(lambda c: c.TotalLength - (c.__StartOfDataPadding - c.__StartOfData), name='Padding'),
        'TRACKLIST' : MHLT,
        }),
    Anchor('__EndOfData'),
    Assertion(_struct_size_check, 'data size mismatch'),
)

MHBD = Structure('DatabaseObject',
    Anchor('__StartOfData'),
    Constant(String('HeaderIdentifier', 4), 'mhbd'),
    ULInt32('HeaderLength'),
    ULInt32('TotalLength'),
    Padding(4),
    ULInt32('VersionNumber'),
    ULInt32('NumberOfChildren'),
    Padding(8),
    Padding(2),
    Padding(4),
    Padding(8),
    ULInt16('HashingScheme'),
    Padding(20),
    ULInt16('Language'),
    ULInt64('LibraryPersistentId'),
    Padding(4),
    Padding(4),
    Padding(20),
    Padding(4),
    Padding(2),
    Padding(46),
    Anchor('__StartOfPadding'),
    Padding(lambda c: c.HeaderLength - (c.__StartOfPadding - c.__StartOfData)),
    Array('Children',
        MHSD, lambda c: c.NumberOfChildren
        ),
    Anchor('__EndOfData'),

    Assertion(_struct_size_check, 'data size mismatch'),
)


ITunesDB = MHBD

# Entry ------------------------------------------------------------------------

def parse():
    with open('iTunesDB', 'rb') as fp:
        return ITunesDB.parse(fp)

def profile():
    import cProfile as Profile
    import pstats
    fn = 'demo_itunes.profile'
    Profile.run('parse()', fn)
    stats = pstats.Stats(fn)

    stats.strip_dirs()
    stats.sort_stats('time')

    stats.print_stats()
    stats.print_callers()
    stats.print_callees()

def memory():
    import gc
    import pprint
    result = parse()
    del result
    pprint.pprint(gc.garbage)

def main():
    context = parse()
    view_context(context)
#    memory()
#    profile()

if __name__ == '__main__':
    main()
