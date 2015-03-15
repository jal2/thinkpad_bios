#!/usr/bin/python

# This program dumps information from a SPI flash copy
# of a Lenovo Thinkpad X200 and can output the various regions
# defined in the descriptor table.
# It tries to do some basic consistency checks.

# This is based on the register description in
# "Intel 7 Series Chipset and Intel C216 Chipset SPI Programming Guide"
# ftp://ftp.nexcom.com/pub/Drivers/NDiSM532/ME/ME8_5M_8.0.13.1502/ME8_5M_8.0.13.1502/SPI%20Programming%20Guide.pdf

# copyright (c) Joerg Albert (<jal2@gmx.de>)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import getopt
import string

verbose = 0
outputname = ""
bios = []
signature = 0x0ff0a55a
frba = 0
nr_err = 0 # incremented for each error which prevents us from writing
# names of the regions
reg_names = [ "descriptor", "bios", "intelme", "gbe", "platform" ]
layoutname="" # if != "" write a flashrom layout file into this filename

def usage(name):
    print ('%s [-h] | [-w outputfile] [-l] inputfile' % name)

# get a 32 bit value (little endian!) from the bios field at offset
def get_u32(bios, offset):
    return bios[offset] | (bios[offset+1]<<8) | \
        (bios[offset+2]<<16) | bios[offset+3]<<24

# get a 16 bit value (little endian) from the bios field at offset
def get_u16(bios, offset):
    return bios[offset] | (bios[offset+1]<<8)

# sum up 16 bit values in a bios region
# start at byte offset start, sum up nr many u16 values 
def sum_u16(bios,start,nr):
    sum = 0
    for i in range(0,nr):
        sum += get_u16(bios,start+2*i)
    return sum

# look for signature and return its offset from start
def search_sig(bios,sig):
    for i in range(0,40,4):
        if get_u32(bios,i) == sig:
            return i
    return -1

#dump GbE info
def dump_gbe(p, f):
    print "%s MAC %02x-%02x-%02x-%02x-%02x-%02x" % (p, f[0],f[1],f[2],f[3],f[4],f[5])

# convert a three bit frequency encoding into a string
def freq(code):
    if code == 0:
        return "20 Mhz"
    if code == 1:
        return "33 Mhz"
    if code == 4:
        return "50 Mhz"
    return "invalid"

# convert a three bit density encoding into a string
def density(code):
        if code == 7:
            return 0
        if code == 0:
            return 512 * 1024
        return (1<<(code-1)) * 1024 * 1024 

def get_regs(bios, sigoff):
    global frba,nr_err
    flmap = (get_u32(bios, sigoff+4), get_u32(bios, sigoff+8), \
             get_u32(bios,sigoff+0xc))
    frba = ((flmap[0] >> 16) & 0xff)<<4
    fcba = (flmap[0] & 0xff)<<4
    fmba = (flmap[1] & 0xff)<<4
    fmsba = (flmap[2] & 0xff)<<4
    nr_comp = ((flmap[0] >> 8) & 3)+1
    print "FLMAPs: 0x%08x 0x%08x 0x%08x" % (flmap[0],flmap[1],flmap[2])
    print "FRBA 0x%x FCBA 0x%x FMBA 0x%x FMSBA 0x%x" % (frba,fcba,fmba,fmsba)
    print "number of components: %u" % (nr_comp)
    print "number of masters: %u" % ((flmap[1] >> 8) & 3)

    flcomp = get_u32(bios,fcba)
    print "frequencies: read %s write/erase %s fast read %s" % \
        (freq((flcomp>>27)&7), freq((flcomp>>24)&7), freq((flcomp>>21)&7))
    dens1 = density(flcomp&7)
    if nr_comp == 2:
        dens2 = density((flcomp>>3)&7)
        print "density: component_1 %u KB  component_2 %u KB" % \
            (dens1/1024, dens2/1024)
    else:
        dens2 = 0
        print "density: component_1 %u KB" % (dens1/1024)
    # check sum of densities against bios overall length
    if len(bios) != (dens1 + dens2):
        print "#ERR BIOS length 0x%x != sum(densities) 0x%x" % \
            (len(bios),dens1+dens2)
        nr_err += 1

# get the printable string at the start of the OEM
# part of the descriptor region (at offset 0xf00)
def get_oem_descr(bios):
    ret = ""
    for i in range(0xf00, 0xfff):
        c = chr(bios[i])
        if (c in string.printable):
            ret += c
        else:
            return ret

# get the region boundaries from a flash region X register
# name of the region is name
# return: (base,limit) # i.e. first and last offset of the region
def get_region(bios,nr):
    reg = get_u32(bios,frba+4*nr)
    base = (reg & 0x1fff)<<12
    limit = (reg & 0x1fff0000)>>4 | 0xfff
    return (base,limit)

try:
    opts,args = getopt.getopt(sys.argv[1:],"hvl:w:")
except getopt.GetoptError:
    usage(sys.argv[0])
    sys.exit(1)

for opt,arg in opts:
    if opt == '-h':
        usage(sys.argv[0])
        sys.exit()
    elif opt == '-v':
        verbose = verbose+1
    elif opt == '-w':
        outputname = arg
    elif opt == '-l':
        layoutname = arg

if len(args) < 1:
    print "#ERR missing input file"
    usage(sys.argv[0])
    sys.exit(2)

# read the input file and convert the char into their ASCII
ifile = open(args[0], 'r')
bios = map(ord,ifile.read())
sigoff = search_sig(bios, signature)
if sigoff == -1:
    print "#ERR signature 0x%08x not found" % (signature)
    sys.exit(3)

print "signature 0x%08x at offset 0x%x" % (signature,sigoff)
get_regs(bios, sigoff)
print "OEM string (@0xf00): %s" % (get_oem_descr(bios))

# dump the regions' limit
for i in range(0,len(reg_names)):
    (base,limit) = get_region(bios,i)
    # all regions > 0 must have a limit > 0xfff, otherwise they are unused 
    if i == 0 or limit != 0xfff:
        print " region %u (%11s): 0x%06x - 0x%06x" % (i,reg_names[i],base,limit)
        if limit > len(bios)-1:
            print "#ERR region %u (%s) end (0x%x) beyond EOF(0x%0x)" % \
                (i, reg_names[i], limit, len(bios)-1)
            nr_err += 1
    else:
        print " region %u (%11s): unused"

# dump some info about the GbE region
(base,limit) = get_region(bios,3)
if limit != 0xfff:
    chk1 = sum_u16(bios, base, 0x40) & 0xffff
    chk2 = sum_u16(bios, base+0x1000, 0x40) & 0xffff
    if chk1 == 0xbaba:
        dump_gbe("GbE1",bios[base:(base+0x80)])
    else:
        print "#WRG GbE first entry invalid checksum 0x%04x" % (chk1)
    if chk2 == 0xbaba:
        dump_gbe("GbE2",bios[(base+0x1000):(base+0x1040)])
    else:
        print "#WRG GbE second entry invalid checksum 0x%04x" % (chk2)

if nr_err > 0:
    print "#ERR not writing components or layout due to previous errors above"
    sys.exit(4)

if outputname != "":
# we write the components
    for i in range(0,len(reg_names)):
        (base,limit) = get_region(bios,i)
        if i == 0 or limit != 0xfff:
            ofile = open(outputname + "." + reg_names[i], "w")
            ofile.write(''.join(map(chr,bios[base:(limit+1)])))
            ofile.close()
        else:
            print "skipping unused region %s for output" % (reg_names[i])

if layoutname != "":
    ofile = open(layoutname, "w")
    for i in range(0,len(reg_names)):
        (base,limit) = get_region(bios,i)
        if i == 0 or limit != 0xfff:
            ofile.write("%08x:%08x %s\n" % (base,limit,reg_names[i]))
    ofile.close()
