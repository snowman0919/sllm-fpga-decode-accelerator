# Generated Verilog

이 디렉터리는 SpinalHDL source에서 생성한 Verilog의 기본 출력 위치다.

`just spinal-generate` 실행 후 핵심 JTAG board project로 복사되는 파일:

- `HexDisplay.v`
- `DecodeMatVecInt8_i16_o4.v`
- `DecodeMatVecRegBank.v`
- `JtagDecodeMatVecRegTop.v`

이 파일들은 `quartus/de10_lite_jtag_matvec/generated_verilog/`로 mirror되어 clean rebuild에 사용된다.

시뮬레이션 workspace는 이 디렉터리 아래에 생성될 수 있지만, 논문 근거로 쓰는 값은 `assets/`의 요약 CSV와 board manifest를 기준으로 한다.
