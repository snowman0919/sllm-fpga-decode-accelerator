# QSF Notes

`de10_lite_pins.qsf` contains the DE10-Lite pin assignments used by the JTAG Decode MatVec clean rebuild.

The checked-in project QSF sources this file with a project-relative path:

```tcl
source qsf/de10_lite_pins.qsf
```

The JTAG path itself uses USB-Blaster and JTAG-to-Avalon Master IP inside Platform Designer; it does not require external UART RX/TX GPIO assignments.
