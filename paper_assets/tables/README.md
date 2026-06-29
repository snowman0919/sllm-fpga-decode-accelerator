# Paper Tables

논문과 README/docs에서 직접 참조하는 최종 CSV 요약만 이 디렉터리에 둔다.

핵심 유지 대상:

- ONNX/ORT profiling 요약: `onnx_operator_histogram.csv`, `onnx_graph_io_summary.csv`, `ort_*`
- ORT micrograph baseline: `onnx_runtime_aligned_micrograph_baseline.csv`, `onnx_runtime_integer_micrograph_baseline.csv`
- FPGA board evidence: `fpga_jtag_primitive_benchmark.csv`, `fpga_jtag_cycle_counter_summary.csv`
- Quartus clean rebuild summary: `quartus_resource_timing_summary.csv`
- measured/projected 비교: `ort_vs_fpga_measured_and_projected_comparison.csv`, `fpga_optimized_interface_estimate.csv`

raw profiler JSON, legacy UART/custom-op table, prior diagnostic table, frozen archive는 `main`에 두지 않고 `examine` 브랜치에 보존한다.

해석 경계:

- FPGA board-measured latency는 fixed 16x4 INT8 Decode MatVec primitive의 internal cycle counter 값으로 제한한다.
- JTAG total latency는 System Console/JTAG host-tool invocation overhead이며 FPGA compute latency가 아니다.
- 이 표들은 full Gemma FPGA execution 또는 end-to-end ONNX Runtime speedup 근거가 아니다.
