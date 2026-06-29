# FPGA Optimized Interface Estimate Model

## Scope

This model separates three quantities that must not be mixed:

| layer | evidence type | interpretation |
| --- | --- | --- |
| Compute-only lower bound | projected | Datapath cycle estimate for the fixed 16x4 primitive |
| Optimized interface estimate | projected | Estimated host/accelerator invocation with preloaded weights and lower-overhead data movement |
| JTAG measured invocation path | measured correctness, latency unavailable in archived record | Correctness/invocation evidence only, not a performance interface |

The CSV artifact is `paper_assets/tables/fpga_optimized_interface_estimate.csv`.

## Fixed Primitive

The estimate uses the fixed primitive dimensions already used by the board validation path:

| parameter | value |
| --- | ---: |
| input dimension | 16 |
| output dimension | 4 |
| MACs | 64 |
| board clock | 50 MHz |
| Fmax clock | read from `paper_assets/tables/quartus_resource_timing_summary.csv` |
| control overhead | 4 cycles |

For each lane count, cycles are computed as:

```text
cycles = ceil(macs / lanes) + control_overhead_cycles
compute_time_us_50mhz = cycles / 50_000_000 * 1e6
compute_time_us_fmax = cycles / fmax_hz * 1e6
```

Lane candidates are 1, 4, 8, and 16. The generated CSV keeps `clock_hz_board`, `clock_hz_fmax`, `compute_time_us_50mhz`, and `compute_time_us_fmax` as separate columns so the DE10-Lite 50 MHz board-clock conversion is not mixed with timing-analysis Fmax context.

## Optimized Interface Assumptions

The optimized interface estimate assumes:

| parameter | value |
| --- | ---: |
| weight preloaded | true |
| activation transfer | 16 bytes |
| result transfer | 16 bytes |
| total per-invocation transfer | 32 bytes |

The interface candidates are:

| interface | assumption case | driver overhead | transfer bandwidth |
| --- | --- | ---: | ---: |
| `ideal_register_batch` | conservative / nominal / aggressive | 10 / 5 / 2 us | 20000 MB/s |
| `low_overhead_driver` | conservative / nominal / aggressive | 100 / 50 / 20 us | 100 MB/s |
| `dma_shared_memory_style` | conservative / nominal / aggressive | 25 / 10 / 5 us | 1000 MB/s |

These are design estimates, not measurements. They are included to show why JTAG is the wrong performance interface and why a future design would need weight preloading, batched register access, DMA, or shared-memory-style invocation to make primitive offload meaningful.

## Boundary

The optimized rows may be compared with ONNX Runtime only as projected design estimates. They are not measured board latency and do not establish ONNX Runtime speedup. The measured JTAG row remains a correctness path, while the optimized rows are future interface models.
