# 재현 가이드

이 저장소는 Linux/Nix와 Windows Pocket4의 역할을 분리한다. Windows에는 Nix가 없으므로, 생성과 검증은 Linux/Nix에서 수행하고 Windows는 Quartus와 실제 DE10-Lite board run에만 사용한다.

## Linux/Nix 역할

Linux/Nix machine에서 수행한다.

- SpinalHDL Verilog 생성
- register-bank RTL simulation
- Python script 검증
- ONNX Runtime CPU / `MatMulInteger` micrograph baseline 생성
- Quartus report extraction 검증
- 논문용 표/그림 생성
- generated dist package 생성과 검증
- git commit/push

권장 흐름:

```bash
nix develop -c just fpga-jtag-verilog
nix develop -c just fpga-jtag-regbank-sim
python scripts/build_ort_fpga_comparison.py
python scripts/build_dist_package.py
python scripts/verify_dist_package.py
```

한 번에 준비하려면:

```bash
nix develop -c just fpga-linux-prepare
nix develop -c just fpga-paper-package
```

## Windows Pocket4 역할

Windows Pocket4에서는 다음만 수행한다.

- `git pull` 또는 Linux에서 만든 archive 수신
- Quartus clean compile
- `.sof` programming
- System Console JTAG-to-Avalon service 확인
- JTAG cycle-counter benchmark 실행
- board log 회수 또는 commit/push

Windows 단계에는 `nix develop`을 넣지 않는다.

## Quartus clean rebuild

Quartus project/revision 이름은 `de10_lite_jtag_matvec`이고, 실제 Verilog top entity는 `De10LiteJtagMatVecTop`이다. QSF에는 다음 설정이 있어야 한다.

```text
set_global_assignment -name TOP_LEVEL_ENTITY De10LiteJtagMatVecTop
```

Windows에서:

```powershell
cd quartus\de10_lite_jtag_matvec
quartus_sh.exe --flow compile de10_lite_jtag_matvec
```

성공 기준:

```text
Quartus Prime Full Compilation was successful. 0 errors
```

현재 primary rebuild는 0 errors, 45 warnings로 성공했고, 생성된 `.sof` SHA-256은 다음과 같다.

```text
40a4f84167d2fd75972ea33684ec949b6c22e61057f1c134dd5bd4b936ef4a84
```

## FPGA programming

```powershell
cd ..\..
quartus_pgm.exe -m jtag -c "USB-Blaster [USB-0]" -o "p;quartus\de10_lite_jtag_matvec\output_files\de10_lite_jtag_matvec.sof"
```

성공 기준:

```text
Configuration succeeded -- 1 device(s) configured
Successfully performed operation(s)
```

## System Console service 확인

다음 Tcl을 실행해 master service path가 보이는지 확인한다.

```tcl
puts "SERVICES_BEGIN"
puts [get_service_paths master]
puts "SERVICES_END"
exit
```

예상 System Console path:

```text
C:\altera_lite\25.1std\quartus\sopc_builder\bin\system-console.exe
```

`SERVICES_BEGIN`과 `SERVICES_END` 사이가 비어 있으면 JTAG-to-Avalon master가 잡히지 않은 것이므로 measured evidence로 승격하지 않는다.

## JTAG cycle-counter benchmark

```powershell
py -3 windows\run_fpga_jtag_matvec.py --runs 20 --cable "USB-Blaster [USB-0]" --quartus-bin "C:\altera_lite\25.1std\quartus\sopc_builder\bin\system-console.exe" --keep-tcl --log-dir logs\jtag_cycle_counter_clean_rebuild_final
```

성공 기준:

- `pass_count = 20`
- `fail_count = 0`
- `reference = -271 239 287 797`
- `result = -271 239 287 797`
- `compute_cycles_mean = 65`
- `compute_time_us_50mhz_mean = 1.3`
- `debug_status`가 run row에 존재

JTAG total latency는 기록만 한다. 이 값은 FPGA compute latency가 아니라 host-tool invocation overhead이다.

## Windows ORT integer baseline

선택적으로 board-control host에서 같은 primitive baseline을 실행한다.

```powershell
py -3 windows\run_ort_matvec_integer_baseline.py --runs 1000 --log-dir logs\ort_integer_baseline_board_env
```

현재 논문에 쓰는 baseline:

```text
mean/p50/p95 = 13.012 / 11.0 / 17.3 us
```

## 실패 처리 원칙

다음 경우에는 board-measured result로 승격하지 않는다.

- Quartus compile 실패
- FPGA programming 실패
- System Console master service 없음
- JTAG register read/write 실패
- `pass_count < runs`
- `fail_count > 0`
- reference/result 불일치
- `COMPUTE_CYCLES` 누락

실패 로그는 진단 자료로만 보존하고, 논문 표에는 measured로 반영하지 않는다.
