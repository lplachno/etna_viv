'''
Parse execution data log stream.
Allows access to selected parts of program memory at the time of recorded events.
'''
# Copyright (c) 2012-2013 Wladimir J. van der Laan
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sub license,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice (including the
# next paragraph) shall be included in all copies or substantial portions
# of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
from __future__ import print_function, division, unicode_literals
import os, sys, struct
from collections import namedtuple
from bisect import bisect_right
from binascii import b2a_hex

LITTLE_ENDIAN = b'<'
BIG_ENDIAN = b'>'

# target architecture description
ENDIAN = LITTLE_ENDIAN
DEBUG = False

RECTYPE_CHAR = b'B' # always 8 bit
MAGIC_CHAR = b'I' # always 32 bit
WORD_CHAR = b'I' # 32 bit
ADDR_CHAR = b'I' # 32/64 bit
LONG_WORD = b'Q' # 64 bit
SHORT_STRING_SIZE_CHAR = b'B'

# struct specifiers for decoding
RECTYPE_SPEC = struct.Struct(ENDIAN + RECTYPE_CHAR)
HDR_SPEC = struct.Struct(ENDIAN + MAGIC_CHAR + WORD_CHAR)
WORD_SPEC = struct.Struct(ENDIAN + WORD_CHAR)
ADDR_SPEC = struct.Struct(ENDIAN + ADDR_CHAR)
RANGE_SPEC = struct.Struct(ENDIAN + ADDR_CHAR + ADDR_CHAR)
IOCTL_SIZE_SPEC = struct.Struct(ENDIAN + ADDR_CHAR + WORD_CHAR + ADDR_CHAR + WORD_CHAR)
IOCTL_SIZE_SPEC_64B = struct.Struct(ENDIAN + LONG_WORD + LONG_WORD + LONG_WORD + LONG_WORD)
SHORT_STRING_SIZE_SPEC = struct.Struct(ENDIAN + SHORT_STRING_SIZE_CHAR)

FDR_MAGIC = 0x8e1aaa8f
FDR_VERSION = 1

class RTYPE:
    '''
    FDR record types
    '''
    RANGE_DATA = 0
    RANGE_TEMP_DATA = 1
    ADD_UPDATED_RANGE = 2
    REMOVE_UPDATED_RANGE = 3
    EVENT = 4
    COMMENT = 5 

def read_spec(f, spec):
    return spec.unpack(f.read(spec.size))

def read_short_string(f):
    (size,) = read_spec(f, SHORT_STRING_SIZE_SPEC)
    return f.read(size)

Event = namedtuple('Event', ['event_type', 'parameters'])
Comment = namedtuple('Comment', ['data'])
Parameter = namedtuple('Parameter', ['name','value'])

class FDRLoader(object):
    '''
    High-level interface for playing back FDR files.

    The object is an iterable that returns event records:
    - Event(...) in case of an event
    - Comment(...) in case of an comment

    Also it can be subscripted to return the current contents of a memory range, like
      fdr[ptr:ptr+4] to return a range, or just fdr[ptr] to return one byte.
    An IndexError will be raised if either the start or stop is out of range 
    (or not up to date at the time of this event).
    '''
    def __init__(self, input_file):
        self.f = open(input_file, 'rb')
        magic,version = read_spec(self.f, HDR_SPEC)
        if magic != FDR_MAGIC:
            raise ValueError('Magic value %08x not recognized (should be %08x)' % (magic, FDR_MAGIC))
        if version != FDR_VERSION:
            raise ValueError('Version %08x not recognized (should be %08x)' % (version, FDR_VERSION))

        # Stored memory ranges
        self.stored = []
        # Active memory ranges
        self.updated_ranges = []
        # Temporary data
        self.temp_ranges = []
        # Cached list of starting addresses for bisection
        self.updated_ranges_start = []
        self.temp_ranges_start = []
        # IMPORTANT precondition: all ranges must be non-overlapping

    def _flush_temps(self):
        self.temp_ranges = []
        self.temp_ranges_start = []

    def __iter__(self):
        f = self.f
        while True:
            try:
                rt, = read_spec(f, RECTYPE_SPEC)
            except struct.error: # could not parse entire structure; end of file allowed here
                break
            if rt == RTYPE.RANGE_DATA:
                addr_start,addr_end = read_spec(f, RANGE_SPEC)
                data = f.read(addr_end - addr_start)
                if DEBUG:
                    print('RANGE_DATA 0x%08x 0x%08x %s...' % (addr_start, addr_end, b2a_hex(data[0:16])))
                # TODO update self.stored
                self.update(addr_start, addr_end, data)
            elif rt == RTYPE.RANGE_TEMP_DATA:
                addr_start,addr_end = read_spec(f, RANGE_SPEC)
                data = f.read(addr_end - addr_start)
                if DEBUG:
                    print('RANGE_TEMP_DATA 0x%08x 0x%08x %s...' % (addr_start, addr_end, b2a_hex(data[0:16])))
                self.temp_ranges.append((addr_start, addr_end, data))
            elif rt == RTYPE.ADD_UPDATED_RANGE:
                addr_start,addr_end = read_spec(f, RANGE_SPEC)
                if DEBUG:
                    print('ADD_UPDATED_RANGE 0x%08x 0x%08x' % (addr_start, addr_end))
                self.updated_ranges.append((addr_start, addr_end, bytearray(addr_end - addr_start)))
                self.updated_ranges.sort()
                self.updated_ranges_start = [r[0] for r in self.updated_ranges]
            elif rt == RTYPE.REMOVE_UPDATED_RANGE:
                addr_start,addr_end = read_spec(f, RANGE_SPEC)
                i = bisect_right(self.updated_ranges_start, addr_start) - 1
                if DEBUG:
                    print('REMOVE_UPDATED_RANGE 0x%08x 0x%08x (%i)' % (addr_start, addr_end, i))
                assert(self.updated_ranges[i][0] == addr_start and self.updated_ranges[i][1] == addr_end)
                del self.updated_ranges[i]
                # keep cached list of ranges up-to-date
                self.updated_ranges_start = [r[0] for r in self.updated_ranges]
                #self.updated_ranges.remove((addr_start, addr_end))
            elif rt == RTYPE.EVENT:
                event_type = read_short_string(f)
                num_parameters, = read_spec(f, WORD_SPEC)
                parameters = {}
                for i in range(num_parameters):
                    par = Parameter(
                            name=read_short_string(f), 
                            value=read_spec(f, ADDR_SPEC)[0])
                    parameters[par.name] = par

                parstr = ' '.join([('%s=0x%x' % par) for par in parameters.itervalues()])
                self.temp_ranges.sort()
                self.temp_ranges_start = [r[0] for r in self.temp_ranges]
                if DEBUG:
                    print('EVENT %s %s' % (event_type, parstr))
                yield Event(event_type, parameters)
                self._flush_temps()
            elif rt == RTYPE.COMMENT:
                size, = read_spec(f, ADDR_SPEC)
                comment = f.read(size)
                if DEBUG:
                    print('COMMENT')
                yield Comment(comment)
            else:
                raise ValueError('Unexpected record type %i' % rt)
    
    def __getitem__(self, key):
        '''
        Get one byte or a range of bytes from this memory map.
        '''
        # Support slicing as well as single lookups
        if isinstance(key, slice):
            start = key.start
            stop = key.stop
            if key.step is not None:
                raise KeyError('Extended slices not supported')
        else:
            start = key
            stop = key+1
        try:
            return self.fetch(self.temp_ranges_start, self.temp_ranges, start, stop)
        except IndexError,e:
            # need to convert to str explicitly because struct won't work with bytearray
            return str(self.fetch(self.updated_ranges_start, self.updated_ranges, start, stop))

    def fetch(self, ranges_start, ranges, start, stop):
        '''Look up in stored or temp ranges'''
        # XXX we don't handle the case of a request spanning multiple consecutive ranges
        idx = bisect_right(ranges_start, start) - 1
        if idx < 0:
            raise IndexError('Start address 0x%x out of range' % (start))
        (range_start, range_end, range_data) = ranges[idx]
        if stop > range_end:
            raise IndexError('End address 0x%x out of range (ends 0x%x)' % (stop, range_end))
        return range_data[start-range_start:stop-range_start]

    def update(self, start, stop, data):
        '''
        Update a stored memory range.
        '''
        idx = bisect_right(self.updated_ranges_start, start) - 1
        if idx < 0:
            raise IndexError('Start address 0x%x out of range' % (start))
        (range_start, range_end, range_data) = self.updated_ranges[idx]
        if stop > range_end:
            raise IndexError('End address 0x%x out of range (ends 0x%x)' % (stop, range_end))
        range_data[start-range_start:stop-range_start] = data


