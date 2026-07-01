# 실험 근거와 주장 범위

이 문서는 논문에서 사용할 수 있는 측정 근거와 사용할 수 없는 주장을 한곳에 모은다. 핵심 원칙은 단순하다. **측정된 것은 측정된 범위 안에서만 말한다.**

## 현재 주장할 수 있는 것

- ONNX export, graph inspection, ONNX Runtime profiling으로 decode-stage MatMul/projection 계열 병목을 분석했다.
- PyTorch 결과는 host-side reference baseline으로만 사용한다.
- FPGA 결과는 fixed 16x4 INT8 Decode MatVec primitive 검증이다.
- DE10-Lite에서 JTAG-to-Avalon register path로 primitive를 호출했고 CPU reference와 같은 결과를 얻었다.
- FPGA 내부 primitive compute latency는 board-measured `COMPUTE_CYCLES` register로 측정했다.
- Optimized interface row는 measured result가 아니라 projected interface estimate이다.

## 주장하지 않는 것

- Gemma 3 1B 전체를 DE10-Lite에서 실행했다는 주장
- ONNX Runtime 전체 모델의 전체 실행 acceleration 주장
- sLLM inference 전체 속도 향상 주장
- JTAG offload를 performance-optimized accelerator interconnect로 보는 주장
- JTAG total latency를 FPGA compute latency로 해석하는 주장
- projected estimate를 measured board latency로 해석하는 주장
- Process RSS delta를 KV-cache allocation 직접 측정값으로 보는 주장

## Primary board evidence

현재 primary board-measured evidence는 Windows clean rebuild bitstream 기준이다.

| 항목 | 값 |
| --- | --- |
| bitstream | `quartus/de10_lite_jtag_matvec/output_files/de10_lite_jtag_matvec.sof` |
| SHA-256 | `40a4f84167d2fd75972ea33684ec949b6c22e61057f1c134dd5bd4b936ef4a84` |
| board | DE10-Lite / MAX 10 |
| host | Windows Pocket4 |
| cable | USB-Blaster `[USB-0]` |
| runs | 20 |
| pass/fail | `20 / 0` |
| reference | `-271 239 287 797` |
| result | `-271 239 287 797` |
| `COMPUTE_CYCLES` mean/p50/p95 | `65 / 65 / 65` |
| compute time at 50 MHz | `1.3 us / 1.3 us / 1.3 us` |
| JTAG total latency mean/p50/p95 | `7720.85016 / 7720.45115 / 7748.84833 ms` |

이전 passing board-run SHA-256 `3b4f2cb50d5aa5608019c550f29b42779ff9c7197383d58cf3132c0bdd635cc5`는 historical prior run으로만 보존한다.

## ORT baseline과 FPGA internal compute 비교

동일한 fixed 16x4 INT8 Decode MatVec primitive 조건에서 Windows board host의 ONNX Runtime `MatMulInteger` micrograph baseline은 다음과 같다.

| 항목 | mean | p50 | p95 |
| --- | ---: | ---: | ---: |
| ORT `MatMulInteger` baseline | `13.012 us` | `11.0 us` | `17.3 us` |
| FPGA internal cycle counter | `1.3 us` | `1.3 us` | `1.3 us` |

이 비교는 primitive internal compute latency 비교이다. ONNX Runtime 전체 모델 실행 시간이나 custom operator 통합 성능을 뜻하지 않는다.

## JTAG total latency 해석

JTAG-to-Avalon total latency는 FPGA 연산부의 순수 처리 시간이 아니다. 이 값에는 다음이 포함된다.

- System Console 실행
- JTAG service 접근 또는 초기화
- register write/read
- polling
- host tool process overhead

따라서 JTAG total latency는 **host-tool invocation overhead**로만 표기한다. 논문에서 FPGA compute latency 근거로 사용하는 값은 `COMPUTE_CYCLES=65`와 `1.3 us @ 50 MHz`뿐이다.

## Quartus resource/timing summary

Clean rebuild bitstream의 Quartus resource/timing 요약은 다음과 같다.

| 항목 | 값 |
| --- | ---: |
| target device | `10M50DAF484C7G` |
| logic elements | `2,560 / 49,760 (5%)` |
| registers | `1,450 / 49,760 (3%)` |
| memory bits | `512 / 1,677,312 (<1%)` |
| DSP 9-bit elements | `1 / 288 (<1%)` |
| Fmax | `56.670 MHz` |
| worst setup/hold slack | `2.353 ns / 0.094 ns` |
| timing met | `True` |

세부 값은 `paper_assets/tables/quartus_resource_timing_summary.csv`에 있다.

## 근거 파일

- `logs/jtag_cycle_counter_clean_rebuild_final/BOARD_RUN_MANIFEST.md`
- `logs/remote_board_eval/BOARD_RUN_MANIFEST.md`
- `paper_assets/tables/fpga_jtag_cycle_counter_summary.csv`
- `paper_assets/tables/fpga_jtag_primitive_benchmark.csv`
- `paper_assets/tables/onnx_runtime_integer_micrograph_baseline.csv`
- `paper_assets/tables/ort_vs_fpga_measured_and_projected_comparison.csv`
- `paper_assets/tables/quartus_resource_timing_summary.csv`
