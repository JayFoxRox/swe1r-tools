#!/usr/bin/env python3

import sys
import struct
from PIL import Image

def read8(f):
  return f.read(1)[0]
def read16(f):
  return int.from_bytes(f.read(2), byteorder='big', signed=False)
def read32(f):
  return int.from_bytes(f.read(4), byteorder='big', signed=False)
def readFloat(f):
  return struct.unpack('>f', f.read(4))[0]

def lerp_s(a, b, t):
  return a * (1.0 - t) + b * t
def lerp(a, b, t):
  return (lerp_s(a[0], b[0], t), lerp_s(a[1], b[1], t), lerp_s(a[2], b[2], t))
  

with open(sys.argv[1], 'rb') as f:
  count = read32(f)
  for i in range(0, count - 1):
    f.seek(4 + 4 * i)
    a = read32(f)
    b = read32(f)
    length = b - a

    print("%d: a: 0x%08X b: 0x%08X (length: %d)" % (i, a, b, length))

    f.seek(a)
    buf = f.read(length)

    with open("/tmp/swep1r/spline-%d.bin" % i, 'wb') as t:
      t.write(buf)

    t = open("/tmp/swep1r/spline-%d.obj" % i, 'w')

    f.seek(a)

    read32(f) # [0]
    count = read32(f) # array count [4]
    read32(f) # [8]

    read32(f) # wtf?! skipping 4 byte?
  
    # some array [16]

    print("Next spline! (%d)" % count)
    for i in range(0, count):
      before = f.tell()
      print("")
      print("[%d]:" % i)

      # Number of elements in unk2[] array
      unk0 = read16(f)
      print("unk0: %d next-count" % unk0) # Read 1 x short [0]
      assert((unk0 == 0x0000) or (unk0 == 0x0001) or (unk0 == 0x0002))

      # Number of elements in unk3[] array (rest is garbage?)
      unk1 = read16(f)
      print("unk1: %d prev-count" % unk1) # Read 1 x short [2]
      assert((unk1 == 0x0000) or (unk1 == 0x0001) or (unk1 == 0x0002) or (unk1 == 0x0003))


      print("unk2[0]: %d next-index?" % read16(f)) # Read 2 x short [4]
      print("unk2[1]: %d" % read16(f)) 

      print("unk3[0]: %d prev-index?" % read16(f)) # Read 4 x short [8]
      print("unk3[1]: %d" % read16(f)) 
      print("unk3[2]: %d" % read16(f)) 
      print("unk3[3]: %d" % read16(f)) # unused

      #FIXME: Apply this scale after printing
      scale = 1.0 / 100.0
      pos = (readFloat(f) * scale, readFloat(f) * scale, readFloat(f) * scale)

      # Unknown because it's always the same constant
      normal = (readFloat(f), readFloat(f), readFloat(f))
      assert(normal == (0.0, 0.0, 1.0))

      print("position: %f %f %f" % pos) # Read 3 x dword [16]

      print("normal?: %f %f %f" % normal) # Read 3 x dword [28]

      # Next control point
      unka = (readFloat(f) * scale, readFloat(f) * scale, readFloat(f) * scale)
      print("next control point: %f %f %f" % unka) # Read 3 x dword [40]

      # Previous control point
      unkb = (readFloat(f) * scale, readFloat(f) * scale, readFloat(f) * scale)
      print("prev control point: %f %f %f" % unkb) # Read 3 x dword [52]

      # Next control point index?
      unk8 = read16(f)
      if unk0 == 0:
        assert(unk8 == i)
      print("unk8: %d (prev control point index?)" % unk8) # Read 1 x short [64]

      # Prev control point index?
      unk9_0 = read16(f)
      if unk1 == 0:
        assert(unk9_0 == i)
      print("unk9[0]: %d (next control point index?)" % unk9_0) # Read 8 x short [66]
      print("unk9[1]: %d" % read16(f))
      # Unused
      for j in range(2, 8):
        unk9_x = read16(f)
        print("unk9_garbage[%d]: 0x%04X" % (j, unk9_x))
        assert(unk9_x == 0xFFFF)

      # Garbage? Padding?
      print("unk10: 0x%04X" % read16(f))

      after = f.tell()
      assert((after - before) == 84)
      # ???
      # = 84

      if False:
        bezier_steps = 30
        for j in range(0, bezier_steps):
          m = j / (bezier_steps - 1)
          posx = (pos[0], pos[1], pos[2] + 10.0)
          pa = lerp(unka, posx, m)
          pb = lerp(posx, unkb, m)
          p = lerp(pa, pb, m)
          t.write("v %f %f %f\n" % p)
      else:
        bezier_steps = 1
        t.write("v %f %f %f\n" % pos)


    for i in range(0, count * bezier_steps * 2 - 2):
      #FIXME: Can we include a normal like %d//%d ?
      t.write("l %d %d %d\n" % (i + 1, i + 2, i + 3))

    t.close()

    assert(f.tell() - a == b - a)
