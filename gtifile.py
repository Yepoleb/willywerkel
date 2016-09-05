import PIL.Image
import math
import struct
import chunk
import os.path
from collections import namedtuple

"""
Attempt at reading gti images

The format is very simple, it's just an IFF chunk with a small header and the
pixel data. But many files start with 0x6624 and have seemingly random pixels
all over the image. I haven't figured out how to handle them, aside from
ignoring.

Supported formats (found in Cc.dll):
GT_FMT_A8, GT_FMT_ALPHA, GT_FMT_XRGB8888, GT_FMT_ARGB4565, GT_FMT_RGBA3328, 
GT_FMT_RGBA5551, GT_FMT_RGBA8888, GT_FMT_RGBA4444, GT_FMT_ABGR8233, 
GT_FMT_ABGR1555, GT_FMT_ABGR8888, GT_FMT_ABGR4444, GT_FMT_BGRA2338, 
GT_FMT_BGRA5551, GT_FMT_BGR555, GT_FMT_BGR233, GT_FMT_BGRA8888, GT_FMT_BGR888, 
GT_FMT_BGRA4444, GT_FMT_BGR565, GT_FMT_DXT5, GT_FMT_DXT4, GT_FMT_DXT3, 
GT_FMT_DXT2, GT_FMT_DXT1, GT_FMT_ARGB8332, GT_FMT_ARGB1555, GT_FMT_RGB555, 
GT_FMT_RGB332, GT_FMT_ARGB8888, GT_FMT_RGB888, GT_FMT_ARGB4444, GT_FMT_RGB565, 
GT_FMT_AP88, GT_FMT_P8, GT_FMT_AP44, GT_FMT_P4, GT_FMT_NONE
"""

# For "broken" images
#GTIM_FMT = "<H4sL"
#GtimTuple = namedtuple("Gtim", ["unk1", "magic", "unk2"])
GTIM_FMT = "<4sL"
GTIM_SIZE = struct.calcsize(GTIM_FMT)
GtimTuple = namedtuple("Gtim", ["magic", "unk2"])
IMAG_FMT = "<5L"
IMAG_SIZE = struct.calcsize(IMAG_FMT)
ImagTuple = namedtuple("Imag", ["unk1", "width", "height", "null", "unk2"])

filename = "ef12_22.gti"
filename_bmp = os.path.splitext(filename)[0] + ".tga"

binary = open(filename, "rb")
gtim_header = GtimTuple(*struct.unpack(GTIM_FMT, binary.read(GTIM_SIZE)))
print(gtim_header)

imag = chunk.Chunk(binary, align=False, bigendian=False)
imag_header = ImagTuple(*struct.unpack(IMAG_FMT, imag.read(IMAG_SIZE)))
print(imag_header)

PIXELSIZE = 2 # in bytes
PIXELBITS = PIXELSIZE * 8
ENDIANNESS = "little"
# Size of each color in bits, not the same for every file
BITS = (5, 6, 5, 0)
# Position of each color in the RGBA tuple
ORDER = (0, 1, 2, 3)

# Generate the bitmasks and shifts for reading the pixel values
# shift_r moves the bits to the lower end for masking and shift_l is used as a
# cheap way to upscale from 5 bit colors to 8 bit. It becomes very inaccurate at
# higher scaling factors and is completely unusable for 1 bit alpha. I should
# probably improve this (later).

masks = []
shifts_r = []
shifts_l = []
for bitn, bitc in enumerate(BITS):
    masks.append((1 << bitc) - 1)
    shifts_r.append(PIXELBITS - sum(BITS[:bitn + 1]))
    shifts_l.append(8 - bitc)

print(masks, shifts_r, shifts_l)

stream = imag

pixels = []
for i in range(stream.tell(), stream.getsize(), PIXELSIZE):
    px_bytes = stream.read(PIXELSIZE)
    # For broken images with red dots all over it
    #if px_bytes == b"\x66\xF8":
    #    continue
    px_int = int.from_bytes(px_bytes, ENDIANNESS)
    pixel = [0] * 4
    for mask, shift_r, shift_l, pos in zip(masks, shifts_r, shifts_l, ORDER):
        val = ((px_int >> shift_r) & mask) << shift_l
        pixel[pos] = val
    pixels.append(tuple(pixel))

width = imag_header.width
height = imag_header.height

img = PIL.Image.new("RGB", (width, height))
img.putdata(pixels)
img.save(filename_bmp)
