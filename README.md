# thinkpad_bios
A tool to print info from a Thinkpad BIOS dump and to split it into its regions

## Description
If you have a dump of the SPI flash of a Lenovo Thinkpad
(newer than T4x I guess) you may try this tool and get some info about
the different regions of the flash (descriptor table, BIOS, Intel ME,
GbE and platform data).

You may also write the various regions into different binary files.

You really need a dump from the SPI flash device, a compressed BIOS file
from the manufacturer won't do.

I've tested it with two dumps from a Thinkpad X200s initially.

This program may work with BIOS dumps from other manufacturers or brands,
please try and tell me.

## Examples
- show a short help text:

    ./tp_bios.py -h

- dump register information and do some basic consistency check on BIOS dump in bios.bin:

    ./tp_bios.py bios.bin

- additionally write the different regions to the files out.{descriptor,bios,intelme,platform,gbe}:

    ./tp_bios.py -w out bios.bin

- write a layout file which may be used by flashrom into layout:

    ./tp_bios.py -l layout bios.bin


## Example Output
    ./tp_bios.py X200s.bin
    signature 0x0ff0a55a at offset 0x0
    FLMAPs: 0x04040001 0x02100206 0x00000120
    FRBA 0x40 FCBA 0x10 FMBA 0x60 FMSBA 0x200
    number of components: 1
    number of masters: 2
    frequencies: read 20 Mhz write/erase 20 Mhz fast read 33 Mhz
    density: component_1 8192 KB
    OEM string (@0xf00): 7UR512WW
    region 0 ( descriptor): 0x000000 - 0x000fff
    region 1 (       BIOS): 0x600000 - 0x7fffff
    region 2 (    IntelME): 0x001000 - 0x5f5fff
    region 3 (        GbE): 0x5f6000 - 0x5f7fff
    region 4 (   platform): 0x5f8000 - 0x5fffff

 The output starts with some internal register content.
 The number of components is the number of SPI flash devices used in the hardware (1 or 2). If this is 2, you must dump two flash devices.
 Density is the size of each component. OEM string may be Lenovo specific. For each region the number, name and first and last offset
 in the flash is given.
 
## Disclaimer

You use this tool on your own risk! If you use it to eventually create a new binary file to flash into the BIOS device,
please check twice, as a bad BIOS may in the worst case permanently damage your hardware.

## Application Example
A while ago I got a Thinkpad X200s which showed a ten minutes delay between power on and the BIOS welcome screen. BIOS up- and downgrade didn't help.
As Windows' ME driver failed as well, we assumed that the IntelME firmware in the SPI flash got corrupted. Apart from the problems before, everything
else worked fine - the X200s booted Windows or Linux, just with a ten minutes delay.

These steps solved the problem:

1. install a matching Lenovo BIOS on a Linux PC using wine and find the matching *.FL1 - this contains the compressed BIOS
2. uncompress the *.FL1 file with the tool e_bcpvpw.exe (with wine :-) yielding a *.wph file
3. Take the first 0x800000 bytes from the .wph file. This is a SPI image, which can be processed by tp_bios.py, but the GbE and platform section are invalid.
4. Unsolder the SPI flash from the X200s (maybe not necessary, but we had problems to reliably contact the pins of the WSON package)
5. Update the IntelME section of the SPI IC with the one extracted from the .wph file, thereby keeping the GbE and platform sections. We used a RaspberryPi and the flashrom program.
6. Solder the IC back into the X200s. Actually we replaced it with a SO-IC8 device to be able to contact the pins more easily in the future.


## Links
* flashrom tool (http://flashrom.org/Flashrom) - I've used it with a Bus Pirate and a Raspberry PI to dump the SPI flash.
* "Intel 7 Series Chipset and Intel C216 Chipset SPI Programming Guide" (ftp://ftp.nexcom.com/pub/Drivers/NDiSM532/ME/ME8_5M_8.0.13.1502/ME8_5M_8.0.13.1502/SPI%20Programming%20Guide.pdf) - contains a description of the flash descriptor section
* UEFITool (https://github.com/LongSoft/UEFITool/) - much more powerful tool which delivers the above information as well
* Phoenix Tools (http://forums.mydigitallife.info/threads/13194-Tool-to-Insert-Replace-SLIC-in-Phoenix-Insyde-Dell-EFI-BIOSes) to deal with pre-UEFI Lenovo BIOS files. This contains, among many other tools, the one to uncompress a BIOS .FL1 file into a .WPH
* Libreboot notes on X200 with a lot of links: http://www.libreboot.org/docs/hcl/x200_remove_me.html
* "Intel® I/O Controller Hub 9M/82567LF/LM/V NVM Map and Information Guide" (http://www.intel.co.uk/content/dam/doc/application-note/i-o-controller-hub-9m-82567lf-lm-v-nvm-map-appl-note.pdf) - page 8 describes the layout of the GbE region
* Endeer's Phoenix BIOS tools: http://www.endeer.cz/bios.tools/
