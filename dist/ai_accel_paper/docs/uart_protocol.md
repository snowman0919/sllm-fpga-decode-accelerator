# FPGA UART MatVec Protocol

This protocol is a low-speed validation path for the fixed INT8 Decode MatVec primitive on DE10-Lite. It is not a performance bus and must not be interpreted as end-to-end ONNX Runtime acceleration evidence.

## Scope

- target primitive: `DecodeMatVecInt8`
- fixed accepted shape in the first FPGA top: `input_dim=16`, `output_dim=4`
- payload dtype: signed `int8`
- result dtype: signed `int32`
- byte order: little-endian
- checksum: omitted in the initial implementation

## Request Packet

| field | bytes | description |
| --- | ---: | --- |
| magic | 2 | `0xA5 0x5A` |
| cmd | 1 | `0x01` PING, `0x02` RESET, `0x10` MATVEC |
| seq | 1 | caller-controlled sequence byte |
| in_dim | 2 | little-endian unsigned integer |
| out_dim | 2 | little-endian unsigned integer |
| flags | 1 | reserved, set to `0` |
| payload_len | 4 | little-endian unsigned integer |
| payload | variable | MATVEC only: `activation int8[in_dim]`, then `weight int8[out_dim][in_dim]` |

The fixed MATVEC payload is 80 bytes: 16 activation bytes followed by 64 row-major weight bytes.

## Response Packet

| field | bytes | description |
| --- | ---: | --- |
| magic | 2 | `0x5A 0xA5` |
| cmd | 1 | `0x81` PING_ACK, `0x82` RESET_ACK, `0x90` MATVEC_RESULT |
| seq | 1 | copied from request |
| status | 1 | `0` OK, nonzero means rejected or parser error |
| out_dim | 2 | little-endian unsigned integer |
| payload_len | 4 | little-endian unsigned integer |
| payload | variable | MATVEC only: `result int32[out_dim]` |

For the fixed primitive, the MATVEC response payload is 16 bytes.

## Interpretation

Results from this protocol measure host packet creation, UART transfer, FPGA command handling, primitive execution, response transfer, and packet decode. If FPGA UART latency is slower than a CPU baseline, record that result directly and attribute the overhead to the validation transport where supported by the breakdown.
