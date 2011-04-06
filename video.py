#!/usr/bin/env python

import array
import cProfile
import datetime
import struct
import sys
import idct
import psyco
psyco.full()

# from zig-zag back to normal
ZIG_ZAG_POSITIONS = array.array('B', ( 0,  1,  8, 16,  9,  2, 3, 10,
                     17, 24, 32, 25, 18, 11, 4,  5,
                     12, 19, 26, 33, 40, 48, 41, 34,
                     27, 20, 13,  6,  7, 14, 21, 28,
                     35, 42, 49, 56, 57, 50, 43, 36,
                     29, 22, 15, 23, 30, 37, 44, 51,
                     58, 59, 52, 45, 38, 31, 39, 46,
                     53, 60, 61, 54, 47, 55, 62, 63))

# int16_t
iquant_tab = array.array('B', ( 3,  5,  7,  9, 11, 13, 15, 17,
               5,  7,  9, 11, 13, 15, 17, 19,
               7,  9, 11, 13, 15, 17, 19, 21,
               9, 11, 13, 15, 17, 19, 21, 23,
              11, 13, 15, 17, 19, 21, 23, 25,
              13, 15, 17, 19, 21, 23, 25, 27,
              15, 17, 19, 21, 23, 25, 27, 29,
              17, 19, 21, 23, 25, 27, 29, 31))

# Used for upscaling the 8x8 b- and r-blocks to 16x16
scalemap = array.array('B', ( 0,  0,  1,  1,  2,  2,  3,  3,
             0,  0,  1,  1,  2,  2,  3,  3,
             8,  8,  9,  9, 10, 10, 11, 11,
             8,  8,  9,  9, 10, 10, 11, 11,
            16, 16, 17, 17, 18, 18, 19, 19,
            16, 16, 17, 17, 18, 18, 19, 19,
            24, 24, 25, 25, 26, 26, 27, 27,
            24, 24, 25, 25, 26, 26, 27, 27,

             4,  4,  5,  5,  6,  6,  7,  7,
             4,  4,  5,  5,  6,  6,  7,  7,
            12, 12, 13, 13, 14, 14, 15, 15,
            12, 12, 13, 13, 14, 14, 15, 15,
            20, 20, 21, 21, 22, 22, 23, 23,
            20, 20, 21, 21, 22, 22, 23, 23,
            28, 28, 29, 29, 30, 30, 31, 31,
            28, 28, 29, 29, 30, 30, 31, 31,

            32, 32, 33, 33, 34, 34, 35, 35,
            32, 32, 33, 33, 34, 34, 35, 35,
            40, 40, 41, 41, 42, 42, 43, 43,
            40, 40, 41, 41, 42, 42, 43, 43,
            48, 48, 49, 49, 50, 50, 51, 51,
            48, 48, 49, 49, 50, 50, 51, 51,
            56, 56, 57, 57, 58, 58, 59, 59,
            56, 56, 57, 57, 58, 58, 59, 59,

            36, 36, 37, 37, 38, 38, 39, 39,
            36, 36, 37, 37, 38, 38, 39, 39,
            44, 44, 45, 45, 46, 46, 47, 47,
            44, 44, 45, 45, 46, 46, 47, 47,
            52, 52, 53, 53, 54, 54, 55, 55,
            52, 52, 53, 53, 54, 54, 55, 55,
            60, 60, 61, 61, 62, 62, 63, 63,
            60, 60, 61, 61, 62, 62, 63, 63))

clzlut = array.array('B', (8, 7, 6, 6, 5, 5, 5, 5, 4, 4, 4, 4, 4,
          4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2,
          2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
          2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
          1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
          1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
          1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
          0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))

FIX_0_298631336 = 2446
FIX_0_390180644 = 3196
FIX_0_541196100 = 4433
FIX_0_765366865 = 6270
FIX_0_899976223 = 7373
FIX_1_175875602 = 9633
FIX_1_501321110 = 12299
FIX_1_847759065 = 15137
FIX_1_961570560 = 16069
FIX_2_053119869 = 16819
FIX_2_562915447 = 20995
FIX_3_072711026 = 25172

CONST_BITS = 13
PASS1_BITS = 1
F1 = CONST_BITS - PASS1_BITS - 1
F2 = CONST_BITS - PASS1_BITS
F3 = CONST_BITS + PASS1_BITS + 3

class BitReader(object):

    def __init__(self, packet):
        self.packet = packet
        self.offset = 0
        self.bits_left = 0
        self.chunk = 0
        self.read_bits = 0

    def read(self, nbits, consume=True):
        # Read enough bits into chunk so we have at least nbits available
        while nbits > self.bits_left:
            try:
                self.chunk = (self.chunk << 32) | struct.unpack_from('<I', self.packet, self.offset)[0]
            except:
                self.chunk <<= 32
            self.offset += 4
            self.bits_left += 32
        # Get the first nbits bits from chunk (and remove them from chunk)
        shift = self.bits_left - nbits
        res = self.chunk >> shift
        if consume:
            self.chunk -= res << shift
            self.bits_left -= nbits
            self.read_bits += nbits
        return res

    def align(self):
        shift = (8 - self.read_bits) % 8
        self.read(shift)


def get_pheader(bitreader):
    bitreader.align()
    psc = bitreader.read(22)
    assert(psc == 0b0000000000000000100000)
    pformat = bitreader.read(2)
    assert(pformat != 0b00)
    if pformat == 1:
        # CIF
        width, height = 88, 72
    else:
        # VGA
        width, height = 160, 120
    presolution = bitreader.read(3)
    assert(presolution != 0b000)
    # double resolution presolution-1 times
    width = width << presolution - 1
    height = height << presolution - 1
    #print "width/height:", width, height
    ptype = bitreader.read(3)
    pquant = bitreader.read(5)
    pframe = bitreader.read(32)
    return width, height


def inverse_dct(block):
    workspace = zeros[0:64]
    data = zeros[0:64]

    for pointer in range(8):

        if (block[pointer + 8] == 0 and block[pointer + 16] == 0 and
            block[pointer + 24] == 0 and block[pointer + 32] == 0 and
            block[pointer + 40] == 0 and block[pointer + 48] == 0 and
            block[pointer + 56] == 0):
            dcval = block[pointer] << PASS1_BITS
            for i in range(8):
                workspace[pointer + i*8] = dcval
            continue

        z2 = block[pointer + 16]
        z3 = block[pointer + 48]

        z1 = (z2 + z3) * FIX_0_541196100
        tmp2 = z1 + z3 * -FIX_1_847759065
        tmp3 = z1 + z2 * FIX_0_765366865

        z2 = block[pointer]
        z3 = block[pointer + 32]

        tmp0 = (z2 + z3) << CONST_BITS
        tmp1 = (z2 - z3) << CONST_BITS

        tmp10 = tmp0 + tmp3
        tmp13 = tmp0 - tmp3
        tmp11 = tmp1 + tmp2
        tmp12 = tmp1 - tmp2

        tmp0 = block[pointer + 56]
        tmp1 = block[pointer + 40]
        tmp2 = block[pointer + 24]
        tmp3 = block[pointer + 8]

        z1 = tmp0 + tmp3
        z2 = tmp1 + tmp2
        z3 = tmp0 + tmp2
        z4 = tmp1 + tmp3
        z5 = (z3 + z4) * FIX_1_175875602

        tmp0 *= FIX_0_298631336
        tmp1 *= FIX_2_053119869
        tmp2 *= FIX_3_072711026
        tmp3 *= FIX_1_501321110
        z1 *= -FIX_0_899976223
        z2 *= -FIX_2_562915447
        z3 *= -FIX_1_961570560
        z4 *= -FIX_0_390180644

        z3 += z5
        z4 += z5

        tmp0 += z1 + z3
        tmp1 += z2 + z4
        tmp2 += z2 + z3
        tmp3 += z1 + z4

        workspace[pointer + 0] = ((tmp10 + tmp3 + (1 << F1)) >> F2)
        workspace[pointer + 56] = ((tmp10 - tmp3 + (1 << F1)) >> F2)
        workspace[pointer + 8] = ((tmp11 + tmp2 + (1 << F1)) >> F2)
        workspace[pointer + 48] = ((tmp11 - tmp2 + (1 << F1)) >> F2)
        workspace[pointer + 16] = ((tmp12 + tmp1 + (1 << F1)) >> F2)
        workspace[pointer + 40] = ((tmp12 - tmp1 + (1 << F1)) >> F2)
        workspace[pointer + 24] = ((tmp13 + tmp0 + (1 << F1)) >> F2)
        workspace[pointer + 32] = ((tmp13 - tmp0 + (1 << F1)) >> F2)

    for pointer in range(0, 64, 8):

        z2 = workspace[pointer + 2]
        z3 = workspace[pointer + 6]

        z1 = (z2 + z3) * FIX_0_541196100
        tmp2 = z1 + z3 * -FIX_1_847759065
        tmp3 = z1 + z2 * FIX_0_765366865

        tmp0 = (workspace[pointer] + workspace[pointer + 4]) << CONST_BITS
        tmp1 = (workspace[pointer] - workspace[pointer + 4]) << CONST_BITS

        tmp10 = tmp0 + tmp3
        tmp13 = tmp0 - tmp3
        tmp11 = tmp1 + tmp2
        tmp12 = tmp1 - tmp2

        tmp0 = workspace[pointer + 7]
        tmp1 = workspace[pointer + 5]
        tmp2 = workspace[pointer + 3]
        tmp3 = workspace[pointer + 1]

        z1 = tmp0 + tmp3
        z2 = tmp1 + tmp2
        z3 = tmp0 + tmp2
        z4 = tmp1 + tmp3

        z5 = (z3 + z4) * FIX_1_175875602

        tmp0 *= FIX_0_298631336
        tmp1 *= FIX_2_053119869
        tmp2 *= FIX_3_072711026
        tmp3 *= FIX_1_501321110
        z1 *= -FIX_0_899976223
        z2 *= -FIX_2_562915447
        z3 *= -FIX_1_961570560
        z4 *= -FIX_0_390180644

        z3 += z5
        z4 += z5

        tmp0 += z1 + z3
        tmp1 += z2 + z4
        tmp2 += z2 + z3
        tmp3 += z1 + z4

        data[pointer + 0] = (tmp10 + tmp3) >> F3
        data[pointer + 7] = (tmp10 - tmp3) >> F3
        data[pointer + 1] = (tmp11 + tmp2) >> F3
        data[pointer + 6] = (tmp11 - tmp2) >> F3
        data[pointer + 2] = (tmp12 + tmp1) >> F3
        data[pointer + 5] = (tmp12 - tmp1) >> F3
        data[pointer + 3] = (tmp13 + tmp0) >> F3
        data[pointer + 4] = (tmp13 - tmp0) >> F3

    return data


def get_mb(bitreader):
    mbc = bitreader.read(1)
    block = zip(zeros[0:256],zeros[0:256],zeros[0:256])

    if mbc == 0:
        y = zeros[0:256]
        mbdesc = bitreader.read(8)
        assert(mbdesc >> 7 & 1)
        if mbdesc >> 6 & 1:
            mbdiff = bitreader.read(2)
        #y[0:63] = get_block2(bitreader, mbdesc & 1)
        #y[64:127] = get_block2(bitreader, mbdesc >> 1 & 1)
        #y[128:191] = get_block2(bitreader, mbdesc >> 2 & 1)
        #y[192:255] = get_block2(bitreader, mbdesc >> 3 & 1)

        y = get_block2(bitreader, mbdesc & 1)
        y.extend(get_block2(bitreader, mbdesc >> 1 & 1))
        y.extend(get_block2(bitreader, mbdesc >> 2 & 1))
        y.extend(get_block2(bitreader, mbdesc >> 3 & 1))

        cb = get_block2(bitreader, mbdesc >> 4 & 1)
        cr = get_block2(bitreader, mbdesc >> 5 & 1)
        # ycbcr to rgb
        for i in range(256):
            j = scalemap[i]
            Y = y[i] - 16
            B = cb[j] - 128
            R = cr[j] - 128
            r = (298 * Y           + 409 * R + 128) >> 8
            g = (298 * Y - 100 * B - 208 * R + 128) >> 8
            b = (298 * Y + 516 * B           + 128) >> 8
            r = 0 if r < 0 else r
            r = 255 if r > 255 else r
            g = 0 if g < 0 else g
            g = 255 if g > 255 else g
            b = 0 if b < 0 else b
            b = 255 if b > 255 else b
            block[i] = r, g, b
        #print "right before first ybr2rgb"
        #print idct.ybr2rgb(y, cb, cr, block)
        #print "right before second ybr2rgb"
        #block = idct.ybr2rgb(y, cb, cr, block)
    else:
        print "mbc was not zero"
    return block

zeros = array.array('i', [0 for i in range(256)])



def _first_half(data):
    # data has to be 12 bits wide
    streamlen = 0
    # count the zeros
    zerocount = clzlut[data >> 4];
    data = (data << (zerocount + 1)) & 0b111111111111
    streamlen += zerocount + 1
    # get number of remaining bits to read
    toread = 0 if zerocount <= 1 else zerocount - 1
    additional = data >> (12 - toread)
    data = (data << toread) & 0b111111111111
    streamlen += toread
    # add as many zeros to out_list as indicated by additional bits
    # if zerocount is 0, tmp = 0 else the 1 merged with additional bits
    tmp = 0 if zerocount == 0 else (1 << toread) | additional
    return [streamlen, tmp]

def _second_half(data):
    # data has to be 15 bits wide
    streamlen = 0
    zerocount = clzlut[data >> 7];
    data = (data << (zerocount + 1)) & 0b111111111111111
    streamlen += zerocount + 1
    # 01 == EOB
    eob = False
    if zerocount == 1:
        eob = True
        return [streamlen, None, eob]
    # get number of remaining bits to read
    toread = 0 if zerocount == 0 else zerocount - 1
    additional = data >> (15 - toread)
    data = (data << toread) & 0b111111111111111
    streamlen += toread
    tmp = (1 << toread) | additional
    # get one more bit for the sign
    tmp = -tmp if data >> (15 - 1) else tmp
    tmp = int(tmp)
    streamlen += 1
    return [streamlen, tmp, eob]

FH = [_first_half(i) for i in range(2**12)]
SH = [_second_half(i) for i in range(2**15)]

TRIES = 16
MASK = 2**(TRIES*32)-1
SHIFT = 32*(TRIES-1)

def get_block2(bitreader, has_coeff):
    # read the first 10 bits in a 16 bit datum
    out_list = zeros[0:64]
    out_list[0] = int(bitreader.read(10)) * iquant_tab[0]
    if not has_coeff:
        #return inverse_dct(out_list)
        return idct.idct(out_list, [])
    i = 1
    while 1:
        _ = bitreader.read(32*TRIES, False)
        streamlen = 0
        #######################################################################
        for j in range(TRIES):
            data = (_ << streamlen) & MASK
            data >>= SHIFT

            l, tmp = FH[data >> 20]
            streamlen += l
            data = (data << l) & 0xffffffff
            i += tmp

            l, tmp, eob = SH[data >> 17]
            streamlen += l
            if eob:
                bitreader.read(streamlen)
                #return inverse_dct(out_list)
                return idct.idct(out_list, [])
            j = ZIG_ZAG_POSITIONS[i]
            out_list[j] = tmp*iquant_tab[j]
            i += 1
        #######################################################################
        bitreader.read(streamlen)
    #return inverse_dct(out_list)
    return idct.idct(out_list, [])



def get_gob(bitreader, blocks):
    block = []
    bitreader.align()
    gobsc = bitreader.read(22)
    if gobsc == 0b0000000000000000111111:
        print "weeeee"
        return False
    elif (not (gobsc & 0b0000000000000000100000) or
         (gobsc & 0b1111111111111111000000)):
        print "Got wrong GOBSC, aborting.", bin(gobsc)
        return False
    #print 'GOBSC:', gobsc & 0b11111
    _ = bitreader.read(5)
    for i in range(blocks):
        #print "b%i" % i
        block.extend(get_mb(bitreader))
    return block

def read_picture(bitreader):
    t = datetime.datetime.now()
    block = []
    width, height = get_pheader(bitreader)
    slices = height / 16
    blocks = width / 16
    # this is already the first slice
    for i in range(blocks):
        block.extend(get_mb(bitreader))
    # those are the remaining ones
    for i in range(1, slices):
        #print "Getting Slice", i, slices
        block.extend(get_gob(bitreader, blocks))
    bitreader.align()
    eos = bitreader.read(22)
    assert(eos == 0b0000000000000000111111)
    t2 = datetime.datetime.now()
    #print "\nEND OF PICTURE\n"
    #print slices, blocks
    #print len(block)
    #print 'time', t2 - t, ',', 1. / (t2 - t).microseconds * 1000000, 'fps'
    # print the image
    #from PIL import Image
    #im = Image.new("RGBA", (blocks*16, slices*16))
    #i = 0
    #for sl in range(slices):
    #    for bl in range(blocks):
    #        for j in range(4):
    #            for y in range(8):
    #                for x in range(8):
    #                    r, g, b = block[i]
    #                    if j == 0:
    #                        im.putpixel((bl*16+x, sl*16+y), (r, g, b))
    #                    if j == 1:
    #                       im.putpixel((bl*16+x+8, sl*16+y), (r, g, b))
    #                    if j == 2:
    #                       im.putpixel((bl*16+x, sl*16+y+8), (r, g, b))
    #                    if j == 3:
    #                       im.putpixel((bl*16+x+8, sl*16+y+8), (r, g, b))
    #                    i += 1
    #im.show()
    return (t2 - t).microseconds / 1000000.

def _pp(name, value):
    #return
    print "%s\t\t%s\t%s" % (name, str(bin(value)), str(value))


def main():
    fh = open('framewireshark.raw', 'r')
    #fh = open('videoframe.raw', 'r')
    #fh = open('video.raw', 'r')
    data = fh.read()
    fh.close()
    runs = 20
    t = 0
    for i in range(runs):
        print '.',
        br = BitReader(data)
        t += read_picture(br)
    print
    print 'avg time:\t', t / runs, 'sec'
    print 'avg fps:\t', 1 / (t / runs), 'fps'


if __name__ == '__main__':
    if 'profile' in sys.argv:
        cProfile.run('main()')
    else:
        main()

