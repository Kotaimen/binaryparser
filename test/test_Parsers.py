# -*- coding: utf-8 -*-

import unittest
import io
import sys, os, os.path
sys.path.insert(0, '../src')

from binaryparser import *

DUMP = False

class TestIntegerFields(unittest.TestCase):

    def setUp(self):
        self.format = Structure(
            None,
            Int8('Byte'),
            UInt8('Char'),
            Int16('Short1'),
            UInt16('Short2'),
            UBInt16('Short3'),
            ULInt16('Short4'),
            Int32('Int1'),
            UInt32('Int2'),
            UBInt32('Int3'),
            ULInt32('Int4'),
            UBInt64('Longlong')
            )
        self.data = \
            b'\xff\xff' \
            b'\xff\xff\xff\xff\x01\x02\x01\x02' \
            b'\xff\xff\xff\xff\xff\xff\xff\xff' \
            b'\x01\x02\x03\x04\x01\x02\x03\x04' \
            b'\x01\x02\x03\x04\x05\x06\x07\x08' \

    def tearDown(self):
        del self.format
        del self.data


    def testIntegerFields(self):
        stream = io.BytesIO(self.data)
        r = self.format.parse(stream)

        self.assertEqual(r.Byte , -1)
        self.assertEqual(r.Char , 2 ** 8 - 1)
        self.assertEqual(r.Short1 , -1)
        self.assertEqual(r.Short2 , 2 ** 16 - 1)
        self.assertEqual(r.Short3 , 0x0102)
        self.assertEqual(r.Short4 , 0x0201)
        self.assertEqual(r.Int1 , -1)
        self.assertEqual(r.Int2 , 2 ** 32 - 1)
        self.assertEqual(r.Int3 , 0x01020304)
        self.assertEqual(r.Int4 , 0x04030201)
        self.assertEqual(r.Longlong, 0x0102030405060708)

        if DUMP:
            print ('testIntegerFields'.center(75, '='))
            print (self.format)
            pretty_print (r)

class TestBytes(unittest.TestCase):

    def setUp(self):

        self.formatBytesStatic = Structure(
            None,
            Bytes('Magic', 4)
            )
        self.formatBytesDynamic = Structure(
            None,
            UBInt16('Length'),
            Bytes('Bytes', lambda c: c.Length)
            )
        self.dataBytesStatic1 = b'MGCK'
        self.dataBytesStatic2 = b'MGC'

        self.dataBytesDynamic = b'\x00\x04MGCK'

    def testBytesStatic(self):
        stream = io.BytesIO(self.dataBytesStatic1)
        r = self.formatBytesStatic.parse(stream)
        self.assertEqual(r.Magic, b'MGCK')

        def throws():
            r = self.formatBytesStatic.parse(io.BytesIO(self.dataBytesStatic2))
        self.assertRaises(StreamExhausted, throws)

        if DUMP:
            print ('testBytesStatic'.center(75, '='))
            print (self.formatBytesStatic)
            pretty_print (r)

    def testBytesDynamic(self):
        stream = io.BytesIO(self.dataBytesDynamic)
        r = self.formatBytesDynamic.parse(stream)
        self.assertEqual(r.Bytes, b'MGCK')

        if DUMP:
            print ('testBytesDynamic'.center(75, '='))
            print (self.formatBytesDynamic)
            print (r)

class TestString(unittest.TestCase):

    def setUp(self):
        self.formatStringStatic = Structure(
            None,
            String('Str1', 14),
            Padding(2),
            String('Str2', 15, padchar=None),
            Padding(1),
            String('Str3', 30, encoding='utf_16_be')
            )
        self.dataStringStatic = \
            b'Hello, world!\0\0\0' \
            b'Hello, world!\0\0\0' \
            b'\0H\0e\0l\0l\0o\0,\0 \0w\0o\0r\0l\0d\0!\0\0\0\0'

        self.formatStringDynamic = Structure(
            None,
            UBInt16('EncodingLength'),
            String('Encoding', lambda c: c.EncodingLength),
            UBInt16('StringLength'),
            String('String',
                   length=lambda c: c.StringLength,
                   encoding=lambda c: c.Encoding),
            )
        self.dataStringDynamic = \
            b'\x00\x0f' \
            b'utf_16_be\0\0\0\0\0\0' \
            b'\0\x1e' \
            b'\0H\0e\0l\0l\0o\0,\0 \0w\0o\0r\0l\0d\0!\0\0\0\0'

        self.formatStringCStyle = Structure(
            None,
            String('Encoding'),
            String('String', encoding=lambda c: c.Encoding),
            )
        self.dataStringCStyle = \
            b'utf_32_le\0' \
            b'H\x00\x00\x00e\x00\x00\x00l\x00\x00\x00l\x00\x00\x00o' \
            b'\x00\x00\x00,\x00\x00\x00 \x00\x00\x00w\x00\x00\x00o\x00' \
            b'\x00\x00r\x00\x00\x00l\x00\x00\x00d\x00\x00\x00!\x00\x00\x00' \
            b'\0\0\0\0'

    def testStringStatic(self):
        stream = io.BytesIO(self.dataStringStatic)
        r = self.formatStringStatic.parse(stream)
        self.assertEqual(r.Str1, 'Hello, world!')
        self.assertEqual(r.Str2, 'Hello, world!\0\0')
        self.assertEqual(r.Str3, 'Hello, world!')

        if DUMP:
            print ('testStringStatic'.center(75, '='))
            print (self.formatStringStatic)
            pretty_print (r)

    def testStringDynamic(self):
        stream = io.BytesIO(self.dataStringDynamic)
        r = self.formatStringDynamic.parse(stream)
        self.assertEqual(r.String, 'Hello, world!')

        if DUMP:
            print ('testStringDynamic'.center(75, '='))
            print (self.formatStringDynamic)
            pretty_print (r)

    def testStringCStyle(self):
        stream = io.BytesIO(self.dataStringCStyle)
        r = self.formatStringCStyle.parse(stream)
        self.assertEqual(r.String, 'Hello, world!')

        if DUMP:
            print ('testStringCStyle'.center(75, '='))
            print (self.formatStringCStyle)
            pretty_print (r)

class TestAdapters(unittest.TestCase):

    def setUp(self):
        self.formatHexBin = Structure(
            None,
            Hex(UInt8('Hex')),
            Bin(UInt8('Bin')),
            )
        self.dataHexBin = b'\xfa\xfb'

        self.formatEnum = Structure(
            None,
            Enum(UBInt16('Encoding1'),
                 utf_8=1, gbk=936, shift_jis=932),
            Enum(UBInt16('Encoding2'),
                 utf_8=1, gbk=936, shift_jis=932, _default='ascii'),
            )

    def testHexBin(self):
        stream = io.BytesIO(self.dataHexBin)
        r = self.formatHexBin.parse(stream)
        self.assertEqual(r.Hex , '0xfa')
        self.assertEqual(r.Bin , '0b11111011')

        if DUMP:
            print ('testHexBin'.center(75, '='))
            print (self.formatHexBin)
            pretty_print (r)

    def testEnum(self):
        stream = io.BytesIO(b'\0\x01\0\x01')
        r = self.formatEnum.parse(stream)
        self.assertEqual(r.Encoding1, 'utf_8')
        self.assertEqual(r.Encoding2, 'utf_8')

        if DUMP:
            print ('testEnum'.center(75, '='))
            print (self.formatEnum)
            pretty_print (r)

        stream = io.BytesIO(b'\0\x00')
        def throws():
            r = self.formatEnum.parse(stream)
        self.assertRaises(InvalidEnumValue, throws)



class TestValidators(unittest.TestCase):

    def testConstant(self):
        self.assertRaises(ValidationError, self._testConstant)

    def _testConstant(self):
        p = Structure(None,
                      Bytes('Magic1', 4),
                      Constant(Bytes('Magic2', 4),
                               b'ABCD'),
                      Constant(UBInt32('Magic3'),
                               16),
                      )
        s = io.BytesIO(b'abcdABCD\0\0\0\x0f')
        if DUMP:
            print ('testConstant'.center(75, '='))
            print (p)
        r = p.parse(s)



class TestStructure(unittest.TestCase):

    def testNestedStructure(self):
        p = Structure('Outer',
                      UBInt16('Outer1'),
                      UBInt16('Outer2'),
                      Structure('Inner1',
                                UBInt16('Inner1'),
                                UBInt16('Inner2'),
                                ),
                      UBInt16('Outer3'),
                      Structure('Inner2',
                                UBInt16('Inner3'),
                                ULInt16('Inner4'),
                                ),
                      )
        s = io.BytesIO(bytes(range(20)))
        r = p.parse(s)
        self.assertEqual(r.Outer1 , 0x0001)
        self.assertEqual(r.Outer2 , 0x0203)
        self.assertEqual(r.Inner1.Inner1, 0x0405)
        self.assertEqual(r.Inner1.Inner2, 0x0607)
        self.assertEqual(r.Outer3, 0x0809)
        self.assertEqual(r.Inner2.Inner3, 0x0A0B)
        self.assertEqual(r.Inner2.Inner4, 0x0D0C)
        if DUMP:
            print ('TestStructure'.center(75, '='))
            print (p)
            pretty_print (r)

class TestArray(unittest.TestCase):

    def testStaticArray(self):
        p = Array('Values',
                 UInt8(None),
                 10)
        s = io.BytesIO(bytes(range(10)))
        r = p.parse(s)
        self.assertEqual(len(r), 10)
        for n in range(10):
            self.assertEqual(r[n], n)

        if DUMP:
            print ('testStaticArray'.center(75, '='))
            print (p)
            pretty_print (r)

    def testDynamicArray(self):
        p = Structure('Foo',
                      UBInt16('Length'),
                      Array('Foo',
                            Structure('Item',
                                      UBInt16('Field1'),
                                      UInt8('Field2'),
                                      ),
                            lambda context: context.Length
                            ),
                      )

        s = io.BytesIO(b'\x00\x05' + bytes(range(3 * 0x5)))
        r = p.parse(s)
        self.assertEqual(r.Length, len(r.Foo))

        if DUMP:
            print ('testDynamicArray'.center(75, '='))
            print (p)
            pretty_print (r)

class TestFormatStructure(unittest.TestCase):

    def testFormatStructure(self):
        p1 = Structure(None,
                       UInt8('F1'),
                       UBInt16('F2'),
                       UBInt32('F3'),
                       )
        p2 = FormatStructure(None, '>BHI', 'F1 F2 F3'.split(' '))
        s1 = io.BytesIO(bytes(range(7)))
        s2 = io.BytesIO(bytes(range(7)))
        r1 = p1.parse(s1)
        r2 = p2.parse(s2)
        self.assertEqual(r1, r2)
        if DUMP:
            print ('testFormatStructure'.center(75, '='))
            print (p1)
            print (p2)
            pretty_print (r1)
            pretty_print (r2)


class TestRepeatUntil(unittest.TestCase):

    def setUp(self):
        self.format1 = Structure(
            None,
            String('Last'),
            RepeatUntil('Strings',
                lambda c: len(c) > 0 and c[-1] == c.__.Last,
                String(None), stop_on_eof=False
                )

            )
        self.data1 = \
            b'\0' \
            b'The Zen of Python\0' \
            b'Beautiful is better than ugly\0' \
            b'Explicit is better than implicit.\0'\
            b'Simple is better than complex.\0' \
            b'\0'

    def testRepeatString(self):
        stream = io.BytesIO(self.data1)
        r = self.format1.parse(stream)
        self.assertEqual(len(r.Strings), 5)
        if DUMP:
            print ('testRepeatString'.center(75, '='))
            print (self.format1)
            pretty_print (r)

class TestUnion(unittest.TestCase):

    def setUp(self):
        self.format1 = Structure(
            None,
            Union('Union',
                  UInt8('Int8'),
                  UBInt16('Int16'),
                  UBInt32('Int32'),
                  Structure('Pair',
                            UBInt16('X'),
                            UBInt16('Y'),
                      )
            ),
            Constant(Bytes('Magic', 4), b'MGCK')
            )
        self.data1 = b'\x00\x01\x02\x03MGCK'

    def testUnion(self):
        stream = io.BytesIO(self.data1)
        r = self.format1.parse(stream)
        self.assertEqual(r.Union.Int8, 0x0)
        self.assertEqual(r.Union.Int16, 0x1)
        self.assertEqual(r.Union.Int32, 0x010203)
        self.assertEqual(r.Union.Pair.X, 0x01)
        self.assertEqual(r.Union.Pair.Y, 0x0203)
        self.assertEqual(r.Magic, b'MGCK')
        if DUMP:
            print ('testUnion'.center(75, '='))
            print (self.format1)
            pretty_print (r)

class TestBitwiseStructure(unittest.TestCase):

    def setUp(self):
        self.format1 = BitwiseStructure(None,
            [
                ('I1', 3),
                ('I2', 1),
                ('I3', 11),
                ('I4', 1),
                (None, 2),
                ('I6', 7),
                ('I7', 3),
                ('I8', 4),
            ]
            )
        self.data1 = b'\x12\x34\x56\x78'

    def testBitwise1(self):
        stream = io.BytesIO(self.data1)
        r = self.format1.parse(stream)
        self.assertEqual(r.I1, 0x2)
        self.assertEqual(r.I2, 0x0)
        self.assertEqual(r.I3, 0x341)
        self.assertEqual(r.I4, 0x0)

        self.assertEqual(r.I6, 0x15)
        self.assertEqual(r.I7, 0x04)
        self.assertEqual(r.I8, 0x07)

        if DUMP:
            print ('testUnion'.center(75, '='))
            print (self.format1)
            pretty_print (r)
            
class TestConditionalFields(unittest.TestCase):

    def testIfElse(self):
        p = Structure('Foo',
                       Enum(UInt8('Kind'), Bytes=0, String=1),
                       UBInt16('EncodingIsUtf8'),
                       IfElse(lambda context: context.Kind == 'Bytes',
                              Bytes('Byte', 15),
                              IfElse(lambda context: context.EncodingIsUtf8 > 0,
                                String('Str', 15, encoding='utf-8'),
                                String('Str', 15, encoding='ascii', padchar=None)
                              )
                       )
                   )
        s = io.BytesIO(b'\x01\x00\x02hello, world\0\0\0')
        r = p.parse(s)
        if DUMP:
            print ('testIfElse'.center(75, '='))
            print (p)
            pretty_print (r)


class TestSpecialFields(unittest.TestCase):

    def setUp(self):
        self.format1 = Structure(None,
                                 UBInt16('PaddingSize'),
                                 Rename('StartPosition', Anchor('Pos1')),
                                 Padding(lambda c: c.PaddingSize),
                                 NullField(),
                                 Rename('EndPosition', Anchor('Pos1')),
                                 Calculate('Size', lambda c:c.EndPosition - c.StartPosition)
                                 )
        self.data1 = b'\x00\x04mgck'

    def testSpecialFields(self):
        stream = io.BytesIO(self.data1)
        r = self.format1.parse(stream)
        self.assertEqual(r.Size, 4)
        if DUMP:
            print ('testSpecialFields'.center(75, '='))
            print (self.format1)
            pretty_print (r)

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
