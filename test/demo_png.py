# -*- coding: utf-8 -*-

""" PNG File Format 1.2
See http://www.libpng.org/pub/png/spec/pngspec-index.html_

NOTE: This don't really decode image data...
"""

import io
import sys, os, os.path
sys.path.insert(0, '../src')

from binaryparser import *

# Header Signature -------------------------------------------------------------

PNGFileSignature = Constant(Bytes('PNGFileSignature', 8), b'\x89PNG\r\n\x1a\n')

# Chunk bodies -----------------------------------------------------------------

def _bit_depth_check(color_depth, color_type):
    if 'GRAYSCALE' == color_type:
        return color_depth in [1, 2, 4, 8, 16]
    if color_type in ['RGB', 'RGBA', 'GRAYSCALE_ALPHA']:
        return color_depth in [8, 16]
    if 'INDEXED' == color_type:
        return color_depth in [1, 2, 4, 8]

IHDR = Structure('ImageHeader',
    UBInt32('Width'),
    UBInt32('Height'),
    UInt8('BitDepth'),
    Enum(UInt8('ColorType'),
        GRAYSCALE=0,
        RGB=2,
        INDEXED=3,
        GRAYSCALE_ALPHA=4,
        RGBA=6,
        ),
    Enum(UInt8('CompressionMethod'),
        DEFLATE=0,
        ),
    Enum(UInt8('FilterMethod'),
        ADAPTIVE=0,
        ),
    Enum(UInt8('InterlaceMethod'),
        NONE=0,
        ADAM7=1,
        ),
    Assertion(lambda c: _bit_depth_check(c.BitDepth, c.ColorType)),

    )

PLTE = Structure('ImagePalette',
    Assertion(lambda c: c.__.Length % 3 == 0, 'Palette size must be divisible by 3'),
    Calculate('Size', lambda c: c.__.Length // 3),
    Array('Colormap',
        FormatStructure('Color', '>BBB', ['Red', 'Green', 'Blue']),
        lambda c: c.Size,
        )
    )

IEND = NullField()  # not used now

IDAT = Padding(lambda c: c.__.Length)  # not used now

# XXX:
TRNS = Structure('Transparency',
    Assertion(lambda c: c.__.__[0].Type == 'IHDR', 'first chunks must be IHDR'),
    Calculate('Size', lambda c: c.__.Length),
    Calculate('Size2', lambda c: 2 ** c.__.__[0].ImageHeader.BitDepth - 1),
    Switch(lambda c: c.__.__[0].ImageHeader.ColorType,
        {
            'INDEXED' : Array('Data', UInt8('Alpha'), lambda c: c.Size),
            'GAYSCALE' : Array('Data', UBInt16('Alpha'), lambda c: c.Size2),
            'RGB' : Structure('Data',
                                   Array('Red', UBInt16('Alpha'), lambda c: c.Size2),
                                   Array('Green', UBInt16('Alpha'), lambda c: c.Size2),
                                   Array('Blue', UBInt16('Alpha'), lambda c: c.Size2))
        }
    )
    )

GAMA = Structure('Gramma',
    UBInt32('Gramma')
    )

CHRM = FormatStructure('PrimaryChromaticities',
    '>IIIIIIII', [
        'WhitePointX', 'WhitePointY', 'RedX',
        'RedY', 'GreenX', 'GreenY', 'BlueX' , 'BlueY'
        ]
    )

TEXT = Structure('TextualData',
    String('Keyword', 0),
    Anchor('__StartOfText'),
    String('Text', lambda c: c.__.Length - (c.__StartOfText - c.__.__StartOfData), errors='ignore'),
    )

# Chunk ------------------------------------------------------------------------

Chunk = Structure('Chunk',
    UBInt32('Length'),
    Embed(Union('ChunkType',
        String('Type', 4),
        BitwiseStructure('Property', [
            (None, 4),
            ('AncillaryBit', 1),
            (None, 3),
            (None, 4),
            ('PrivateBit', 1),
            (None, 3),
            (None, 4),
            ('ReservedBit', 1),
            (None, 3),
            (None, 4),
            ('SafeToCopy', 1),
            (None, 3),
            ]
        ))),
    Anchor('__StartOfData'),
    Switch(lambda c: c.Type,
        {
            'IHDR' : IHDR,
            'PLTE' : PLTE,
            'gAMA' : GAMA,
            'cHRM' : CHRM,
            'tEXt' : TEXT,
            'tRNS' : TRNS
        },
        default_field=Padding(lambda c: c.Length),
        ),
    Anchor('__EndOfData'),
    Assertion(lambda c: c.__EndOfData - c.__StartOfData == c.Length, 'data size mismatch'),
    Bytes('CRC', 4),
    )

# File -------------------------------------------------------------------------

PNGFile = Structure('PNGFile',
    PNGFileSignature,
    RepeatUntil('Chunks',
        lambda c: c and c[-1].Type == 'IEND',
        Chunk,
        stop_on_eof=False
    ),
    )

def main():
    with open('tiger.png', 'rb') as fp:
        r = PNGFile.parse(fp)
        pretty_print(r)
        view_context(r)


if __name__ == '__main__':

#    import cProfile as Profile
#    import pstats
#    fn = 'demo_png.profile'
#    Profile.run('main()', fn)
#    stats = pstats.Stats(fn)
#
#    stats.strip_dirs()
#    stats.sort_stats('time')
#
#    stats.print_stats()
#    stats.print_callers()
#    stats.print_callees()

    main()
