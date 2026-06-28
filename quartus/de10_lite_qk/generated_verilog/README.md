# Quartus Import Mirror

This directory mirrors the canonical SpinalHDL outputs from `hw/spinal/generated/`.

Expected files after `just spinal-generate`:

- `DotProductInt8_dim16.v`
- `HexDisplay.v`
- `De10LiteTop.v`

Quartus project Tcl scripts consume this mirror so that the Quartus-side flow stays self-contained.
