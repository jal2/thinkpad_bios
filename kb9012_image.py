#!/usr/bin/python

# This program tries to locate an ENE KB9012 image (8051) in a binary file
# and may extract it.
#
# We look for certain values in the interrupt vector table and at the end of the table:
# offset      value      vector    remark
# 0x00000      0x02       reset     ljmp
# 0x0000b      0x02       timer0    ljmp
# 0x00013      0xe0       extint1   movx a,@dptr
# 0x0001b      0xef       timer1    mov a,r7
# 0x00023      0xd3       serial    setb c
# 0x0002b      0x37       timer2    addc a,@r1
# 0x1ff00      0xff        -        last 0x100 byte of the image shall be 0xff
#
# copyright (c) 2016 Joerg Albert (<jal2@gmx.de>)

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

# fixed image length
image_len=128*1024
verbose = 0
outputname = ""
bios = []
# table of offsets and byte values to match
# each tupel: (offset, list of byte values)
matches = [ (0,[2]), (0xb,[2]), (0x13,[0xe0]), (0x1b,[0xef]), (0x23, [0xd3]), (0x2b,[0x37]), (0x1ff00,0x100 * [0xff]) ]

def usage(name):
    print ('%s [-h] | [-w outputfile] inputfile' % name)

try:
    opts,args = getopt.getopt(sys.argv[1:],"hw:")
except getopt.GetoptError:
    usage(sys.argv[0])
    sys.exit(1)

for opt,arg in opts:
    if opt == '-h':
        usage(sys.argv[0])
        sys.exit()
    elif opt == '-w':
        outputname = arg

if len(args) < 1:
    print "#ERR missing input file"
    usage(sys.argv[0])
    sys.exit(2)

# read the input file and convert the char into their ASCII
ifile = open(args[0], 'r')
bios = map(ord,ifile.read())
ifile.close()
bios_len = len(bios)

if len(bios) < image_len:
    print "#ERR input image too short"
    sys.exit(3)

for offset in range(0,bios_len - image_len + 1):

#    if offset % 0x10000 == 0:
#        print "#DBG offset 0x%x" % (offset)

# try each offset

#check all matches
    match=1
    for (o,l) in matches:
        if bios[offset+o:(offset+o+len(l))] != l:
           match=0
           break
    if match == 1:
        # image at offset  matches whole list
        print "ENE KB9012 image at offset 0x%x" % (offset)
        if outputname != "":
            ofile = open(outputname, "w")
            ofile.write(''.join(map(chr,bios[offset:(offset+image_len)])))
            ofile.close()
# we only break after the first match if -w was given
# so we find multiple matches without -w
            break



    
