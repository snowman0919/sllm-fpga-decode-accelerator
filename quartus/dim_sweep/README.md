# Quartus Dim Sweep

이 디렉터리는 primitive 차원 변화에 따른 합성 경향을 확인하기 위한 보조 Quartus sweep 위치다.

목적:

- `dim = 16, 32, 64, 128` 변형의 resource/timing 경향 확인
- board-facing clean rebuild project인 `quartus/de10_lite_jtag_matvec/`와 분리
- 최종 논문 수치와 혼동되지 않는 보조 자료 유지

해석 경계:

- 이 sweep은 synthesis 보조 실험이며 board-measured primary evidence가 아니다.
- primary board evidence는 clean rebuild `de10_lite_jtag_matvec` bitstream과 JTAG cycle-counter run이다.
- full sLLM FPGA execution 또는 end-to-end ONNX Runtime speedup 근거로 사용하지 않는다.
