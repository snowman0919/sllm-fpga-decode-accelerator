# Paper Figures

논문에서 직접 인용하는 최종 그림만 이 디렉터리에 둔다.

유지 대상:

- ONNX Runtime profiling 요약 그림
- FPGA Decode MatVec 구조 그림
- ORT baseline, FPGA internal compute, JTAG invocation overhead, projected interface estimate를 구분한 비교 그림

raw artifact 정책:

- raw board 사진, 동영상, 전체 profiler JSON, 중간 진단 로그는 `main`에 두지 않는다.
- 전체 실험 흔적은 `examine` 브랜치에 보존한다.
- `main`에는 논문에서 인용하는 정리된 PNG/CSV만 남긴다.

해석 경계:

- FPGA 그림과 latency 그림은 fixed 16x4 INT8 Decode MatVec primitive evidence를 설명한다.
- JTAG total latency는 System Console/JTAG invocation overhead이며 FPGA compute latency가 아니다.
- 그림을 full Gemma FPGA execution 또는 end-to-end ONNX Runtime speedup 근거로 해석하지 않는다.
