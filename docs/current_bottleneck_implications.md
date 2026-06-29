# Current Bottleneck Implications for Gemma 3 1B on ONNX Runtime

## 핵심 결론

현재 ONNX Runtime CPUExecutionProvider profiling으로 확인된 Gemma 3 1B 병목은 `KV-cache 하나`로 요약하기 어렵다. 측정 결과의 1차 병목은 MatMul 중심의 dense linear algebra이며, 그 내부에서도 attention QK score보다 `mlp/*_proj` 계열 projection과 `lm_head` projection이 큰 비중을 차지한다.

KV-cache는 여전히 중요하다. 다만 현 단계에서의 의미는 단일 주병목이 아니라, long-context decode에서 cache I/O, tensor shape expansion, concat, graph-level bookkeeping, memory movement를 통해 runtime pressure와 memory pressure를 키우는 보조 병목이다. 따라서 FPGA Decode 가속기 설계도 QK dot-product 단일 블록을 전체 병목 해결책으로 주장하기보다, dense MatVec/MatMul 데이터패스와 KV-cache stream/buffer interface를 함께 검토하는 방향이 더 타당하다.

## 증거 범위

- Test run: `nix develop -c just ort-sweep`, `nix develop -c just ort-sweep-report`, `nix develop -c just ort-matmul-analysis`, `nix develop -c just onnx-inspect model=/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx out_dir=onnx_profile/results_onnx`
- Runtime: ONNX Runtime `CPUExecutionProvider`
- Model: `/home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx`
- Context lengths: `128, 512, 1024, 2048`
- Decode steps: `1, 2, 4, 8`
- Runs / warmup: `3` / `1`
- Sweep status: `ok`
- Graph nodes / MatMul nodes: `7837` / `237`
- Cache I/O: cache inputs `52`, cache outputs `52`
- MatMul category 분석 profile: `60 / 60`

이 문서는 ONNX Runtime profiling 결과를 중심으로 해석한다. PyTorch sweep은 host-side reference baseline이고, FPGA 결과는 INT8 QK dot-product primitive feasibility evidence이므로 여기의 ORT 병목 수치와 직접 합치지 않는다.

## 1. MatMul이 현재 가장 강한 runtime hotspot이다

ORT sweep의 traced node time을 합산하면 MatMul은 전체 phase node time 중 가장 큰 비중을 차지한다.

| scope | MatMul time | traced phase time | MatMul share |
| --- | ---: | ---: | ---: |
| prefill 전체 | 14.711 s | 27.539 s | 53.4% |
| decode 전체 | 23.207 s | 28.629 s | 81.1% |
| prefill + decode | 37.918 s | 56.168 s | 67.5% |

decode에서 MatMul 지배성이 특히 강하다. context `128`부터 `2048`까지 decode 8-step 기준 MatMul share는 `86.7% -> 74.5%`로 내려가지만, 여전히 단일 operator group으로는 가장 크다.

| context | prefill latency | decode/token, 8 steps | prefill MatMul share | decode MatMul share, 8 steps |
| ---: | ---: | ---: | ---: | ---: |
| 128 | 250.5 ms | 144.1 ms/token | 77.1% | 86.7% |
| 512 | 856.7 ms | 152.1 ms/token | 71.7% | 85.1% |
| 1024 | 2330.9 ms | 197.4 ms/token | 55.5% | 81.6% |
| 2048 | 5782.7 ms | 170.1 ms/token | 48.9% | 74.5% |

이 표의 함의는 두 가지다. 첫째, 현재 ORT 실행에서 산술적으로 가장 큰 target은 MatMul 계열이다. 둘째, context가 길어질수록 MatMul만으로 전체 증가분을 설명하기 어려워진다. prefill latency는 context `128 -> 2048`에서 약 `23.1x` 증가했고, 같은 구간의 prefill MatMul share는 `77.1% -> 48.9%`로 낮아졌다. decode 8-step의 per-token latency는 `144.1 -> 170.1 ms/token`으로 약 `1.18x` 증가했지만, context `1024` 지점의 run variance가 커서 decode latency는 재반복 측정으로 안정성을 더 확인할 필요가 있다.

## 2. MatMul 내부의 주된 병목은 QK보다 MLP projection과 lm_head다

MatMul category를 node name/path 기반으로 보수적으로 분류하면, 전체 MatMul 시간 중 `mlp_projection`과 `lm_head`가 대부분을 차지한다.

| category | call count | total time | MatMul share |
| --- | ---: | ---: | ---: |
| `mlp_projection` | 14976 | 23.163 s | 61.09% |
| `lm_head` | 192 | 10.547 s | 27.81% |
| `attention_qkv_projection` | 14976 | 1.861 s | 4.91% |
| `attention_output_projection` | 4992 | 1.343 s | 3.54% |
| `attention_v_weighted_sum` | 4992 | 1.001 s | 2.64% |
| `unknown` | 384 | 0.003 s | 0.01% |
| `attention_qk_score` | 0 | 0.000 s | 0.00% |

`mlp_projection + lm_head` 합계는 전체 MatMul 시간의 `88.90%`다. 따라서 현재 ORT profiling만 놓고 보면 병목의 중심은 attention QK dot-product 단일 연산이 아니라 transformer block 전반에 반복되는 dense projection이다.

phase별로 보아도 같은 결론이 유지된다.

| phase | category | total time | MatMul share |
| --- | --- | ---: | ---: |
| prefill | `mlp_projection` | 8.147 s | 55.38% |
| prefill | `lm_head` | 4.467 s | 30.36% |
| prefill | attention projection/sum 합계 | 2.097 s | 14.25% |
| decode | `mlp_projection` | 15.017 s | 64.71% |
| decode | `lm_head` | 6.080 s | 26.20% |
| decode | attention projection/sum 합계 | 2.109 s | 9.09% |

`lm_head`는 call count가 적지만 output dimension이 매우 크다. profile shape 예시는 `[1, 128, 1152] -> [1, 128, 262144]`이며, decode에서도 token마다 vocabulary projection이 발생한다. MLP projection은 각 layer에서 `gate_proj`, `up_proj`, `down_proj`가 반복되고, shape 예시는 `[1, seq, 1152] -> [1, seq, 6912]` 또는 `[1, seq, 6912] -> [1, seq, 1152]`다. 이 구조 때문에 작은 per-node latency가 layer 수와 projection 수만큼 누적된다.

`attention_qk_score`가 0.00%라는 값은 QK 연산이 존재하지 않는다는 뜻이 아니다. 이 분석은 profile node name/path와 output shape로 QK score를 확정할 수 있는 MatMul만 분류했다. QK score가 ORT 최적화, fused kernel, 또는 다른 node 형태로 나타난 경우에는 이 category에 넣지 않았다. 따라서 안전한 해석은 `현재 MatMul hotspot으로 확인되는 큰 덩어리는 QK score가 아니라 MLP/lm_head 쪽`이라는 것이다.

## 3. KV-cache와 graph overhead는 long-context에서 보조 병목으로 커진다

ONNX graph에는 cache-style I/O가 명확히 존재한다. cache input과 output이 각각 `52`개이며, decode mode는 `with_past_kv_cache`로 실행되었다. 이것은 KV-cache를 측정 가능한 decode 구성 요소로 만든다. 그러나 cache I/O 존재 자체가 KV-cache 단독 병목을 증명하지는 않는다.

현재 결과에서 KV-cache의 의미는 다음에 가깝다.

- decode가 길어진 context를 참조할수록 past/present tensor의 shape, concat, expand, gather, reshape 계열 연산과 memory movement가 증가한다.
- MatMul은 여전히 큰 산술 병목이지만, context가 커질수록 MatMul 외 연산의 상대 비중이 커진다.
- prefill에서는 long sequence 전체를 처리하므로 MatMul 외에도 `Mul`, `Where`, `Add`, `Softmax` 같은 sequence-length sensitive 연산이 크게 증가한다.

예를 들어 prefill의 MatMul share는 context `128`에서 `77.1%`였지만 context `2048`에서는 `48.9%`까지 내려간다. 같은 구간에서 prefill latency는 `250.5 ms -> 5782.7 ms`로 약 `23.1x` 증가했다. 즉 long-context prefill에서는 MatMul 자체도 커지지만, graph-level tensor operation과 memory traffic도 같이 커진다.

decode 8-step 기준 top operator도 같은 방향을 보여준다.

| context | MatMul | notable non-MatMul operators |
| ---: | ---: | --- |
| 128 | 2855.0 ms | `Unsqueeze` 49.7 ms, `Mul` 47.8 ms, `Concat` 45.5 ms, `Gather` 40.5 ms |
| 512 | 2960.0 ms | `Expand` 70.2 ms, `Concat` 66.9 ms, `Unsqueeze` 51.8 ms, `Mul` 48.0 ms |
| 1024 | 3694.6 ms | `Expand` 187.1 ms, `Concat` 136.0 ms, `Unsqueeze` 85.3 ms, `FusedMatMul` 63.1 ms |
| 2048 | 2915.1 ms | `Expand` 414.2 ms, `Concat` 150.8 ms, `FusedMatMul` 91.8 ms, `Unsqueeze` 51.3 ms |

prefill context `2048`에서는 non-MatMul pressure가 더 분명하다. traced node time `17.307 s` 중 `MatMul`은 `8.460 s` (`48.9%`)였고, 그 다음은 `Mul` `3.201 s` (`18.5%`), `Where` `1.986 s` (`11.5%`), `Add` `1.552 s` (`9.0%`), `Softmax` `0.492 s` (`2.8%`), `FusedMatMul` `0.484 s` (`2.8%`) 순이었다.

따라서 `KV-cache는 병목이 아니다`도 부정확하고, `KV-cache 하나가 병목이다`도 부정확하다. 더 정확한 표현은 다음과 같다.

> ONNX Runtime 기반 Gemma 3 1B 실행에서 주된 runtime hotspot은 MatMul 중심 dense linear algebra이며, long-context decode에서는 cache I/O와 graph-level tensor manipulation이 memory/runtime pressure를 증가시키는 보조 병목으로 작동한다.

## 4. FPGA Decode accelerator 설계에 대한 함의

현재 DE10-Lite 결과는 INT8 QK dot-product primitive가 deterministic test vector에 대해 합성, programming, board display validation까지 가능하다는 feasibility evidence다. 예상 signed score는 `-22`, lower 16-bit two's-complement 값은 `0xFFEA`, board display는 `HEX3..HEX0 = F F E A`다. 이 결과는 유효하지만, Gemma 3 1B 전체 decode 병목을 해결했다는 뜻은 아니다.

현재 병목 분석을 반영하면 FPGA 설계 방향은 다음처럼 정리하는 것이 안전하다.

1. QK dot-product primitive는 decode attention datapath의 한 구성요소로 유지한다.
2. 그러나 우선순위가 더 큰 후보는 MLP projection, attention projection, lm_head에 공통으로 나타나는 dense MatVec/MatMul datapath다.
3. 특히 decode는 batch/token dimension이 작고 weight dimension이 큰 projection이 반복되므로, weight streaming, tiling, reuse, accumulation, quantization strategy가 핵심 설계 문제가 된다.
4. `lm_head`는 vocabulary projection이 커서 bandwidth와 output reduction/top-k 전략을 함께 고려해야 한다.
5. KV-cache는 QK dot-product 자체보다 buffer layout, stream interface, past/present update, concat 제거 또는 graph rewrite 가능성의 문제로 다루는 것이 더 타당하다.
6. ONNX Runtime graph overhead를 줄이려면 hardware block만이 아니라 host/runtime boundary, operator fusion, static shape specialization, cache tensor binding 전략도 같이 검토해야 한다.

즉 논문에서 FPGA 파트는 `QK dot-product를 검증했으므로 전체 decode 병목이 해결된다`가 아니라, `QK primitive 검증을 출발점으로 삼되, profiling 결과상 future accelerator는 projection-heavy dense linear algebra와 KV-cache stream/buffer pressure까지 포괄해야 한다`고 쓰는 편이 증거와 맞다.

## 5. 논문용 해석 문단

다음 문단은 결과/논의 섹션에 바로 가져다 쓸 수 있는 형태다.

> ONNX Runtime CPUExecutionProvider 기반 Gemma 3 1B profiling 결과, 실행 시간의 1차 hotspot은 KV-cache 단일 요소가 아니라 MatMul 중심의 dense linear algebra로 나타났다. Context sweep 전체에서 MatMul은 traced phase time의 67.5%를 차지했으며, decode 단계에서는 81.1%까지 상승하였다. MatMul 내부를 node path 기반으로 분류한 결과, `mlp_projection`과 `lm_head`가 전체 MatMul 시간의 88.90%를 차지하였다. 이는 decode 병목을 attention QK score 하나로 축소하기보다, transformer block의 반복적 MLP projection과 vocabulary projection을 포함하는 dense projection workload로 해석해야 함을 보여준다.

> 동시에 context length가 증가할수록 KV-cache 및 graph-level overhead의 영향도 커졌다. ONNX graph는 52개의 cache input과 52개의 cache output을 노출하며, decode cache reuse가 가능한 interface를 제공한다. Decode 8-step 기준 MatMul share는 context 128에서 86.7%였으나 context 2048에서 74.5%로 감소했고, `Expand`, `Concat`, `Unsqueeze` 등 cache/shape manipulation과 관련된 operator 시간이 증가하였다. 따라서 KV-cache는 단독 주병목이라기보다 long-context decode에서 memory movement와 runtime overhead를 키우는 구조적 보조 병목으로 해석하는 것이 적절하다.

> 이러한 결과는 FPGA Decode accelerator의 설계 범위를 재조정한다. 현재 DE10-Lite 구현은 INT8 QK dot-product primitive의 feasibility validation으로 한정되며, full Gemma 3 1B 실행이나 end-to-end ONNX Runtime speedup을 의미하지 않는다. 향후 구조는 QK dot-product뿐 아니라 MLP/lm_head/attention projection을 포괄하는 dense MatVec/MatMul datapath, quantized weight streaming, accumulation, KV-cache buffer/stream interface, 그리고 graph/runtime overhead를 줄이기 위한 operator fusion 또는 static-shape specialization까지 함께 고려해야 한다.

## 6. 주장 경계

이 자료에서 말할 수 있는 것:

- ONNX Runtime CPU profiling에서 MatMul이 현재 가장 큰 runtime hotspot이다.
- MatMul 내부에서는 `mlp_projection`과 `lm_head`가 큰 비중을 차지한다.
- KV-cache I/O는 graph에 존재하며, long-context decode pressure를 키우는 구조적 요인이다.
- FPGA QK block은 decode attention primitive feasibility evidence다.

이 자료만으로 말하면 안 되는 것:

- KV-cache가 유일한 병목이다.
- QK dot-product가 전체 Gemma 3 1B decode의 지배 병목이다.
- DE10-Lite가 Gemma 3 1B 또는 full sLLM을 실행했다.
- FPGA 결과가 ONNX Runtime end-to-end speedup을 증명한다.
- PyTorch sweep 결과를 ONNX Runtime profiling 결과로 대체할 수 있다.

## 관련 산출물

- `docs/onnx_bottleneck_report.md`
- `docs/onnx_runtime_sweep_report.md`
- `docs/ort_matmul_hotspot_analysis.md`
- `paper_assets/tables/ort_context_sweep_latency.csv`
- `paper_assets/tables/ort_operator_share_by_context.csv`
- `paper_assets/tables/ort_matmul_category_by_context.csv`
- `paper_assets/tables/ort_matmul_top_nodes.csv`
- `paper_assets/figures/ort_matmul_category_share.png`
