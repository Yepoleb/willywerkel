import struct
import os
import sys
from collections import namedtuple

"""
UpPackage Format

Each UpPackage has 3 meta sections: directories, strings and files. I start with
reading the strings section. It contains zero terminated strings that are later
referenced by the directories and files. "directories" contains an offset in 
"strings" for the name, the number of files in it and an offset in "files" for 
the contents. Follow that offset and read the number of entries. The file 
"name_ofs" has to be combined with the directory "name_ofs" to get the final 
path. The data offset for files is from the package start, not any section.
"""

HEADER_FMT = "<4s7L"
HEADER_SIZE = struct.calcsize(HEADER_FMT) # 32
INFO_FMT = "<6L"

HeaderTuple = namedtuple("Header", ["magic", "version", "dirs_size", "dirs_ofs", 
    "strings_size", "strings_ofs", "files_size", "files_ofs"])
InfoTuple = namedtuple("Info", ["unk1", "name_ofs", "null", "size1", "size2", "offset"])
FileTuple = namedtuple("File", ["name", "offset", "size"])
DirTuple = namedtuple("Directory", ["path", "offset", "entries"])

def cstring_at(data, pos):
    """Read cstring at position in bytes object"""
    end = data.find(b'\0', pos)
    return data[pos:end].decode("ASCII")


if len(sys.argv) < 2:
    print("Usage: {} <file.up>".format(sys.argv[0]))
    exit(1)

binary = open(sys.argv[1], "rb")
header_bytes = binary.read(HEADER_SIZE)
header = HeaderTuple(*struct.unpack(HEADER_FMT, header_bytes))
if not header.magic == b"UDSP":
    print("File not UpPackage")

print("Magic: {}".format(header.magic.decode("ASCII")))
print("Version: {}".format(header.version))
print("Directories: {} bytes at {:x}".format(header.dirs_size, header.dirs_ofs))
print("Files: {} bytes at {:x}".format(header.files_size, header.files_ofs))
print("Strings: {} bytes at {:x}".format(header.strings_size, header.strings_ofs))

# Read strings section
binary.seek(header.strings_ofs)
strings_bytes = binary.read(header.strings_size)

# Read directories
binary.seek(header.dirs_ofs)
dir_bytes = binary.read(header.dirs_size)
dirstructs = [InfoTuple(*x) for x in struct.iter_unpack(INFO_FMT, dir_bytes)][1:]
dirs = []
for dirstruct in dirstructs:
    name = cstring_at(strings_bytes, dirstruct.name_ofs)
    directory = DirTuple(name, dirstruct.offset, dirstruct.size2)
    dirs.append(directory)

for direntry in dirs:
    print(direntry)

# Read files
filetree = {}
for directory in dirs:
    filetree[directory.path] = []
    binary.seek(header.files_ofs + directory.offset)
    files_bytes = binary.read(directory.entries * 0x18)
    filestructs = [InfoTuple(*x) for x in struct.iter_unpack(INFO_FMT, files_bytes)]
    for filestruct in filestructs:
        name = cstring_at(strings_bytes, filestruct.name_ofs)
        fileentry = FileTuple(name, filestruct.offset, filestruct.size1)
        filetree[directory.path].append(fileentry)

# Export files
for path in sorted(filetree.keys()):
    unix_path = path.replace('\\', '/')
    os.makedirs(unix_path, exist_ok=True)
    for fileentry in filetree[path]:
        print(hex(fileentry.offset), fileentry.size, path + '\\' + fileentry.name)
        binary.seek(fileentry.offset)
        data = binary.read(fileentry.size)
        with open(unix_path + '/' + fileentry.name, "wb") as f:
            f.write(data)
