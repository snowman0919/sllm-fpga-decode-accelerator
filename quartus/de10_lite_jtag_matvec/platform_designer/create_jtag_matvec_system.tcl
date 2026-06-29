# Platform Designer setup checklist for the JTAG MatVec register path.
#
# This file is intentionally conservative. It documents the intended system
# rather than claiming that a .qsys has been generated in this repository state.
#
# Manual Platform Designer steps:
# 1. Create a new system clocked by CLOCK_50.
# 2. Add "JTAG to Avalon Master Bridge" (JTAG-to-Avalon Master IP).
# 3. Add or wrap the generated DecodeMatVecRegBank Avalon-MM slave.
# 4. Connect the master's data master interface to the register slave.
# 5. Connect clock/reset to both components.
# 6. Export optional debug LED/HEX signals or wrap them at top level.
# 7. Generate HDL and include it in the Quartus project.
#
# Expected register map is documented in docs/jtag_matvec_offload.md.
puts "JTAG MatVec Platform Designer checklist loaded. Create/generate the .qsys manually or extend this Tcl for your Quartus version."
