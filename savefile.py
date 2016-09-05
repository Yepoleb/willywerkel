import chunk
import struct
from collections import namedtuple

"""
Format: IFF

MISS - Mission status
INVI - Inventory items
PHOT - Map photo progress
DIPL - Diplomas
BARN - Hangar parts?
AIRP - 2 or 4 byte ints describing airplane part numbers
"""

DIPLOMA_NAMES = ["Water", "Snow", "Racing", "Circus", "Map", "Mecci"]

ChunkTuple = namedtuple("Chunk", ["name", "size", "data"])

def get_chunks(chunks, name):
    return filter(lambda c: c.name == name, chunks)



save = open("user0.dat", "rb")

form = chunk.Chunk(save, align=False, bigendian=True)
chunks = []

# USERNAME is special because it has 8 bytes long name. Definitely worth
# breaking the format for the nice suffix
form.seek(8, 1) # Skip chunk name
username_len = int.from_bytes(form.read(4), "big")
username = form.read(username_len)
chunks.append(ChunkTuple(b"USERNAME", username_len, username))

while form.tell() < form.getsize():
    ch = chunk.Chunk(form, align=False, bigendian=True)
    data = ch.read()
    chunks.append(ChunkTuple(ch.getname(), ch.getsize(), data))

# Inventory
invis = get_chunks(chunks, b"INVI")
inventory = []
for invi in invis:
    inventory.append(invi.data.rstrip(b'\0').decode("ASCII"))
print("Inventory:", inventory)
print()

# Diplomas
dipl = next(get_chunks(chunks, b"DIPL"))
dipl_vals = [bool(x[0]) for x in struct.iter_unpack("<L", dipl.data)]
print("Diplomas:")
for dipl_name, dipl_done in zip(DIPLOMA_NAMES, dipl_vals):
    print("{}: {}".format(dipl_name, dipl_done))
print()

# Missions
missions = get_chunks(chunks, b"MISS")
print("Missions:")
for miss in missions:
    values = list(x[0] for x in struct.iter_unpack("<L", miss.data))
    print(values)
    
