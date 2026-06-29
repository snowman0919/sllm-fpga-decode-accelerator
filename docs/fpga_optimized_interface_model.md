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
| clock | 59.85 MHz |
| clock source | Quartus slow 1200mV 85C `CLOCK_50` Fmax |
| control overhead | 4 cycles |

For each lane count, cycles are computed as:

```text
cycles = ceil(macs / lanes) + control_overhead_cycles
compute_time_ms = cycles / clock_hz * 1000
```

Lane candidates are 1, 4, 8, and 16. The 16-lane projected compute-only lower bound is 8 cycles, or 0.000133668 ms at 59.85 MHz.

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
