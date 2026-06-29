# ONNX Runtime sLLM Decode FPGA 가속기 구조 실험

이 저장소는 논문 **「ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계」**의 재현용 저장소이다.

핵심은 간단하다. ONNX Runtime profiling으로 decode 단계의 MatMul/projection 계열 병목을 확인하고, 그 병목을 바로 전체 모델 가속으로 과장하지 않고, **fixed 16x4 INT8 Decode MatVec primitive** 하나로 좁혀 DE10-Lite FPGA에서 실제 board-measured cycle counter로 검증했다.

## 이 저장소의 목적

- ONNX export, graph inspection, ONNX Runtime profiling 결과를 논문 근거로 정리한다.
- PyTorch host baseline과 ONNX Runtime evidence를 섞지 않는다.
- SpinalHDL 기반 Decode MatVec primitive와 JTAG-to-Avalon register wrapper를 제공한다.
- Windows Pocket4 + DE10-Lite에서 얻은 board-measured `COMPUTE_CYCLES` 값을 보존한다.
- 논문, 최종 표/그림, 재현 스크립트를 검토자가 빠르게 따라갈 수 있게 둔다.

## 핵심 결과

Primary board evidence는 Windows clean rebuild로 생성한 bitstream 기준이다.

```text
quartus/de10_lite_jtag_matvec/output_files/de10_lite_jtag_matvec.sof
SHA-256: 40a4f84167d2fd75972ea33684ec949b6c22e61057f1c134dd5bd4b936ef4a84
```

| 항목 | 값 |
| --- | ---: |
| FPGA primitive | fixed 16x4 INT8 Decode MatVec |
| board run | `pass_count=20`, `fail_count=0` |
| reference/result | `-271 239 287 797` / `-271 239 287 797` |
| FPGA internal compute | `65 cycles = 1.3 us @ 50 MHz` |
| ORT MatMulInteger baseline | mean/p50/p95 = `13.012 / 11.0 / 17.3 us` |
| JTAG total invocation | mean/p50/p95 = `7720.85016 / 7720.45115 / 7748.84833 ms` |

JTAG total invocation latency는 System Console 실행, JTAG service 접근, register write/read, polling을 포함한 **host-tool invocation overhead**이다. FPGA compute latency가 아니다.

## 이 저장소가 주장하지 않는 것

- Gemma 3 1B 전체를 DE10-Lite에서 실행했다는 주장
- ONNX Runtime 전체 모델의 end-to-end 가속 주장
- sLLM inference 전체 speedup 주장
- JTAG total latency를 FPGA compute latency로 해석하는 주장
- projected interface estimate를 board-measured latency로 해석하는 주장

허용되는 해석은 **동일한 16x4 INT8 Decode MatVec primitive 조건에서 FPGA 내부 cycle counter가 65 cycles, 1.3 us @ 50 MHz를 보였다**는 것이다.

## 저장소 구조

| 경로 | 역할 |
| --- | --- |
| `paper/current/manuscript.md` | canonical 논문 원고 |
| `paper_assets/tables/` | 논문에 들어가는 최종 CSV 표 |
| `paper_assets/figures/` | 논문에 들어가는 최종 그림 |
| `docs/01_실험_근거와_주장_범위.md` | 측정 근거, claim boundary, 수치 해석 |
| `docs/02_재현_가이드.md` | Linux/Nix와 Windows Pocket4 재현 절차 |
| `docs/03_저장소_구조.md` | main/examine 역할과 artifact 정책 |
| `hw/spinal/` | SpinalHDL source와 simulation |
| `quartus/de10_lite_jtag_matvec/` | DE10-Lite JTAG-to-Avalon clean rebuild project |
| `windows/` | Windows board run 및 host baseline runner |
| `scripts/` | 표/그림/dist package 생성 및 검증 script |
| `logs/` | compact board manifest만 유지 |

## 논문

canonical manuscript:

```text
paper/current/manuscript.md
```

검토 순서는 보통 다음이 가장 빠르다.

1. 이 `README.md`
2. `paper/current/manuscript.md`
3. `paper_assets/tables/fpga_jtag_cycle_counter_summary.csv`
4. `paper_assets/tables/ort_vs_fpga_measured_and_projected_comparison.csv`
5. `docs/02_재현_가이드.md`

## 재현 방법

Windows에는 Nix를 쓰지 않는다. 개발/생성/검증은 Linux/Nix에서, Quartus compile과 실제 board run은 Windows Pocket4에서 수행한다.

### Linux/Nix

```bash
nix develop -c just fpga-jtag-verilog
nix develop -c just fpga-jtag-regbank-sim
python scripts/build_ort_fpga_comparison.py
python scripts/build_dist_package.py
python scripts/verify_dist_package.py
```

### Windows Pocket4 + DE10-Lite

```powershell
cd quartus\de10_lite_jtag_matvec
quartus_sh.exe --flow compile de10_lite_jtag_matvec
cd ..\..
quartus_pgm.exe -m jtag -c "USB-Blaster [USB-0]" -o "p;quartus\de10_lite_jtag_matvec\output_files\de10_lite_jtag_matvec.sof"
py -3 windows\run_fpga_jtag_matvec.py --runs 20 --cable "USB-Blaster [USB-0]" --quartus-bin "C:\altera_lite\25.1std\quartus\sopc_builder\bin\system-console.exe" --keep-tcl --log-dir logs\jtag_cycle_counter_clean_rebuild_final
```

자세한 절차는 `docs/02_재현_가이드.md`에 있다.

## 근거 파일

- Primary board manifest: `logs/jtag_cycle_counter_clean_rebuild_final/BOARD_RUN_MANIFEST.md`
- Historical prior board manifest: `logs/remote_board_eval/BOARD_RUN_MANIFEST.md`
- FPGA cycle counter table: `paper_assets/tables/fpga_jtag_cycle_counter_summary.csv`
- FPGA JTAG primitive table: `paper_assets/tables/fpga_jtag_primitive_benchmark.csv`
- ORT integer baseline table: `paper_assets/tables/onnx_runtime_integer_micrograph_baseline.csv`
- Measured/projected comparison: `paper_assets/tables/ort_vs_fpga_measured_and_projected_comparison.csv`
- Quartus resource/timing: `paper_assets/tables/quartus_resource_timing_summary.csv`

## examine 브랜치

`main`은 논문 검토자용 최소 구조이다. Raw profile JSON, raw board logs, legacy Quartus projects, diagnostic notes, generated dist package copy는 `examine` 브랜치에 보존되어 있다.

```bash
git switch examine
```

`main`에서 파일이 보이지 않는다는 것은 증거를 버렸다는 뜻이 아니라, 검토 흐름을 방해하는 raw trace를 별도 보존 브랜치로 옮겼다는 뜻이다.
