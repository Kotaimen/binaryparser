# -*- coding : utf-8 -*-

import io
import struct
import codecs
import sys

__all__ = ['Adapter', 'Anchor', 'Array', 'ArrayContext',
'AssertEqual', 'Assertion', 'BInt16', 'BInt32', 'BInt64', 'BYTE',
'Bin', 'BinaryParserError', 'BitwiseStructure', 'Boolean', 'Bytes',
'Calculate', 'ConditionalField', 'Constant', 'ContainerField',
'Contains', 'ContextError', 'DWORD', 'Dump', 'Embed', 'Enum', 'Field',
'FieldError', 'FieldNameError', 'FormatArray', 'FormatField',
'FormatStructure', 'FormatUnion', 'Hex', 'IfElse', 'Int16', 'Int32',
'Int64', 'Int8', 'InvalidChildField', 'InvalidEnumValue',
'InvalidFieldName', 'InvalidFieldParameter', 'InvalidFieldSize',
'InvalidFunctor', 'LInt16', 'LInt32', 'LInt64', 'NoDefaultField',
'NullField', 'Padding', 'ParseError', 'PrettyPrinter', 'Rename',
'RepeatUntil', 'Select', 'SizeofError', 'StaticField', 'StreamError',
'StreamExhausted', 'StreamStateBookmark', 'String', 'StructContext',
'Structure', 'Switch', 'UBInt16', 'UBInt32', 'UBInt64', 'UInt16',
'UInt32', 'UInt64', 'UInt8', 'ULInt16', 'ULInt32', 'ULInt64', 'Union',
'ValidationError', 'Validator', 'WORD', 'Watch', 'WrapperField',
'hex_dump', 'pretty_print']


#===============================================================================
# Exceptions
#===============================================================================

class BinaryParserError(Exception):  pass
class ContextError(BinaryParserError): pass
class FieldError(BinaryParserError): pass
class ParseError(BinaryParserError): pass

class InvalidFieldParameter(FieldError): pass
class InvalidFieldName(FieldError): pass
class InvalidChildField(FieldError): pass
class InvalidFunctor(FieldError): pass
class InvalidFieldSize(FieldError): pass

class SizeofError(ParseError): pass
class StreamError(ParseError): pass
class ValidationError(ParseError):pass
class StreamExhausted(ParseError): pass
class InvalidEnumValue(ParseError):pass

class FieldNameError(ParseError): pass
class NoDefaultField(ParseError):pass

#===============================================================================
# Context
#===============================================================================

class StructContext(dict):

    """ Context object stores parsing result of a structure field

    Performance: Originally this class is implemented as a subclass of
    container.OrderedDict, but that proved to be too slow and cumbersome...
    """

    # this class really need __slots__ to save object dictionary
    __slots__ = '_StructContext__order', '__', '_StructContext__name'

    def __init__(self, name=None, parent=None):
        self.__ = parent
        self.__name = name
        self.__order = list()

    def __getattr__(self, name):
        if name in self:
            return self.get(name)
        else:
            return self.__getattribute__(name)

    def __setitem__(self, key, value):
        self.__order.append(key)
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        self.__order.remove(key)
        dict.__delitem__(self, key)

    def __dir__(self):
        attrlist = list(self.keys())
        attrlist.extend(self.__slots__)
        return attrlist

    def get_ordered_items(self):
        for key in self.__order:
            if not key.startswith('__'):
                yield key, self.__getitem__(key)

    def get_reversed_items(self):
        for key in reversed(self.__order):
            if not key.startswith('__'):
                yield key, self.__getitem__(key)

    def get_parent(self):
        return self.__

    def get_name(self):
        return self.__name

    def get_key_order(self):
        return self.__order

    def extend_key_order(self, order):
        # Performance hack...
        self.__order.extend(order)


class ArrayContext(list):

    """ Context object stores parsing result of an array field """

    __slots__ = '__', '_ArrayContext__name'

    def __init__(self, name=None, parent=None):
        self.__ = parent
        self.__name = name

    def get_ordered_items(self):
        for n, item in enumerate(self):
            yield n, item

    def get_reversed_items(self):
        for n, item in reversed(self.__order):
            yield n, item

    def get_parent(self):
        return self.__

    def get_name(self):
        return self.__name

#===============================================================================
# Public Helper Classes
#===============================================================================

class PrettyPrinter():

    """ Pretty print the context tree """

    # XXX Works incorrect in some cases...

    def __init__(self):
        pass

    def pretty_print(self, obj):
        buffer = io.StringIO()
        if isinstance(obj, StructContext):
            self._structcontext_pprint(obj, buffer, '')
        elif isinstance(obj, ArrayContext):
            self._arraycontext_pprint(obj, buffer, '')
        else:
            raise ContextError('Not a Context')
        return buffer.getvalue()

    def _structcontext_pprint(self, context, stream, ident):
        if context.get_name():
            stream.write(context.get_name())
        else:
            stream.write('StructContext')
        stream.write(' {\n')
        pad = max(len(k) for k in context.keys())
        ident1 = ident + ' |- '
        ident2 = '{} | {}'.format(ident, ' ' * (pad + 3))
        for name, value in context.get_ordered_items():
            stream.write(ident1)
            stream.write('{name:{pad}} : '.format(name=name, pad=pad))
            if isinstance(value, StructContext):
                self._structcontext_pprint(value, stream, ident2)
            elif isinstance(value, ArrayContext):
                self._arraycontext_pprint(value, stream, ident2)
            else:
                stream.write('{!r}\n'.format(value))
        stream.write(ident)
        stream.write('}\n')

    def _arraycontext_pprint(self, context, stream, ident):
        if context.get_name():
            stream.write(context.get_name())
        else:
            stream.write('ArrayContext')
        stream.write(' [\n')
        pad = len(str(len(context)))
        ident1 = ident + ' |-#'
        ident2 = '{} | {}'.format(ident, ' ' * (pad + 3))
        for name, value in context.get_ordered_items():
            stream.write(ident1)
            stream.write('{name:{pad}} : '.format(name=name, pad=pad))
            if isinstance(value, StructContext):
                self._structcontext_pprint(value, stream, ident2)
            elif isinstance(value, ArrayContext):
                self._arraycontext_pprint(value, stream, ident2)
            else:
                stream.write('{!r}\n'.format(value))
        stream.write(ident)
        stream.write(']\n')

class StreamStateBookmark():

    """ Remember the stream offset in a with statement """

    def __init__(self, stream):
        if not stream.seekable():
            raise StreamError('Requires a seekable stream')
        self._stream = stream
        self._offset = 0

    def __enter__(self):
        self._offset = self._stream.tell()
        return self._stream

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._stream.seek(self._offset, io.SEEK_SET)



#===============================================================================
# Public Helper Functions
#===============================================================================

def pretty_print(obj):
    print(PrettyPrinter().pretty_print(obj))


def hex_dump(stream, offset, size):

    """ Dump stream context in "Hex viewer" style """

    data_row_size = 16
    offset_size = 11
    hex_row_size = data_row_size * 2 + data_row_size - 1
    buffer = io.StringIO()

    def write_hex_string(data, right_justify=False):
        hex_string = ' '.join(hex(ch)[2:].upper().rjust(2, '0') for ch in data)
        if right_justify:
            hex_string = hex_string.rjust(hex_row_size)
        else:
            hex_string = hex_string.ljust(hex_row_size)
        buffer.write(hex_string)

    def convert_ch(ch):
        if ch > 38 and ch < 128:
            return chr(ch)
        elif ch >= 128:
            return '_'
        else:
            return '.'

    def write_data_string(data, right_justify=False):
        data_string = ''.join(convert_ch(ch) for ch in data)
        if right_justify:
            data_string = data_string.rjust(data_row_size)
        else:
            data_string = data_string.ljust(data_row_size)
        buffer.write(data_string)

    with StreamStateBookmark(stream) as stream:
        buffer.write('OFFSET'.center(offset_size))
        buffer.write(' | ')
        buffer.write(' '.join(hex(n)[2:].upper().rjust(2) \
                              for n in range(data_row_size)))
        buffer.write(' | ')
        buffer.write('DATA'.center(16))
        buffer.write('\n')
        buffer.write('-' * 80)
        buffer.write('\n')

        data_read = 0
        row_offset = offset
        stream.seek(offset, io.SEEK_SET)

        if offset % data_row_size != 0:
            read_size = data_row_size - offset % data_row_size
            data = stream.read(read_size)
            data_read += len(data)

            row_offset = offset // data_row_size * data_row_size

            buffer.write(hex(row_offset)[2:].rjust(offset_size, '0'))
            buffer.write(' | ')
            write_hex_string(data, True)
            buffer.write(' | ')
            write_data_string(data, True)
            buffer.write('\n')

        while data_read <= size:
            row_offset += data_row_size
            if data_row_size + data_read <= size:
                read_size = data_row_size
            else:
                read_size = size - data_read
            data = stream.read(read_size)
            if len(data) == 0:
                break

            buffer.write(hex(row_offset)[2:].rjust(offset_size, '0'))
            buffer.write(' | ')
            write_hex_string(data)
            buffer.write(' | ')
            write_data_string(data)
            buffer.write('\n')

            data_read += read_size
            # row_offset += read_size

    return buffer.getvalue()

#===============================================================================
# Private Helper Functions
#===============================================================================

def _is_valid_functor(f):
    if not hasattr(f, '__call__'):
        return False
    if 1 != f.__code__.co_argcount:
        return False
    return True

def _is_positive_integer(i):
    if not isinstance(i, int):
        return False
    if i <= 0:
        return False
    return True

def _is_valid_field_name(n):
    if n is None:
        # None is OK
        return True
    if not n:
        # but empty string is not good
        return False
    if not n.isidentifier():
        # must be a valid Python identifier
        return False
    if n.startswith('__') and len(n) > 3:
        # anything starts with two underscores is Ok
        return True
    elif n[0].isupper():
        # otherwise must start with upper-case char
        return True
    else:
        return False

def _is_unique(i):
    return len(i) == len(set(i))

#===============================================================================
# Abstract Classes
#===============================================================================

class Field():

    """ Basic class for all fields

    A field describes how to parse particular byte data in a binary
    stream.  It also gives parsed data a name.

    Field should be immutable and thread safe thus it shall not keep
    internal parsing state. """

    def __init__(self, name):
        if not _is_valid_field_name(name):
            raise InvalidFieldName(name)
        self.name = name

    def __repr__(self):
        """ Generate a repr for the parser itself """
        return '{}({})'.format(self.__class__.__name__, self.name)

    def parse(self, stream, context):
        """ Parse stream and returns context

        Most fields doesn't require a seekable stream.
        """
        raise NotImplementedError()

    def sizeof(self, context):
        """ Byte size of the field """
        raise SizeofError()

    def is_embedded(self):
        """ Whether the fields in current structure is embedded into
        outer structure """
        return False

    def is_nested(self):
        """ Whether the field contains other fields """
        return False

class StaticField(Field):

    """ A field with fixed size """

    def __init__(self, name, size):
        super().__init__(name)
        if (not isinstance(size, int)) or (size < 0):
            raise InvalidFieldSize('Size must be non negative, got {!r}'.format(size))
        self._size = size

    def sizeof(self, context):
        return self._size

class WrapperField(Field):

    """ A field wraps a child field, inherit its name if no name
    is provided """

    def __init__(self, field, name=None):
        if not isinstance(field, Field):
            raise InvalidChildField('Child must be a Field, got {!r}'.format(field))
        super().__init__(field.name if name is None else name)
        self._childfield = field

    def __repr__(self):
        return '{}({}, {!r})'.format(self.__class__.__name__,
                                     self.name,
                                     self._childfield)

    def parse(self, stream, context):
        return self._childfield.parse(stream, context)

    def sizeof(self, context):
        return self._childfield.sizeof(context)

    def is_nested(self):
        return self._childfield.is_nested()

    def is_embedded(self):
        return self._childfield.is_embedded()

class ContainerField(Field):

    """ A container of child fields, this can be name-value pairs (aka
    Structure) or a linear list (Array) """

    def __repr__(self):
        buffer = io.StringIO()
        self._pretty_print(buffer, 0)
        return buffer.getvalue()

    def is_nested(self):
        return True

    def is_embedded(self):
        return False

class ConditionalField(Field):

    """ A field which its layout is determined at run time """

    def is_nested(self):
        return False

    def is_embedded(self):
        return True

#===============================================================================
# Basic Fields
#===============================================================================

class Adapter(WrapperField):

    """ Convert inner field parse result to another format """

    def parse(self, stream, context):
        return self.unpack(self._childfield.parse(stream, context))

    def unpack(self, value):
        raise NotImplementedError()

class Validator(WrapperField):

    """ Validate parsed value, raise ValidationError if failed """

    def parse(self, stream, context):
        value = self._childfield.parse(stream, context)
        if not self.validate(value):
            raise ValidationError()
        return value

    def validate(self, value):
        raise NotImplementedError()

class FormatField(StaticField):

    """ A static field uses Python build-in struct module to parse
    data.

    Note the interpretation of format depends on Python compiler, see
    document of struct module for more information.
    """

    def __init__(self, name, format):
        formatter = struct.Struct(format)
        super().__init__(name, formatter.size)
        self._formatter = formatter

    def parse(self, stream, context):
        data = stream.read(self._formatter.size)
        try:
            return self._formatter.unpack(data)
        except struct.error as e:
            raise StreamExhausted() from e

#===============================================================================
# Integer Fields
#===============================================================================

class _IntegerFieldBase(Field):

    """ Base class for integer fields

    Fly-weight pattern: Integer fields will be used many, many times so
    reuse underlying FormatField to avoid creation overhead of
    struct.Struct objects. """

    FORMAT_FIELDS = [
                     FormatField('Int8', 'b'),
                     FormatField('UInt8', 'B'),
                     FormatField('Int16', 'h'),
                     FormatField('BInt16', '>h'),
                     FormatField('LInt16', '<h'),
                     FormatField('UInt16', 'H'),
                     FormatField('UBInt16', '>H'),
                     FormatField('ULInt16', '<H'),
                     FormatField('Int32', 'i'),
                     FormatField('BInt32', '>i'),
                     FormatField('LInt32', '<i'),
                     FormatField('UInt32', 'I'),
                     FormatField('UBInt32', '>I'),
                     FormatField('ULInt32', '<I'),
                     FormatField('Int64', 'q'),
                     FormatField('BInt64', '>q'),
                     FormatField('LInt64', '<q'),
                     FormatField('UInt64', 'Q'),
                     FormatField('UBInt64', '>Q'),
                     FormatField('ULInt64', '<Q'),
                     ]

    FIELD_NO = None

    def __init__(self, name):
        super().__init__(name)
        self._field = self.FORMAT_FIELDS[self.FIELD_NO]

    def parse(self, stream, context):
        return self._field.parse(stream, context)[0]

    def __repr__(self):
        return '{}()'.format(self._field.name)

# Classes below are generated by following code block:
# (actually it is possible to generate these classes dynamiclly, but that will
#  be too difficult to debug)

# for n, field in enumerate(_IntegerFieldBase.FORMAT_FIELDS):
#    code = """class {name}(_IntegerFieldBase):
#    FIELD_NO = {n}""".format(name=field.name, n=n)
#    exec(code, globals(), locals())
#    print (code)
# else:
#    # delete unused global variables
#    del n, field, code

class Int8(_IntegerFieldBase):
    FIELD_NO = 0
class UInt8(_IntegerFieldBase):
    FIELD_NO = 1
class Int16(_IntegerFieldBase):
    FIELD_NO = 2
class BInt16(_IntegerFieldBase):
    FIELD_NO = 3
class LInt16(_IntegerFieldBase):
    FIELD_NO = 4
class UInt16(_IntegerFieldBase):
    FIELD_NO = 5
class UBInt16(_IntegerFieldBase):
    FIELD_NO = 6
class ULInt16(_IntegerFieldBase):
    FIELD_NO = 7
class Int32(_IntegerFieldBase):
    FIELD_NO = 8
class BInt32(_IntegerFieldBase):
    FIELD_NO = 9
class LInt32(_IntegerFieldBase):
    FIELD_NO = 10
class UInt32(_IntegerFieldBase):
    FIELD_NO = 11
class UBInt32(_IntegerFieldBase):
    FIELD_NO = 12
class ULInt32(_IntegerFieldBase):
    FIELD_NO = 13
class Int64(_IntegerFieldBase):
    FIELD_NO = 14
class BInt64(_IntegerFieldBase):
    FIELD_NO = 15
class LInt64(_IntegerFieldBase):
    FIELD_NO = 16
class UInt64(_IntegerFieldBase):
    FIELD_NO = 17
class UBInt64(_IntegerFieldBase):
    FIELD_NO = 18
class ULInt64(_IntegerFieldBase):
    FIELD_NO = 19

class BYTE(_IntegerFieldBase):  # = UINt8
    FIELD_NO = 1
class WORD(_IntegerFieldBase):  # = UInt16
    FIELD_NO = 5
class DWORD(_IntegerFieldBase):  # = UInt32
    FIELD_NO = 11

#===============================================================================
# String Fields
#===============================================================================

class Bytes(WrapperField):

    """ Field yields raw data as Python bytes object

    Length can be a positive integer or a function, which returns a integer
    as bytes length.

    """

    # TODO: This copies data from stream, not efficient when data is large, need
    # a "stream view" class ...

    class _BytesMixin():

        def _parse(self, stream, context, length):
            data = stream.read(length)
            if len(data) != length:
                raise StreamExhausted('Expected {} bytes, read {}'\
                                      .format(length, len(data)))
            return data

    class _StaticBytes(StaticField, _BytesMixin):

        def __init__(self, length):
            super().__init__(None, length)
            self._length = length

        def parse(self, stream, context):
            return self._parse(stream, context, self._length)

    class _DynamicBytes(Field, _BytesMixin):

        def __init__(self, length_function):
            super().__init__(None)
            self._length_function = length_function

        def sizeof(self, context):
            return self._length_function(context)

        def parse(self, stream, context):
            length = self._length_function(context)
            return self._parse(stream, context, length)

    def __init__(self, name, length):

        if _is_valid_functor(length):
            super().__init__(self._DynamicBytes(length), name=name)
        elif length >= 0:
            super().__init__(self._StaticBytes(length), name=name)
        else:
            raise InvalidFunctor('Length must be a positive integer or a ' \
                                 'callable object, got {!r}'.format(length))

    def __repr__(self):
        return '{}.{}()'.format(self.__class__.__name__,
                                self._childfield.__class__.__name__[1:])

class String(WrapperField):

    """ A field which represents a string

    The string can be both fixed length (padded) or null terminated, also it
    supports
    encoding conversion on-the-fly.
    """

    class _StringMixin():

        def __init__(self, encoding, errors, padchar):
            if _is_valid_functor(encoding):
                self._is_dynamic_encoding = True
            else:
                self._is_dynamic_encoding = False
                try:
                    codecs.lookup(encoding)
                except LookupError as e:
                    raise InvalidFieldParameter('Invalid encoding {}'. \
                                                format(encoding)) from e
            self._encoding = encoding
            self._errors = errors
            self._padchar = padchar

        def _parse(self, stream, context, length):
            if self._is_dynamic_encoding:
                encoding = self._encoding(context)
            else:
                encoding = self._encoding
            assert length >= 0
            data = stream.read(length)
            if len(data) != length:
                raise StreamExhausted('Expected {} bytes, read {}'\
                                             .format(length, len(data)))

            string = data.decode(encoding, self._errors)
            if self._padchar is not None:
                return string.rstrip(self._padchar)
            else:
                return string

    class _StaticString(StaticField, _StringMixin):

        def __init__(self, length, encoding, errors, padchar):
            StaticField.__init__(self, None, length)
            String._StringMixin.__init__(self, encoding, errors, padchar)
            self._length = length

        def parse(self, stream, context):
            return self._parse(stream, context, self._length)

        def __repr__(self):
            return '{}({})'.format(self.__class__.__name__, self._length)

    class _DynamicString(Field, _StringMixin):

        def __init__(self, length, encoding, errors, padchar):
            Field.__init__(self, None)
            String._StringMixin.__init__(self, encoding, errors, padchar)
            self._length_function = length

        def sizeof(self, context):
            return self._length_function(context)

        def parse(self, stream, context):
            length = self._length_function(context)
            return self._parse(stream, context, length)

        def __repr__(self):
            return '{}()'.format(self.__class__.__name__)

    class _CString(Field):

        def __init__(self, encoding, errors):
            super().__init__(None)
            self._is_dynamic_encoding = _is_valid_functor(encoding)
            self._encoding = encoding
            super().__init__(None)
            self._errors = errors

        def sizeof(self, context):
            # size of a zero terminated string can't be determined from context
            raise SizeofError()

        def parse(self, stream, context):
            if self._is_dynamic_encoding:
                encoding = self._encoding(context)
            else:
                encoding = self._encoding
            reader = codecs.getreader(encoding)(stream, self._errors)
            def char_gen():
                while True:
                    char = reader.read(size=1, chars=1)
                    if not char:
                        raise StreamExhausted('Encountered EOF before EOS')
                    if char == '\0':
                        break
                    yield char
            return ''.join(char_gen())

        def __repr__(self):
            return '{}()'.format(self.__class__.__name__)


    def __init__(self, name, length=0, encoding='ascii', errors='strict', padchar='\0'):

        if _is_valid_functor(length):
            super().__init__(self._DynamicString(length, encoding, errors, padchar),
                             name)
        elif _is_positive_integer(length):
            super().__init__(self._StaticString(length, encoding, errors, padchar),
                             name)
        elif length == 0:
            super().__init__(self._CString(encoding, errors),
                             name)
        else:
            raise InvalidFunctor('Length must be a positive integer or a callable' \
                                 'object, or 0, got {!r}'.format(length))

    def __repr__(self):
        return '{}.{}()'.format(self.__class__.__name__,
                                self._childfield.__class__.__name__[1:])

#===============================================================================
# Adapters
#===============================================================================

class Hex(Adapter):

    """ Convert adaptee to a hex string """

    def unpack(self, value):
        return hex(value)

class Bin(Adapter):

    """ Convert adaptee to a binary string """

    def unpack(self, value):
        return bin(value)

class Boolean(Adapter):

    """ Convert adaptee to a boolean value """

    def unpack(self, value):
        return bool(value)


class Enum(Adapter):

    """ Convert adaptee to a string value according to given mapping

    If no value matches, then return default value, if it is set in the
    constructor, otherwise raise InvalidEnumValue
    """

    _DEFAULT = '_default'

    def __init__(self, child_field, **kwargs):
        super().__init__(child_field)
        self._has_default_value = False
        self._default_value = None

        if self._DEFAULT in kwargs:
            self._default_value = kwargs[self._DEFAULT]
            self._has_default_value = True
            del kwargs[self._DEFAULT]

        if not _is_unique(list(kwargs.keys())):
            raise InvalidFieldParameter('Enum names must be unique')
        if not _is_unique(list(kwargs.items())):
            raise InvalidFieldParameter('Enum values must be unique')

        self._enum = dict((v, k) for (k, v) in kwargs.items())

    def unpack(self, value):
        try:
            return self._enum[value]
        except KeyError as e:
            if self._has_default_value:
                return self._default_value
            else:
                raise InvalidEnumValue(str(value)) from e

class Embed(WrapperField):

    """ A embedded field appends its contents to parent context """

    def is_embedded(self):
        return True

#===============================================================================
# Validators
#===============================================================================

class Constant(Validator):

    """ Field have a constant value

    Throw ValidationError if parse give an different value"""

    def __init__(self, child, value):
        super().__init__(child)
        self._value = value

    def validate(self, value):
        equal = (self._value == value)
        if not equal:
            raise ValidationError('Excepted: {!r}, got {!r}'.format(self._value, value))
        return equal

class AssertEqual(Validator):


    def __init__(self, childfield, functor):
        super().__init__(childfield)
        self._functor = functor

    def parse(self, stream, context):
        value = self._childfield.parse(stream, context)
        expected = self._functor(context)
        if expected != value:
            raise ValidationError('Expected value {!r}, got {!r}'.format(expected, value))
        return value

class Assertion(Field):

    def __init__(self, functor, what='Assertion Error'):
        super().__init__(None)
        self._functor = functor
        self._what = what

    def parse(self, stream, context):
        if not self._functor(context):
            raise ValidationError(self._what)
        return None

class Contains(Validator):

    # TODO : Replace with a field accepts functor

    def __init__(self, child, values):
        super().__init__(child)
        self._values = set(values)

    def validate(self, value):
        return value in self._values


#===============================================================================
# Container Fields
#===============================================================================

class _EncloseMixin():

    """ Mixin class for enclose field (Structure, Conditional) """
    @staticmethod
    def _update_context_embedded(is_embedded, stream, context, field, enclosed_context):
        # first, parse the field
        value = field.parse(stream, context)
        if field.name is None:
            # don't add to context if name is None
            return
        elif is_embedded:
            # for embedded fields, add value into enclosed context
            # don't insert one by one because the overhead of explicit loop
            enclosed_context.update(value)
            enclosed_context.extend_key_order(value.get_key_order())
        else:
            enclosed_context[field.name] = value

    @staticmethod
    def _update_context_plain(stream, context, fields):

        for field in fields:
            value = field.parse(stream, context)
            if field.name is None:
                continue
            dict.__setitem__(context, field.name, value)
        else:
            context.extend_key_order(k.name for k in fields if k.name is not None)

class Structure(ContainerField, _EncloseMixin):

    """ All fields in the structure must have unique names.  If field name is
    None, its parsing result will NOT be added to context.
    """

    def __init__(self, name, *fields):
        # child fields check
        if not all(isinstance(f, Field) for f in fields):
            raise InvalidChildField('Child must be a Field')
        if not _is_unique(list(f.name for f in fields if f.name is not None)):
            raise InvalidFieldName('Child field names must be unique or None')

        super().__init__(name)
        self._child_fields = fields
        self._embedded_flags = list(f.is_embedded() for f in fields)
        self._has_embedded_field = any(self._embedded_flags)

    def parse(self, stream, context=None):
        # create my context
        context = StructContext(name=self.name, parent=context)

        if self._has_embedded_field:
        # walk through all child fields
            for n, child_field in enumerate(self._child_fields):
                self._update_context_embedded(self._embedded_flags[n],
                                              stream, context, child_field,
                                              context)
        else:
            self._update_context_plain(stream, context, self._child_fields)
        return context

    def sizeof(self, context):
        size = 0
        for child_field in self._child_fields:
            size += child_field.sizeof(context)

    def _pretty_print(self, stream, nest_depth):
        ident = '  ' * nest_depth
        stream.write('{}{}({}):\n'\
                     .format(ident,
                             self.__class__.__name__,
                             self.name if self.name else ''))
        for field in self._child_fields:
            stream.write('{}{}'.format(ident, '  '))
            if hasattr(field, '_pretty_print'):
                field._pretty_print(stream, nest_depth + 1)
            else:
                stream.write('{!r}'.format(field))
                stream.write('\n')

class Array(ContainerField):

    """ Repeat a field for specified times

    The size can be an integer (thus a static array), or a size function
    which accepts context and returns size (dynamic array).
    """

    def __init__(self, name, field, size):
        super().__init__(name)
        self._childfield = field
        if _is_valid_functor(size):
            self._is_callable = True
            self._function = size
        elif _is_positive_integer(size):
            self._is_callable = False
            self._size = size
        else:
            raise InvalidFunctor('Size must be a integer or a callable')

    def parse(self, stream, context=None):
        context = ArrayContext(name=self.name, parent=context)

        if self._is_callable:
            size = self._function(context.get_parent())  # always use parent as context
        else:
            size = self._size

        for n in range(size):
            context.append(self._childfield.parse(stream, context))
        return context

    def sizeof(self, context):
        if self._is_callable:
            return self._function(context.get_parent()) * self._childfield.sizeof(context)
        else:
            return  self._size * self._childfield.sizeof(context)

    def _pretty_print(self, stream, nest_depth):
        stream.write('  ' * (nest_depth - 1))
        stream.write('{}({}):\n'.format(self.__class__.__name__,
                                        self.name if self.name else ''))
        if hasattr(self._childfield, '_pretty_print'):
            self._childfield._pretty_print(stream, nest_depth + 2)
        else:
            stream.write('{}{!r}\n'.format('  ' * (nest_depth + 1), self._childfield))

class FormatStructure(ContainerField, FormatField):

    """ Uses Python build-in struct module to parse data but act like
    a Structure """

    def __init__(self, name, format, field_names):
        ContainerField.__init__(self, name)
        FormatField.__init__(self, name, format)
        # parameter check
        if not _is_unique(list(f for f in field_names if f is not None)):
            raise InvalidFieldName('Child field names must be unique or None')
        if len(self._formatter.unpack(b'\0' * self._formatter.size)) != len(field_names):
            raise ParseError('field names mismatch')

        self._field_names = field_names

    def parse(self, stream, context=None):
        context = StructContext(name=self.name, parent=context)
        values = FormatField.parse(self, stream, context)
        for name, value in zip(self._field_names, values):
            if name is not None:
                context[name] = value
        return context

    def _pretty_print(self, stream, nest_depth):
        stream.write('  ' * nest_depth)
        stream.write('{}({},{!s}):\n'.format(self.__class__.__name__,
                                        self.name if self.name else '',
                                        self._formatter.format))
        for field_name in self._field_names:
            stream.write('  ' * (nest_depth + 1))
            stream.write('{}\n'.format(field_name))

class FormatArray(ContainerField):
    # XXX: not implemented yet...

    """ Uses Python build-in array module to parse data but act like a Array """

    pass

class RepeatUntil(ContainerField):

    """ Repeat a filed until given predict satisfies """

    def __init__(self, name, predict, field, stop_on_eof=True):
        if not _is_valid_functor(predict):
            raise InvalidFunctor()
        if not isinstance(field, Field):
            raise InvalidChildField('Child must be a Field')
        ContainerField.__init__(self, name)
        self._predict = predict
        self._childfield = field
        self._stop_on_eof = stop_on_eof

    def parse(self, stream, context):
        context = ArrayContext(name=self.name, parent=context)
        while True:
            if self._predict(context):
                break
            try:
                context.append(self._childfield.parse(stream, context))
            except StreamExhausted:
                if self._stop_on_eof:
                    break
                else:
                    raise
        return context

    def _pretty_print(self, stream, nest_depth):
        stream.write('  ' * (nest_depth - 1))
        stream.write('{}({}):\n'.format(self.__class__.__name__,
                                        self.name if self.name else ''))
        if hasattr(self._childfield, '_pretty_print'):
            self._childfield._pretty_print(stream, nest_depth + 2)
        else:
            stream.write('{}{!r}\n'.format('  ' * (nest_depth + 1), self._childfield))


class Union(Structure):

    """ Union

    Unlike C Union, field of this class can be container or conditional fields.
    Because the implement actually rewind the stream position after a each
    field is parsed, thus this structure requires a seekable stream """

    def parse(self, stream, context=None):
        # create my context
        context = StructContext(name=self.name, parent=context)

        for n, child_field in enumerate(self._child_fields):
            max_size_read = 0
            with StreamStateBookmark(stream) as stream:
                offset = stream.tell()
                self._update_context_embedded(self._embedded_flags[n],
                                              stream, context, child_field, context)
                size_read = stream.tell() - offset
                if size_read > max_size_read:
                    max_size_read = size_read
        else:
            stream.seek(max_size_read, io.SEEK_CUR)

        return context

    def sizeof(self, context):
        return max(f.sizeof(context) for f in self._child_fields)

class FormatUnion(Field):
    # TODO:
    """ Union which has C behavior """
    pass

#===============================================================================
# Conditional Fields
#===============================================================================

class Switch(ConditionalField, _EncloseMixin):

    """ Select a field according to a given condition variable """

    def __init__(self, condition_function, value_field_mapping, default_field=None, ignore_unmatched_fields=True):
        # check parameter
        if not _is_valid_functor(condition_function):
            raise InvalidFunctor()

        if not isinstance(value_field_mapping, dict):
            raise InvalidFieldParameter('Must be a dictionary object')
        if not all(isinstance(field, Field) for field in value_field_mapping.values()):
            raise InvalidFieldParameter('Dict must be a value-field mapping')
        if not all(field.name is not None for field in value_field_mapping.values()):
            raise InvalidChildField('Field name cannot be None')
        if not _is_unique(list(value for value in value_field_mapping.keys())):
            raise InvalidFieldParameter('Values must be unique')

        if default_field is not None:
            if not isinstance(default_field, Field):
                raise InvalidChildField('Default must be a Field')

        if not ignore_unmatched_fields:
            raise NotImplementedError()  # TODO: still under construction
            if not _is_unique(list(field.name for field in value_field_mapping.values())):
                raise InvalidChildField('Child field names must be unique when unmatched fields is not ignored')

        super().__init__(self.__class__.__name__)
        self._condition_function = condition_function
        self._mapping = value_field_mapping
        self._has_default = default_field is not None
        self._default_field = default_field
        self._ignore_unmatched = ignore_unmatched_fields

    def parse(self, stream, context):
        private_context = StructContext(name=self.name, parent=context)
        condition_key = self._condition_function(context)

        try:
            field = self._mapping[condition_key]
        except KeyError:
            if self._has_default:
                field = self._default_field
            else:
                raise NoDefaultField('Expected one of {!r}, got {!r}'\
                                     .format(list(self._mapping.keys()),
                                             condition_key))

        self._update_context_embedded(field.is_embedded(),
                                      stream, context, field, private_context)

        return private_context

    def _pretty_print(self, stream, nest_depth):
        stream.write('  ' * nest_depth)
        stream.write('{}()\n'.format(self.__class__.__name__))
        items = list(self._mapping.items())
        if self._has_default:
            items.append(('Default', self._default_field))
        pad = max(list(len(repr(item[0])) for item in items))
        for value, field in items:
            stream.write('{}{!r:{}} : '.format('  ' * (nest_depth + 2), value, pad))
            if hasattr(field, '_pretty_print'):
                stream.write('\n')
                field._pretty_print(stream, nest_depth + 3)
            else:
                stream.write('{!r}\n'.format(field))

class Select(Field, _EncloseMixin):

    """ Select a child field which predict matches (If-ElseIf-ElseIf...)"""

    def __init__(self, predict_field_list, default_field=None):
        super().__init__(self.__class__.__name__)
        for predict, field in predict_field_list:
            if not _is_valid_functor(predict):
                raise InvalidFunctor('Predict must be a callable object')
            if not isinstance(field, Field):
                raise InvalidChildField('Must be a field')
        self._predict_field_list = predict_field_list
        self._has_default = default_field is not None
        self._default_field = default_field

    def parse(self, stream, context):
        private_context = StructContext(name=self.name, parent=context)
        selected_field = None
        for predict, field in self._predict_field_list:
            if predict(context):
                selected_field = field
                break
        if selected_field is None:
            if self._has_default:
                selected_field = self._default_field
            else:
                raise NoDefaultField('No predict matches')
        self._update_context_embedded(selected_field.is_embedded(),
                                      stream, context, selected_field, private_context)

        return private_context


class IfElse(Switch):

    """ If-Then-Else """

    def __init__(self, predict, true_field, false_field=None):
        # parameter check
        if not hasattr(predict, '__call__'):
            raise InvalidFunctor('Predict must be a callable object')
        if not isinstance(true_field, Field):
            raise InvalidChildField('Must be a field')
        if false_field is None:
            false_field = NullField()
        if not isinstance(false_field, Field):
            raise InvalidChildField('Must be a field')

        condition_function = lambda context: bool(predict(context))
        value_field_mapping = { True: true_field, False: false_field }

        super().__init__(condition_function, value_field_mapping)

#===============================================================================
# Bitwise Fields
#===============================================================================

class BitwiseStructure(ContainerField):

    """ Bitwise structure

    BE AWARE: This do not behavior like bitwise structure in C/C++. There
    is no limitation of "field cannot cross used integer type boundary".

    """

    _FIELD_BE = {
              8 : UInt8(None),
              16: UBInt16(None),
              32: UBInt32(None),
              64: UBInt64(None),
              }
    _FIELD_LE = {
              8 : UInt8(None),
              16: ULInt16(None),
              32: ULInt32(None),
              64: ULInt64(None),
              }

    def __init__(self, name, fieldname_bitsize_list, byteorder=None, reversed=False):
        super().__init__(name)

        if byteorder is None:
            byteorder = sys.byteorder
        if byteorder == 'big':
            field_table = self._FIELD_BE
        elif byteorder == 'little':
            field_table = self._FIELD_LE
        else:
            raise InvalidFieldParameter('Byte order must be one of '\
                                        '"big", "little" or None, got {}'\
                                        .format(byteorder))

        total_bit_size = sum(i[1] for i in fieldname_bitsize_list)

        try:
            self._int_field = field_table[total_bit_size]
        except KeyError as e:
            raise InvalidFieldParameter('Bit size count must be one of 8, 16, '\
                                        '32, 64, got{}. '\
                                        .format(total_bit_size)) \
                                        from e

        if reversed:
            fieldname_bitsize_list.reverse()
        accumated_bit_offset = 0

        self._child_fields = list()
        for field_name, bit_size in fieldname_bitsize_list:
            self._child_fields.append((field_name,
                                       accumated_bit_offset,
                                       bit_size,
                                       int('1' * bit_size, 2) << accumated_bit_offset
                                       ))
            accumated_bit_offset += bit_size

    def parse(self, stream, context=None):
        context = StructContext(name=self.name, parent=context)
        integer = self._int_field.parse(stream, context)

        for field_name, bit_offset, bit_size, bit_mask in self._child_fields:
            field_value = (integer & bit_mask) >> bit_offset
            if field_name is not None:
                context[field_name] = field_value
        return context

    def _pretty_print(self, stream, nest_depth):
        stream.write('  ' * nest_depth)
        stream.write('{}({},{!r}):\n'.format(self.__class__.__name__,
                                        self.name if self.name else '',
                                        self._int_field))
        for field_name, bit_offset, bit_size, bit_mask in self._child_fields:
            stream.write('  ' * (nest_depth + 1))
            stream.write('{}:{}\n'.format(field_name, bit_size))


#===============================================================================
# Special Purpose Fields
#===============================================================================

class NullField(Field):

    """ A null field do not consumes binary stream nor yield any
    value """

    def __init__(self):
        super().__init__(None)

    def parse(self, stream, context):
        return

    def __repr__(self):
        return '{}()'.format(self.__class__.__name__)

    def sizeof(self, context):
        return 0

    def is_nested(self):
        return False

    def is_embedded(self):
        return False

class Padding(Field):

    """ Data padding"""

    def __init__(self, size, strict=False, padvalue=0, name=None):
        super().__init__(name)
        if _is_valid_functor(size):
            self._is_callable = True
            self._function = size
        elif _is_positive_integer(size):
            self._is_callable = False
            self._size = size
        else:
            raise InvalidFunctor('Size must be a integer or a callable')
        self._strict = strict
        self._pad = padvalue

    def parse(self, stream, context):
        if self._is_callable:
            size = self._function(context)
        else:
            size = self._size
        if not self._strict and stream.seekable():
            # if not checking padding and the stream is seekable
            # don't actually read data...
            stream.seek(size, io.SEEK_CUR)
        else:
            data = stream.read(size)
            if self._strict:
                if any(ch != self._pad for ch in data):
                    raise ValidationError('Expected {}, got {}'\
                                          .format(self._pad * size,
                                                  data))
        return None
    def sizeof(self, context):
        if self._is_callable:
            return self._function(context)
        else:
            return self._size

class Rename(WrapperField):

    """ Rename a child field """

    def __init__(self, name, child_field):
        super().__init__(child_field, name=name)

class Calculate(StaticField):
    """ Calculate a field value from context without parsing the stream """

    def __init__(self, name, calculator):
        super().__init__(name, 0)
        self._calculator = calculator

    def parse(self, stream, context):
        return self._calculator(context)

#===============================================================================
# Stream Position Related Fields
#===============================================================================

class Anchor(StaticField):

    """ Return current stream offset """

    def __init__(self, name):
        super().__init__(name, 0)

    def parse(self, stream, context):
        return stream.tell()

#===============================================================================
# Debug Helper Fields
#===============================================================================

# Debugger fields requires a seekable stream and is NOT thread safe

class Watch(WrapperField):

    """ Print value and stream when parsing """

    def __init__(self, field):
        super().__init__(field)

    def parse(self, stream, context=None):
        before_offset = stream.tell()
        value = super().parse(stream, context)
        after_offset = stream.tell()
        print ('Watch'.center(80, '*'))
        print ('Field'.center(80, '='))
        print (self._childfield)
        print ('Value'.center(80, '='))
        pretty_print(value)
        print ('Offset'.center(80, '='))
        print ('{:x}~{:x}'.format(before_offset, after_offset))
        print ('HexDump'.center(80, '='))
        print (hex_dump(stream, before_offset,
                         after_offset - before_offset))
        return value

class Dump(WrapperField):

    """ Print value and stream if a exception is thrown during parsing """

    def __init__(self, field, hexdumpsize=512):
        super().__init__(field)
        self._hexdumpsize = hexdumpsize

    def parse(self, stream, context=None):
        before_offset = stream.tell()
        try:
            return super().parse(stream, context)
        except Exception:
            after_offset = stream.tell()
            print ('Dump'.center(80, '*'))
            print ('Field'.center(80, '='))
            print (self._childfield)
            print ('Offset'.center(80, '='))
            print ('{:x}~{:x}'.format(before_offset, after_offset))
            depth = 0
            while True:

                if context is None:
                    break
                if context.get_parent() is None:
                    break
                print (' Context Level {} '.format(depth).center(80, '-'))
                pretty_print (context)
                context = context.get_parent()
                depth -= 1
            print ('HexDump'.center(80, '='))
            offset = after_offset - self._hexdumpsize // 2
            if offset < 0:
                offset = 0
            print (hex_dump(stream, offset, self._hexdumpsize))
            raise

# Uncomment this to get __all__ ------------------------------------------------
# print(sorted(k for k in globals().keys() if not k.startswith('_')))
