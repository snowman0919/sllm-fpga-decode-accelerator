# Quartus Clean Rebuild Notes

## Issue

An earlier Windows clean compile attempt reported:

```text
Top-level design entity "de10_lite_jtag_matvec" is undefined
```

The Quartus project and revision are named `de10_lite_jtag_matvec`, but the real
board wrapper module is `De10LiteJtagMatVecTop`.

## Fix

The checked-in QSF now keeps the project/revision name separate from the top
entity:

```text
set_global_assignment -name TOP_LEVEL_ENTITY De10LiteJtagMatVecTop
```

It also uses project-relative source assignments instead of Linux absolute
paths:

```text
set_global_assignment -name VERILOG_FILE "De10LiteJtagMatVecTop.v"
set_global_assignment -name QIP_FILE "platform_designer/jtag_matvec_system/synthesis/jtag_matvec_system.qip"
set_global_assignment -name SDC_FILE "de10_lite_jtag_matvec.sdc"
```

`quartus/de10_lite_jtag_matvec/scripts/create_project.tcl` was updated to
regenerate those relative assignments.

A second clean-archive compile check confirmed that the top entity was resolved
correctly, but failed because Platform Designer synthesis files were not present
in the archive:

```text
Tcl Script File platform_designer/jtag_matvec_system/synthesis/jtag_matvec_system.qip not found
Node instance "system_inst" instantiates undefined entity "jtag_matvec_system"
```

The clean rebuild source set therefore includes the generated Platform Designer
`jtag_matvec_system.qsys`, `.sopcinfo`, `.cmp`, QIP, and synthesis submodules.
These files are source rebuild inputs for the Windows-only Quartus compile path.

## Windows Command

```powershell
cd C:\Users\dbsgu\Dev\sllm_fpga_board_eval\repo\quartus\de10_lite_jtag_matvec
quartus_sh.exe --flow compile de10_lite_jtag_matvec
```

Record the compile result here after each clean Windows rebuild. Do not mark a
clean rebuild as successful unless Quartus exits successfully and creates a new
`.sof`.

## 2026-06-30 Windows Clean Archive Rebuild

Host: Pocket4

Command:

```powershell
cd C:\Users\dbsgu\Dev\sllm_fpga_clean_rebuild_test\repo\quartus\de10_lite_jtag_matvec
quartus_sh.exe --flow compile de10_lite_jtag_matvec
```

Result:

```text
Quartus Prime Full Compilation was successful. 0 errors, 45 warnings
Quartus Prime Shell was successful. 0 errors, 45 warnings
```

Generated file:

```text
quartus\de10_lite_jtag_matvec\output_files\de10_lite_jtag_matvec.sof
SHA-256: c78fc674229763bf202eeac5303212bf621f54533130ba7b82d30d18d0b7bcc1
```

This confirmed clean source rebuild reproducibility for the Quartus project in
the isolated test directory. It did not itself replace the prior board-measured
JTAG log.

## 2026-06-30 Primary Windows Clean Rebuild Board Run

Host: Pocket4

Source delivery:

```text
git push succeeded from Linux.
Windows working directory was not a git checkout, so current HEAD 70953945 was
transferred as a git archive to C:\Users\dbsgu\Dev\sllm_fpga_board_eval\repo.
```

Command:

```powershell
cd C:\Users\dbsgu\Dev\sllm_fpga_board_eval\repo\quartus\de10_lite_jtag_matvec
quartus_sh.exe --flow compile de10_lite_jtag_matvec
```

Result:

```text
Quartus Prime Full Compilation was successful. 0 errors, 45 warnings
Quartus Prime Shell was successful. 0 errors, 45 warnings
```

Generated and programmed file:

```text
quartus\de10_lite_jtag_matvec\output_files\de10_lite_jtag_matvec.sof
SHA-256: 40a4f84167d2fd75972ea33684ec949b6c22e61057f1c134dd5bd4b936ef4a84
```

Programming result:

```text
Configuration succeeded -- 1 device(s) configured
Successfully performed operation(s)
```

System Console master service:

```text
/devices/10M50DA(.|ES)|10M50DC@1#USB-0/(link)/JTAG/(110:132 v1 #0)/phy_0/master
```

JTAG cycle-counter benchmark:

```text
pass_count=20
fail_count=0
reference=-271 239 287 797
result=-271 239 287 797
COMPUTE_CYCLES mean/p50/p95=65.0/65.0/65.0
compute_time_us_50mhz mean/p50/p95=1.3/1.3/1.3
JTAG total latency mean/p50/p95=7720.85016/7720.45115/7748.84833 ms
```

This clean rebuild run is now the primary board-measured evidence. The prior
passing board-run SHA-256
`3b4f2cb50d5aa5608019c550f29b42779ff9c7197383d58cf3132c0bdd635cc5` is preserved
as a historical prior run.
