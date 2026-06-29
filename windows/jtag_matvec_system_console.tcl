# Template/reference for the Python-generated JTAG MatVec System Console script.
#
# The runner fills in cable, base address, activation, and weight values at
# runtime. This template documents the expected commands and output shape.
#
# Expected stdout line:
# JTAG_MATVEC_RESULT seq=0 status=2 debug_status=2 compute_cycles=... core_total_cycles=... last_run_id=0 r0=-271 r1=239 r2=287 r3=797 elapsed_ms=...

proc signed32 {value} {
    set value [expr {$value & 0xffffffff}]
    if {$value >= 0x80000000} {
        return [expr {$value - 0x100000000}]
    }
    return $value
}

puts "Use windows/run_fpga_jtag_matvec.py to generate a concrete script with payload values."
