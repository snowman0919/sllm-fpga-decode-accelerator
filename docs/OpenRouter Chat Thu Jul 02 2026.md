# 해당 논문은 내가 작성하고 있는 논문의 초안이야. 현재도 수정을 지속하고

**User - --**

해당 논문은 내가 작성하고 있는 논문의 초안이야. 현재도 수정을 지속하고 있어, 수정의 방향성을 잡기 위해. 해당 논문을 조목조목 비평하고 문장의 함의와 중의성, 논문으로서 가치가 하락하는 지점을 짚어주고 수정사항을 제시해줘. 평가는 학회에서 박사졸업논문을 평가하듯 비판적으로 진행해

**Assistant - --**

먼저 한 가지 전제를 분명히 하겠습니다. 이 글은 요청하신 대로 "박사학위 심사장에서의 비판적 평가" 톤으로 작성합니다. 저자가 고등학생이라는 점을 고려하면 이 논문이 보여주는 정직성과 재현성 관리는 매우 인상적이지만, 요청하신 기준(학회·학위 심사)에서는 칭찬보다 결함을 적시하는 것이 도움이 되므로 그렇게 진행하겠습니다.

## 총평 (Verdict)

<details open>
<summary><b>핵심 진단: 이 논문은 "정직함"을 "기여"로 착각하고 있다</b></summary>

이 논문의 가장 큰 문제는 표절이나 데이터 조작 같은 종류가 아니라, **주장을 모두 회수(retract)하고 나면 남는 명제가 거의 없다**는 점입니다. 거의 모든 문장이 "그러나 이것은 X를 의미하지 않는다", "성능 주장으로 해석하지 않는다"로 끝납니다. 이는 학문적 정직성으로는 칭찬할 만하나, 심사 관점에서는 **저자 스스로 자기 논문의 결론을 무효화하고 있다**는 신호입니다.

논문을 다음과 같이 압축하면 본질이 드러납니다.

1. CPU에서 ONNX Runtime을 돌렸더니 MatMul, 특히 projection이 시간을 많이 쓴다 → **잘 알려진 사실**
2. 16×4 INT8 MatVec을 FPGA에 올렸더니 맞게 동작한다 → **사소한 primitive**
3. 1번과 2번은 **어떤 측정으로도 연결되어 있지 않다**

즉 "병목 분석"과 "가속기 설계"라는 두 축이 모두 약하고, 그 둘을 잇는 논리적 다리가 측정으로 뒷받침되지 않습니다.
</details>

---

## 1. 가장 치명적인 결함: 방법론의 방향이 거꾸로다

이 논문의 핵심 논증 구조는 다음과 같습니다.

> CPU(ORT CPUExecutionProvider)에서 MatMul이 지배적 → 따라서 FPGA는 projection MatVec을 가속해야 한다 → 작은 MatVec primitive를 검증했다

여기서 $1 \to 2$ 추론이 학문적으로 성립하지 않습니다.

- **CPU에서 비싼 연산이 FPGA에서 이득이 되는 연산이라는 보장이 없습니다.** 가속기 설계를 정당화하려면 CPU operator share가 아니라, *offload 후 얻는 이득(Amdahl/roofline)* 을 근거로 삼아야 합니다. CPU에서 60%를 차지하는 연산이라도, 그것이 메모리 대역폭 병목이고 FPGA로 옮기면 데이터 이동 비용이 더 커진다면 가속 대상이 아닙니다.
- 저자 스스로 표 12에서 모든 projection을 `bandwidth-bound`로 분류했습니다. 그렇다면 **compute 가속기(MatVec engine)를 만드는 것 자체가 잘못된 처방**일 수 있습니다. bandwidth-bound 워크로드에 compute lane을 늘리는 설계는 roofline상 의미가 없습니다. 이 모순이 논문 안에서 해소되지 않습니다.

**제안:** 동기 부여를 "CPU에서 무엇이 비싼가"가 아니라 "decode 단계 projection이 가속 가능한 arithmetic intensity / 데이터 재사용 구조를 갖는가"로 재구성해야 합니다. 그렇지 않으면 분석과 설계의 인과관계가 무너집니다.

---

## 2. 프로파일링 자체의 타당성 위협 (가장 시급한 수정 대상)

여기가 심사위원이라면 가장 먼저 찌를 지점입니다.

### 2.1 float32 모델을 프로파일링했다는 치명적 비대표성

표 13에서 ONNX Runtime baseline이 **"float32 MatMul equivalent"** 로 실행되었다고 명시되어 있습니다. 그런데 실제 온디바이스 sLLM은 거의 예외 없이 INT8/INT4로 배포됩니다.

- float32 모델에서 MatMul이 67.5%를 차지한다는 사실은, **양자화된 실제 배포 모델의 병목 프로파일을 대표하지 못합니다.** 양자화하면 MatMul 비용이 줄고 dequant·shape·cache I/O의 상대 비중이 커지는 것이 일반적입니다.
- 따라서 "병목은 projection MatMul" 이라는 핵심 결론이 **연구가 표방하는 '온디바이스 배포' 시나리오에 대해 무효**일 수 있습니다.

이것은 단순 한계가 아니라 **동기(motivation)를 붕괴시키는 문제**이므로, 양자화 경로에서 재측정하거나, 최소한 "왜 float32 프로파일이 배포 병목의 대리지표로 정당한가"를 논증해야 합니다.

### 2.2 토큰당 140~250ms — 측정 환경의 신뢰성 문제

표 4의 `decode/token mean`이 Ryzen 7 9700X에서 1B 모델에 대해 139~249 ms/token입니다. 이는 비정상적으로 느립니다(최적화된 INT4 1B 모델은 동급 CPU에서 수십 ms 이하). 이 수치는 **export/실행 파이프라인이 최적화되지 않았음**을 강하게 시사합니다. 즉 관측된 병목이 "Transformer decode의 본질적 병목"인지 "미최적화 ONNX export의 우발적 병목"인지 구분되지 않습니다.

### 2.3 long-decode sweep의 자기모순

`runs=1, warmup=0`이라 "latency benchmark가 아니다"라고 정직하게 선언하면서도, 표 4에 `decode/token mean` (ms 단위)을 그대로 싣고, 결론과 표 10에서 "$72.91\sim87.29\%$" 같은 범위를 인용합니다.

- **벤치마크가 아니라고 선언한 데이터에서 정량적 결론을 끌어내면, 그 선언은 면책이 아니라 자기모순이 됩니다.** 심사에서 "그럼 이 표는 왜 있는가"라는 질문에 답할 수 없습니다.
- operator share 경향만 보겠다면 ms 수치는 빼고 share만 제시하거나, 제대로 된 반복 측정으로 교체해야 합니다.

### 2.4 traced node time ≠ wall-clock

"trace 수집 node 시간"의 67.5%라는 수치는 *traced 구간 내부*의 비중입니다. 전체 wall-clock 중 trace되지 않은 host overhead가 얼마인지 보고하지 않으면, "MatMul이 전체 latency의 67.5%"라는 흔한 오독을 막을 수 없습니다. **untraced fraction을 반드시 보고**해야 합니다.

---

## 3. FPGA 파트와 "Offload 역설"

### 3.1 16×4 primitive와 실제 워크로드의 4~5자리 간극

데모는 `inputDim=16, outputDim=4`인데, 실제 대상은 `mlp_projection` $1152 \to 6912$, `lm_head` $1152 \to 262144$입니다. 64개 MAC 규모의 toy와 실제 워크로드 사이에는 약 $10^4 \sim 10^5$배의 간극이 있습니다.

- "65 cycles, 1.3 µs"는 이 toy 규모에서만 의미가 있고, **scaling 분석이 전혀 없습니다.** outputDim이 262144인 `lm_head`에서 이 구조가 어떻게 동작하는지, tile 수·BRAM·DSP가 어떻게 늘어나는지에 대한 정량 모델이 없으면 "가속기 구조 설계"라는 제목을 지탱할 수 없습니다.

### 3.2 JTAG 7720 ms — 논문의 전제를 스스로 반증하는 숫자

가장 날카로운 모순은 여기입니다. 내부 compute는 1.3 µs인데 JTAG total invocation은 **7720 ms**, 즉 약 $6 \times 10^6$배입니다.

저자는 이를 "host-tool overhead일 뿐 가속 성능이 아니다"라고 정직하게 분리합니다. 그러나 이 정직함이 역설을 만듭니다.

> projection은 bandwidth-bound인데(표 12), 선택한 플랫폼/인터페이스(DE10-Lite + JTAG)는 데이터 이동에서 6자리 단위로 손해를 본다. 그렇다면 **이 설계 방향은 자신이 식별한 병목(데이터 이동)을 정면으로 악화시킨다.**

"projected optimized interface"(표 14, 0.005 ms)는 측정이 아니라 가정이며, weight preloading·DMA를 전제합니다. 즉 **실제로 이득이 나는 구간은 전부 미측정 가정 영역에 있습니다.** 이것은 설계 제안의 핵심 약점이며, 단순히 "estimate라고 표기했다"로 면책되지 않습니다.

### 3.3 통계적 연출의 문제

표 8에서 `COMPUTE_CYCLES`의 mean/p50/p95가 모두 65.0입니다. 결정론적 회로에서 당연한 결과인데 p50/p95를 제시하는 것은 **통계적 엄밀성의 외형만 빌린 것**입니다. 반대로 정작 variance가 중요한 JTAG latency(7720.45~7748.85)는 분산 논의가 없습니다. 통계 표기를 의미 있는 곳에만 쓰십시오.

---

## 4. 기여(Contribution)의 부재 — 무엇이 새로운가?

심사에서 "그래서 새로운 발견이 무엇인가?"에 답해야 합니다. 현재로서는:

| 주장한 기여 | 실제 평가 |
|---|---|
| MatMul이 dense linear algebra hotspot | 교과서적 사실, 비novel |
| `mlp_projection + lm_head`가 MatMul의 88.9% | **거의 동어반복** — 가장 큰 행렬이 가장 오래 걸리는 것은 자명 |
| "병목은 KV-cache/QK만이 아니다" | **허수아비 논증** — 진지한 연구자는 decode 병목을 QK 단독으로 환원하지 않음 |
| evidence layer 분리 방법론 | 가장 방어 가능한 기여이나, 기술적 결과가 아닌 *서술 프레임* |
| FPGA MatVec primitive 검증 | toy 규모, scaling 부재 |

특히 `attention_qk_score = 0.00%` 항목은 *발견*이 아니라 **분류기의 결함**입니다. runtime classifier가 QK를 통째로 놓쳤고, 저자가 graph-level fallback을 추가해서야 26개 노드를 찾았다는 것은 — 솔직하긴 하나 — **category 분석 전체의 신뢰도를 떨어뜨립니다.** QK를 놓쳤다면 다른 분류는 신뢰할 수 있는가? 라는 질문이 따라옵니다.

---

## 5. 제목과 내용의 불일치 (Overclaim)

- 제목: "FPGA **기반 Decode 가속기 구조 설계**"
- 실제: 16×4 toy primitive + 블록 다이어그램(그림 6) + 미구현 "future architecture sketch"

본문은 정직하게 "future 구조 제안이며 현재 구현이 아니다"라고 반복하지만, **제목은 그 정직함을 배신합니다.** 제목/초록과 본문 면책 사이의 이 긴장은 심사에서 "제목 사기(title overclaim)"로 지적될 전형적 사례입니다.

**제안 제목:** "ONNX Runtime 기반 온디바이스 sLLM의 Decode projection 병목 분석과 INT8 MatVec primitive의 FPGA 타당성 검증" 정도로, 실제 한 일에 맞춰 축소해야 합니다.

---

## 6. 문장 수준의 중의성·정밀도 문제

<details>
<summary>구체적 라인 에디트 (펼치기)</summary>

- **초록**: "MatMul은 ... node 시간(traced phase time)의 67.5%를 차지했으며" — '시간의 67.5%'라는 표현은 wall-clock 오독을 부릅니다. "trace된 node event duration 합계 중 67.5%"로 한정어를 문장 안에 박아야 합니다.
- **"이 결과는 병목을 KV-cache 또는 QK dot-product 하나로 축소하기 어렵다는 점을 보여준다"** — 누가 그렇게 축소했는지 선행 문헌 근거가 없습니다. 반박 대상이 명시되지 않으면 허수아비입니다.
- **"board-measured evidence로 제한한다"** — '제한한다(limit)'가 초록에서 4회 이상 반복됩니다. 면책 문구의 과잉은 오히려 *결과가 빈약하다*는 인상을 줍니다. 면책은 '한계' 절에 한 번 정리하고 본문에서는 줄이십시오.
- **"projection-general dataflow"**, **"offload boundary"** 등 신조어가 정의 없이 반복 사용됩니다. 최초 등장 시 1문장 정의가 필요합니다.
- **표 10의 "72.91~87.29%"** vs 본문 4.2의 "72.91~78.33%" — **수치 범위가 표마다 다릅니다.** 87.29%는 표 4의 `Expand+...` 열(7.29%)과 혼동된 오기로 보입니다. 즉시 검증·수정 요망. 이런 불일치는 심사에서 데이터 관리 신뢰도를 떨어뜨립니다.
- **"FPGA 내부 연산부가 ... Decode 병목 primitive를 낮은 compute latency로 처리할 수 있음을 보이는 board-measured evidence이다"** (12쪽) — 이 문장은 1.3 µs(데이터 이동 제외)와 13 µs(런타임 오버헤드 포함)를 비교한 것으로, 면책 문구가 붙어 있어도 **사실상 우위 암시(misleading)** 입니다. 동일 조건 비교가 아님을 문장 *안*에서 명시하거나 비교 자체를 빼야 합니다.
- 영어 용어의 과도한 코드펜스(`mlp_projection`, `lm_head` 등) 처리는 가독성을 크게 해칩니다. 한국어 학술지 문체로 보면 산만합니다.

</details>

---

## 7. 인용·관련연구의 표면성

관련 연구(FlashAttention, GPTQ, vLLM, FlightLLM 등)는 "우리는 이것을 하지 않는다"는 *차별점 나열*로만 소비됩니다. 정작 **본 연구의 설계 선택이 이들로부터 무엇을 받아들였는지**가 없습니다. 예컨대 FlightLLM의 mapping flow나 DFX의 데이터 이동 처리가 JTAG 병목 문제에 어떤 교훈을 주는지 논의했다면, 6장의 offload 역설을 정면으로 다룰 수 있었을 것입니다. 현재는 관련연구가 *방어용 울타리*로만 쓰입니다.

---

## 8. 수정 로드맵 (우선순위 순)

1. **[필수] float32 vs 양자화 문제 해결** — INT8/INT4 경로에서 재프로파일하거나, float32 프로파일이 배포 병목의 대리지표라는 명시적 논증을 추가. 이것이 안 되면 동기 자체가 무너짐.
2. **[필수] 분석→설계의 인과 재구성** — operator share가 아니라 arithmetic intensity / roofline 기반으로 "왜 이 연산이 FPGA 가속 후보인가"를 논증. bandwidth-bound 분류와 compute-engine 설계 사이의 모순을 해소.
3. **[필수] Offload 역설 정면 돌파** — JTAG 7720 ms는 한계가 아니라 "선택한 인터페이스가 식별된 병목을 악화시킨다"는 문제. projected estimate가 아닌, 최소한의 *측정된* DMA/온칩 경로 실험을 하거나, 못한다면 결론을 "compute 타당성 확인"으로 강하게 축소.
4. **[필수] scaling 모델 추가** — 16×4 → 실제 차원으로의 자원/지연 외삽 모델. 없으면 "구조 설계"라는 표현 철회.
5. **[권장] 제목·초록을 실제 결과에 맞게 축소.** 면책 문구를 한계 절로 집약.
6. **[권장] long-decode sweep을 제대로 반복 측정으로 교체**하거나, latency 수치를 제거하고 share trend만 남김.
7. **[권장] category 분류기 신뢰도 보강** — QK 누락이 분류 전반에 주는 함의를 정량적으로 평가.
8. **[권장] 수치 불일치(72.91~87.29% 등) 전수 점검.**

---

## 마무리 코멘트

냉정히 말하면, 현재 원고는 **잘 정리된 엔지니어링 로그**이지 *논문*의 형태에 아직 도달하지 못했습니다. 강점인 정직성과 재현성(비트스트림 SHA-256, c01~c19 출처 표기)은 그대로 살리되, 그것이 *결론의 회수*가 아니라 *검증 가능한 주장의 토대*가 되도록 방향을 바꿔야 합니다.

핵심 한 문장으로 요약하면:

> **이 연구가 답해야 할 단 하나의 질문은 "CPU 프로파일에서 비싼 연산을, 데이터 이동에서 6자리 손해를 보는 플랫폼으로 옮기는 것이 왜 의미 있는가?"이며, 현재 원고는 이 질문을 정직하게 회피할 뿐 답하지 않는다.**

이 질문에 측정으로 답하는 순간, 위 결함의 절반 이상이 동시에 해소됩니다.

방향 설정에 도움이 되도록, 위 8개 수정 항목 중 어느 것부터 함께 깊게 파고들지 골라주시면 구체적인 실험 설계나 문장 재작성까지 도와드리겠습니다.

**Assistant - --**

해당 논문 초안에 대해 학회에서 박사 학위 논문을 평가하는 기준을 적용하여 비판적으로 검토한 결과를 제시합니다. 연구의 방향성과 증거 기반(evidence-based) 접근을 구분하려는 태도는 돋보이나, 학술 논문으로서의 가치와 설득력을 떨어뜨리는 몇 가지 치명적인 지점이 존재합니다. 이를 조목조목 짚어보고 수정 방향을 제안합니다.

---

## 1. 논문의 가치 하락 지점 및 핵심 비판

### 1.1 과도한 면책 조항(Disclaimer)으로 인한 설득력 상실
이 논문의 가장 큰 약점은 **"이 결과는 end-to-end 성능이 아님", "이것은 성능 가속 주장이 아님"이라는 변명을 초록부터 결론까지 반복**한다는 점입니다. 
- **문장의 함의:** 연구자가 자신의 기여도에 대한 확신이 없거나, 결과의 빈약함을 사전에 방어하려는 태도로 읽힙니다. 학술 논문은 자신의 설계와 결과에 대해 책임을 지고 주장하는 형태이어야 합니다.
- **수정 방향:** 본문 곳곳에 산발된 면책 문구를 전부 삭제하십시오. 대신, "본 연구는 ~한 한계 내에서 ~을 증명하며"라는 식의 객관적 서술로 대체하고, 상세한 한계는 **III. 결론의 '2. 연구의 한계' 섹션에 한 번에 모아 명료하게 정리**해야 합니다.

### 1.2 FPGA 검증 규모의 현저한 부족
FPGA 가속기 설계를 주제로 한 논문임에도 불구하고, 실제 하드웨어 검증이 $16 \times 4$ 크기의 INT8 MatVec primitive(총 64개의 곱셈-누적 연산)에 불과합니다.
- **가치 하락 지점:** 분석 대상인 Gemma 3 1B의 실제 projection 차원은 1152$\rightarrow$6912 등 매우 큽니다. $16 \times 4$ primitive는 실제 연산 부하와 너무 동떨어져 있어 "가속기 구조 설계"라는 타이틀을 뒷받침하기 어렵습니다. 박사 논문 기준에서는 최소한 실제 모델의 한 타일(tile) 규모(예: $1152 \times 512$ 등)에 대한 합성(synthesis) 결과나 리소스 추정치, 메모리 대역폭 분석을 실측 기반으로 제시해야 합니다.
- **수정 방향:** 논문의 제목을 "FPGA 기반 Decode 가속기 구조 설계"에서 **"ONNX Runtime 기반 sLLM 추론 병목 분석 및 FPGA 가속을 위한 Primitive 수준 설계 방향성 탐색"**으로 수정하여 기대 수준을 조정하거나, 제안하는 아키텍처(그림 6)에 대해 최소한의 파라미터화된 합성 추정(synthesis estimate) 데이터를 추가해야 합니다.

### 1.3 데이터 신뢰성 문제와 변명적 서술
표 4의 Long-decode sweep 데이터는 `runs 1, warmup 0` 조건으로 수행되었습니다.
- **문장의 함의:** 측정 환경이 통계적 신뢰성을 결여하고 있음에도 이를 본문 중심 결과(표 4)에 배치하고 "latency benchmark가 아니라 operator share 경향 확인용"이라고 반복적으로 변명하는 것은 논문의 논리적 흐름을 깹니다. 신뢰성 없는 데이터를 본문에 두고 예외를 달아두는 것은 학술 논문에서 지양해야 할 습관입니다.
- **수정 방향:** Long-decode sweep을 본 실험이 아닌 보조 실험으로 격하하거나, 데이터를 측정하여 `runs 3` 이상의 정상적인 통계를 다시 산출해 포함시키십시오.

---

## 2. 문장의 중의성 및 텍스트 오류 수정

### 2.1 오타 및 OCR/복붙 오류
논문 전반에 걸쳐 치명적인 오타와 텍스트 깨짐 현상이 존재합니다. 이는 학술 논문으로서의 신뢰도를 크게 훼손합니다.
- **"Material" 오타:** 본문 3.4절 표 5와 본문 전체에서 `MatMul`을 `Material`로 오기입했습니다. "Material category 분석 결과", "Material 내부 category" 등을 모두 `MatMul`로 수정하십시오.
- **캡션 내 의미 불명 영어 문장:** 
  - 그림 1 캡션 하단: "Existence based on domain expansion. Within graph, ANF+ sentence profiling, most wide forfeited references. While primitive+validation." -> **문맥을 전혀 알 수 없는 텍스트이므로 즉시 삭제**하십시오.
  - 그림 6 캡션 하단: "Sequence-general tiled data path for first projection, attention projection, next to, scale output thing, cache/accelerator output, precision input." -> 의미가 불완전하므로 "제안된 FPGA Decode tiled MatVec/MatMul 가속기의 전체 데이터 흐름도" 정도의 간결한 한국어로 수정하십시오.

### 2.2 번역투 용어 및 어색한 표현
- **"trace 수집 node 시간(traced phase time)"**: 직역투의 느낌이 강합니다. "프로파일링 트레이스 상의 노드 실행 시간 합" 또는 간단히 "트레이스 노드 시간"으로 통일하여 서술하십시오.
- **"FPGA primitive 수준 검증"**: "FPGA 연산 단위(Primitive) 수준 검증"으로 명사를 보완하십시오.
- **"계층"의 혼용**: "runtime 계층", "evidence layer(증거 계층)" 등의 용어가 혼용되고 있습니다. 증거 계층이라는 용어가 연구 방법론을 설명하는 데 유용하므로, "Layer"라는 단어를 일관되게 "단계" 또는 "계층"으로 통일해 번역하십시오.

---

## 3. 논리적 연결 및 구조적 비판

### 3.1 분석 결과와 FPGA 제안의 인과관계 부족
ONNX Runtime 프로파일링에서 `mlp_projection`과 `lm_head`가 병목(88.90%)이라는 결과를 도출한 것은 훌륭합니다. 그러나 이를 근거로 제안된 FPGA 구조(그림 6, 표 11)가 실제 프로파일링된 차원과 어떻게 매핑되는지 구체적으로 설명되지 않았습니다.
- **수정 방향:** 표 12(Roofline/design estimate)에서 제시한 representative shape(1152$\rightarrow$6912 등)을 기반으로, 제안하는 tiled MatVec 엔진이 이 연산을 처리하기 위해 몇 개의 타일로 쪼개지고, 어느 정도의 온칩 메모리(BRAM)가 필요한지 산정하는 논리적 단계가 추가되어야 "설계 제안"으로서의 가치를 갖습니다.

### 3.2 표 5의 분류 오류에 대한 지나친 방어
표 5에서 `attention_qk_score`가 0.00%로 나타난 것에 대해, graph-level fallback 분석을 통해 26개의 노드를 확인했다고 서술합니다. 그러나 이를 끝까지 "런타임 이벤트 분류 규칙의 한계"로만 돌리는 것은 아쉽습니다. 
- **수정 방향:** ONNX Runtime의 그래프 최적화(Graph Optimization) 단계에서 attention 연산이 하나의 fused 노드(예: `MultiHeadAttention`) 또는 커스텀 커널로 병합되어 trace에 노드 단위로 노출되지 않았을 가능성을 언급하고, 이를 분석의 한계로 명확히 선긋기 하는 것이 더 학술적인 태도입니다.

---

## 4. 요약 및 수정 방향성 가이드라인

1. **제목 및 기대효과 조정:** 현재의 FPGA 구현 규모(16x4)를 고려하여, 논문의 기여를 "분석 중심의 설계 방향 탐색"으로 명확히 한정지으십시오.
2. **면책 문구 통합:** 본문 곳곳의 "이것은 end-to-end 성능이 아님", "이것은 가속 주장이 아님"이라는 문장을 전부 삭제하고, 결론의 '연구의 한계'에서 딱 한 번 서술하십시오.
3. **텍스트 교정:** `Material` -> `MatMul` 전역 치환, 그림 1 및 그림 6의 깨진 영어 캡션을 한국어로 재작성.
4. **데이터 보완:** 표 4 (Long-decode sweep)의 데이터를 다시 측정하여 `runs`를 3~5회로 늘리고, 변명구문을 삭제한 채 정상적인 비교 데이터로 제시하십시오.
5. **설계 매핑 명확화:** 프로파일링 결과(표 5의 차원)와 제안하는 tiled MatVec 아키텍처(표 11, 12) 간의 구체적인 타일링 전략을 한 단락 추가하여 설명하십시오.

해당 논문은 기획 단계의 프레임워크(evidence layer 분리)는 훌륭하나, 결과의 빈약함을 두려워한 나머지 본문 전체가 방어적 태도로 일관하고 있습니다. 자신의 분석 결과에 대한 확신을 가지고, 한계는 한계의 자리(결론부)로 보내십시오.

**Assistant - --**

박사 학위 논문 심사(Defense)에 준하는 엄격하고 비판적인 시각으로 제출하신 초안을 검토했습니다. 

본 논문은 ONNX Runtime profiling을 통해 sLLM의 병목을 분석하고 이를 바탕으로 FPGA 가속기 구조를 도출하려는 훌륭한 시도를 담고 있습니다. 그러나 **"분석(CPU Profiling)"과 "해결(FPGA Primitive)" 사이의 논리적 간극이 매우 크며, 논문의 학술적 주장을 방어하기 위해 과도하게 자기 제한적(Self-limiting)인 서술을 남발**하여 오히려 연구의 가치를 스스로 훼손하고 있습니다. 

아래에 논문의 학술적 가치 하락 지점, 논리적 오류, 문장의 중의성, 그리고 구체적인 수정 방향을 조목조목 비판하고 제언합니다. 섹션별 상세 내용은 펼침(Collapse) 메뉴를 확인하시기 바랍니다.

---

<details>
<summary><b>1. 논문으로서 가치 하락 지점 (근본적 한계 및 논리적 비약)</b></summary>

### 1-1. 목표와 결과물의 불일치 (Scope Mismatch)
본 논문의 제목은 "FPGA 기반 Decode 가속기 구조 설계"이나, 실제 구현 및 검증된 하드웨어는 DE10-Lite 보드에서의 `fixed 16x4 INT8 Decode MatVec primitive`에 불과합니다. 
*   **비판:** $16 \times 4$ 크기의 연산은 딥러닝 가속기 설계에서 구조(Architecture)라기보다는 단순한 연산기(MAC unit) 블록에 가깝습니다. 실질적인 LLM의 Projection 레이어 차원인 $N, M \ge 1024$ 수준의 데이터를 처리하기 위한 메모리 계층(Memory Hierarchy), FIFO, AXI 버스 등 **핵심 구조 설계(Architecture Design)에 대한 하드웨어적 증명이 전무**합니다. 
*   **결과:** 제목이 주는 기대감(Full Architecture)과 실제 결과물(Toy Primitive) 사이의 괴리로 인해 논문의 신뢰성이 크게 하락합니다.

### 1-2. CPU Profiling 결과의 FPGA 설계로의 논리적 비약
*   **비판:** 논문은 `CPUExecutionProvider`에서 관측된 MatMul의 실행 시간 비용(%)을 기반으로 FPGA 설계 방향을 정당화합니다. 그러나 **CPU의 병목 현상(주로 Cache Miss, Von Neumann Bottleneck, Memory Bandwidth)이 FPGA 공간 기반 연산(Spatial Computing)의 병목과 1:1로 일치하지 않습니다.**
*   **수학적 함의:** CPU에서 $\mathcal{O}(N^2)$의 병목을 가지는 연산이더라도, FPGA에서는 파이프라인(Pipeline)과 병렬화(Parallelism) 수준에 따라 Latency가 $\mathcal{O}(N)$ 혹은 $\mathcal{O}(1)$로 은닉될 수 있습니다. CPU 프로파일링 결과를 하드웨어 설계의 절대적 당위성으로 치환하는 것은 구조 설계 논문에서 심각한 결격 사유입니다.

### 1-3. JTAG 오버헤드 서술의 비대화
*   **비판:** 하드웨어 가속 연구에서 JTAG을 통한 데이터 통신 오버헤드는 너무나 자명한 사실입니다. 본 논문은 JTAG Latency와 내부 Compute Latency를 분리하는 데 지면을 과도하게 할애하고 있습니다. 이는 마치 "네트워크 프로토콜 개발 논문에서 케이블 꽂는 시간을 제외해야 한다고 길게 변명하는 것"과 같습니다. 학회 전문가들에게는 지루하고 불필요한 서술입니다.
</details>

<details>
<summary><b>2. 실험 방법론 및 데이터의 치명적 결함</b></summary>

### 2-1. 통계적 유의성이 결여된 Profiling (Runs 1, Warmup 0)
*   **현상:** 2.3절 "Long-decode sweep은 runs 1, warmup 0 조건이므로... operator share 경향 확인용 trace로 해석한다."
*   **비판:** 시스템 소프트웨어 및 아키텍처 평가에서 **방향성(Trend) 조사라 할지라도 Cache Cold-start 상태에서의 1회 측정값은 어떠한 학술적 증거로도 채택될 수 없습니다.** OS 스케줄링, 메모리 페이지 폴트(Page Fault), 캐시 상태에 따라 변동성(Variance)이 극심하기 때문입니다. 이를 증거로 "Long-context에서 shape/cache-related overhead가 증가함을 확인하였다"고 주장하는 것은 학문적 기만에 가깝습니다.

### 2-2. Roofline / Design Estimate (표 12)의 허술함
*   **현상:** "Bandwidth-bound"라고 명시하면서도 실제 Memory Bandwidth(GB/s) 수치나 FPGA BRAM/DRAM 대역폭 한계치 대비 Data 요구량을 수식으로 증명하지 않았습니다.
*   **비판:** Roofline 모델을 언급하려면 최소한 Arithmetic Intensity ($\frac{FLOPs}{Byte}$)와 Peak Memory Bandwidth에 기반한 수식이 동반되어야 합니다. 예상 수치(us)만 덩그러니 달아놓은 것은 Architecture exploration으로 인정받기 어렵습니다.
</details>

<details>
<summary><b>3. 문장의 함의, 중의성 및 방어적 글쓰기의 문제점</b></summary>

본 논문은 리뷰어의 공격을 피하기 위해 **과도하게 방어적인 태도("~하지 않는다", "~로 제한한다")**를 취하고 있습니다. 이는 솔직한 한계 명시가 아니라, 연구의 미완성을 변명하는 것으로 읽힘니다.

*   **원문:** "본 연구는 ~ end-to-end inference 결과를 의미하지 않으며... 분리해 병목과 설계 가능성을 분석하기 위한 연구 범위이다." (1.1절)
    *   **비판:** 서론부터 본작의 가치를 깎아내리고 있습니다. 중의적으로 읽히면 "우리는 전체 시스템을 만들 능력이/시간이 없어서 부분만 떼어서 핑계를 만들었다"로 해석됩니다.
    *   **수정 방향:** "본 연구는 sLLM 추론의 핵심 병목인 MatMul 연산의 본질적 특성을 분석하고, 이를 타겟팅한 Hardware Primitive의 기능적 가능성을 검증하는 데 집중한다."로 긍정적으로 서술하십시오.
*   **원문:** "단, JTAG total latency는 System Console/JTAG invocation overhead로만 해석하며, full sLLM 실행 또는 end-to-end ONNX Runtime 성능 개선으로 해석하지 않는다." (초록)
    *   **비판:** 초록은 연구의 가장 빛나는 성과를 적는 곳입니다. 초록에서조차 JTAG 오버헤드를 변명하는 것은 최악의 전개입니다. 
    *   **수정 방향:** 초록에서 JTAG 관련 서술은 완전히 삭제하고, "보드 레벨 측정 결과 $16 \times 4$ MatVec Primitive가 50 MHz 기준 1.3 us의 Compute Latency로 동작함을 확인하여 제안 구조의 하드웨어 실현 가능성을 입증하였다"로 끝맺으십시오.
*   **용어의 모호성:** `Primitive-level validation`이라는 단어를 자의적으로 사용하고 있습니다. FPGA 학계에서는 보통 Microarchitecture 블록 검증이거나 IP Core 검증이라고 칭합니다. Primitive는 LUT, DSP 등 하드웨어 소자를 의미하는 경우가 많아 혼동(중의성)을 유발합니다.
</details>

<details>
<summary><b>4. 조목조목 비평 및 구체적 수정 지시 (Action Items)</b></summary>

### Title & Abstract
*   **문제:** 제목이 너무 거창합니다. 설계된 것은 가속기의 "구조(Architecture)" 전체가 아니라 "연산 코어 블록(Compute Core Block)"의 일부입니다.
*   **수정안:** `ONNX Runtime 기반 온디바이스 스몰 언어모델 추론 병목 분석 및 FPGA 기반 INT8 MatVec 코어 설계` 정도로 Scope을 명확히 하십시오.

### I. 서론
*   **문제:** 관련 연구(1.4)에서 FTRANS, FlightLLM 등을 나열하고 "본 연구는 이와 달리 full model mapping... 제시하지 않는다"라고 적었습니다.
*   **지적:** 선행 연구와 비교해서 본 연구가 **가지는 장점(혹은 차별화되는 니치 마켓)**을 적어야지, 선행 연구보다 **부족한 점만 나열**하면 안 됩니다. "선행 연구들은 Full model mapping에 집중하느라 자원이 제한적인 온디바이스 엣지 환경(예: DE10-Lite)에서의 극소형화 설계 요소는 간과하였다. 본 연구는..." 형식으로 방어(Defense) 논리를 구축하십시오.

### II. 본론
*   *2.3 ORT profiling setup:* `runs=1, warmup=0` 데이터는 삭제하거나, 최소한 `warmup=1, runs=3` 이상의 데이터를 다시 수집하여 반영하십시오. CPU 시간 2분만 더 쓰면 해결될 문제를 방치하는 것은 연구자의 게으름입니다.
*   *3.4 MatMul category 분석 결과:* 
    *   $10546.540 \text{ ms} / 192 = 54.930 \text{ ms/call}$ 과 같은 수식 전개는 평문으로 쓰면 가독성이 떨어집니다. 인라인 수식 달러 기호 연산 $...$ 블록을 활용하거나 표로 명확히 분리하십시오.
*   *5. FPGA 기반 Decode 가속기 구조 (제안 부분):*
    *   **가장 큰 약점입니다.** 제안하는 구조(그림 6)와 실제 구현된 내용(표 7, 8) 사이의 격차가 큽니다. 구조 제안을 할 것이라면, AXI 버스를 통한 메모리 대역폭(Memory Bandwidth)이 `lm_head`의 가중치 스트리밍(Weight Streaming)을 감당할 수 있는지 최소한의 정량적 수식 모델이 있어야 합니다.
    *   예컨대, DE10-Lite SDRAM의 대역폭 한계를 수식 $$ B_{req} = \frac{Weight\_Size}{Target\_Latency} $$ 로 계산하여, 왜 타일링(Tiling) 기법을 제안할 수밖에 없었는지 논리적으로 유도하십시오.

### III. 결론
*   "연구의 한계" 섹션이 결론의 절반을 차지합니다. 스스로 비판받을 공간을 너무 많이 내어주었습니다. 연구의 한계는 짧게 1단락으로 압축하고, 본 연구가 남긴 의의(Contribution)를 강조하는 방향으로 결론을 재작성하십시오.

</details>

---

### 총평 및 디펜스 전략

본 논문 초안은 **엔지니어링 리포트(Engineering Report)로는 훌륭하나, 학술 논문(Academic Paper)으로는 주장의 스케일과 증거의 스케일이 엇박자**를 냅니다. CPU 프로파일링은 방대하고 종합적인 반면, 하드웨어 구현부는 지나치게 협소(`16x4 primitive`)합니다.

이를 극복하기 위해 **방어적인 언어(변명)들을 모두 제거**하시고, "우리가 비록 $16 \times 4$ 크기만 구현했지만, 이는 철저한 분석에 의해 도출된 가장 치명적인 병목 연산(Dense Projection)을 FPGA로 옮겼을 때의 작동을 증명한 핵심 코어(Microarchitecture Core) 설계이다"라는 식으로 **자신감 있게 서술의 톤 앤 매너를 변경**하셔야 합니다. 지적한 통계적 측정 한계(Runs=1)는 반드시 보완 데이터로 교체하십시오.

**Assistant - --**

### Reasoning

The user has provided a long PDF document of a paper titled "ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계". It's a draft, and they want a detailed, critical review as if evaluati...First, the user wants a detailed, critical review of the paper draft, section by section. Evaluate like a PhD thesis defense at a conference: be critical, point out ambiguities, implications that weaken the value, ambiguities in sentences, and suggest revisions.

The paper is in Korean with English parts, titled about ONNX Runtime based on-device small LLM inference bottleneck analysis and FPGA-based Decode accelerator design.

I need to go 조목조목: section by section.

Key weaknesses from my thinking:

- Overclaiming limited scope but presenting as novel.

**종합 평가 (PhD-level / Top-tier conference review 기준)**

이 논문은 **고등학생 수준의 FPGA primitive demo**를 ONNX Runtime profiling 결과와 과도하게 결합해 “FPGA 기반 Decode 가속기 구조 설계”라는 제목과 기여를 주장하는 전형적인 **scope inflation** 논문이다. 

방법론적으로 evidence layer를 철저히 구분하려는 시도는 긍정적이지만, **실질적인 학술 기여가 매우 약하고**, 반복적인 “이것은 full acceleration이 아니다”, “JTAG latency는 overhead다”라는 방어 문장이 논문 전체의 신뢰와 가독성을 크게 떨어뜨린다. 

현재 형태로는 **저널/학회 게재가 매우 어렵다**. 특히 “FPGA 기반 Decode 가속기 구조 설계”라는 제목과 Abstract의 framing 자체가 과장되어 있어, reviewer가 첫 페이지에서 reject 사유를 찾기 쉽다.

### 1. 제목·Abstract·서론 단계의 핵심 문제

**제목**
- “FPGA 기반 Decode 가속기 구조 설계”는 **명백한 overclaim**이다. 
- 실제 구현은 DE10-Lite에서 `inputDim=16, outputDim=4` 고정 크기 INT8 MatVec primitive 하나일 뿐이다. 
- **수정 제안**: 
  - “ONNX Runtime 기반 sLLM 추론 병목 분석 및 Decode-stage MatVec Primitive의 FPGA 구현 검증” 
  - 또는 “Profiling-driven Analysis and Primitive-level Validation toward FPGA Decode Accelerator”

**Abstract (한글·영문 모두)**
- “FPGA 설계 방향을 … decode-stage dense tiled MatVec/MatMul 구조로 설정하였다”라는 문장은 **미래 구조 제안**을 현재 시제로 쓰며 과장한다.
- 65 cycles / 1.3 µs @ 50 MHz primitive 결과만 board-measured evidence로 제시하면서 “FPGA 기반 Decode 가속기 구조 설계”라는 framing을 유지하는 것은 논문의 신뢰를 크게 훼손한다.
- **수정**: “primitive-level validation에 한정하며, full accelerator 성능 개선은 주장하지 않는다”를 Abstract에도 명확히 넣어야 한다.

**서론 1.3 연구 목표와 기여**
- 5가지 기여 중 4번째(“QK 단일 primitive가 아니라 … tiled MatVec/MatMul 구조를 FPGA 설계 방향으로 제안한다”)가 **실질적 기여**로 보기 어렵다. 이는 profiling 결과로부터 당연히 도출되는 방향성일 뿐, 아키텍처 논문 수준의 기여가 아니다.

### 2. 방법론 및 결과 단계의 문제점

**Long-decode sweep (runs=1, warmup=0)**
- 이 sweep을 표 4에 넣고 그림까지 그린 것은 **데이터 신뢰성 문제**를 자초한다. 
- “latency benchmark가 아니라 operator share 경향 확인용”이라고 3번이나 변명하면서도 표와 그림을 크게 배치한 것은 모순이다. 
- **강력 권고**: long-decode sweep은 **부록**으로 옮기거나, 최소한 runs=3, warmup=1로 재측정하거나, 아예 삭제.

**MatMul category 분석**
- `attention_qk_score`가 0.00%로 나온 것은 **분류 규칙의 한계**를 솔직히 인정했지만, graph fallback 분석으로 26개를 confirmed했다고 해도 runtime share는 측정하지 않았다는 점이 약점이다.
- `lm_head`가 call count는 적지만 per-call 비용이 크다는 점은 잘 지적했으나, 이 부분을 hardware design implication으로 더 깊게 연결하지 못했다.

**FPGA 결과 (가장 큰 약점)**
- 16×4 INT8 MatVec primitive를 clean rebuild bitstream으로 만들고 JTAG로 20회 검증한 것은 **undergraduate project** 수준이다.
- Quartus resource usage 5% 이하, Fmax 56 MHz라는 결과는 DE10-Lite라는 초저사양 보드에서 당연한 결과다.
- **reviewer가 가장 공격할 부분**: “이 primitive가 실제 Decode workload에서 어떤 의미가 있는가?”에 대한 답이 없다. 16×4 크기는 MLP나 lm_head 어떤 projection과도 맞지 않는다.

### 3. 논의·결론 단계의 문제

**반복되는 방어 문장**
논문 전체에 걸쳐 “이것은 full sLLM 실행이 아니다”, “JTAG latency는 host-tool overhead다”, “projected estimate는 측정 결과가 아니다”라는 문장이 **20회 이상** 반복된다. 이는 
- 논문의 신뢰를 떨어뜨리고
- reviewer에게 “저자가 스스로도 이 결과가 약하다는 것을 알고 있다”는 인상을 준다.

**FPGA 구조 제안 (5장)**
- 그림 6과 표 11은 **아키텍처 논문** 수준의 설계가 아니다. 
- activation buffer, weight tile streamer, scale/requant unit 등을 나열했지만, 실제 구현된 것은 아무것도 없다. 
- 이는 “future work”로 돌려야 할 내용이다.

### 4. 문장·표현·중의성 문제 (구체적 예시)

| 위치 | 문제 표현 | 왜 문제인가 | 수정 방향 |
|------|-----------|-------------|-----------|
| Abstract | “FPGA 설계 방향을 … 설정하였다” | 현재형 + 과장 | “profiling 결과로부터 도출된 설계 방향성을 제시한다” |
| 1.3 | “주요 기여는 다음과 같다” + 5가지 bullet | 실제 기여 2~3개로 압축 필요 | bullet 수를 줄이고, 각 bullet을 더 구체적으로 |
| 3.3 | long-decode sweep 표 | runs=1 데이터 | 삭제 또는 부록 이동 |
| 5.1 | “비목표도 명확하다” | defensive tone 과다 | 이 단락 자체를 대폭 축소 |
| 표 13, 14 | measured vs projected 혼재 | reviewer 혼동 유발 | measured 행과 projected 행을 시각적으로 명확히 분리 |

### 5. 종합 수정 방향 제안 (우선순위 순)

1. **제목·Abstract 대대적 수정** (가장 중요)
2. **FPGA 결과 부분을 “primitive validation”로 철저히 repositioning**
   - “FPGA 기반 Decode 가속기 구조 설계”라는 framing을 완전히 포기
3. **Long-decode sweep 데이터 삭제 또는 부록화**
4. **반복되는 defensive statement 대폭 삭제** (최대 70% 이상 제거)
5. **5장 (FPGA 구조 제안)**을 “Discussion”의 한 절로 축소하거나, 아예 “Future Work”로 이동
6. **관련 연구 비교**를 대폭 강화 (FlightLLM, DFX, FTRANS 등과 primitive 수준에서라도 비교)
7. **영문 Abstract와 한글 Abstract의 일관성** 확보 (현재 영문이 더 솔직함)

### 최종 의견

현재 논문은 **“고등학생이 ONNX Runtime profiling을 열심히 하고, 아주 작은 primitive를 만들었다”**는 수준의 작업을 학술지 논문으로 포장하려는 시도로 보인다. 

학회/저널에서 통과하려면 **“primitive-level validation”에 솔직하게 초점을 맞추고**, “가속기 구조 설계”라는 과장된 framing을 완전히 포기해야 한다. 

그렇게 하면 **방법론적으로는 괜찮은 undergraduate research paper**가 될 수는 있지만, 박사 과정 논문이나 정상적인 학회 논문으로는 아직 거리가 멀다.

필요하면 각 섹션별로 더 구체적인 수정 문장까지 제안해 드릴 수 있습니다.

**Assistant - --**

최윤혁 연구자님, 제출해주신 논문 초안을 잘 받아보았습니다. 고등학생이라는 점이 믿기지 않을 정도로 **증거 계층(Evidence Layer)을 엄격히 분리하고, 과장(Overclaim)을 경계하는 태도**는 매우 성숙하며 훌륭한 연구자적 자질을 보여줍니다. 

하지만 요청하신 대로 **학회 박사 학위논문 심사위원의 기준**을 적용하여, 논문의 치명적 약점과 가치 하락 지점을 매우 엄격하고 비판적으로 짚어드리겠습니다. 현재 초안은 '현상 관측'과 '면책 조항'에 지나치게 많은 지면을 할애하고 있어, 정작 핵심 기여점(Contribution)이 흐려지는 문제가 있습니다.

다음은 조목조목 비평과 수정 가이드라인입니다.

---

## 1. 논문 가치가 치명적으로 하락하는 지점 (Critical Flaws)

심사 과정에서 즉각적인 'Reject' 또는 'Major Revision' 사유가 될 수 있는 치명적 오류들입니다.

### 1.1. 그림 캡션의 AI 생성 흔적 (Nonsensical Captions)
그림 1, 6 등의 하단에 의미 없는 영문 문장이 포함되어 있습니다.
> *"Existence based on domain expansion. Within graph, ANF+ sentence profiling, most wide forfeited references. While primitive+validation."*
> *"Sequence-general tiled data path for first projection, attention projection, next to, scale output thing, a central acceleration sample, periodic average."*

이는 이미지 생성 AI나 캡션 생성 모델이 만들어낸 **완전한 넌센스(Hallucination)** 입니다. 학술지에 이러한 텍스트가 포함되는 것은 **연구 윤리 및 논문 신뢰도에 치명적**이므로 즉시 삭제하고 정확한 한글/영문 캡션으로 대체해야 합니다.

### 1.2. 치명적 오타 및 용어 혼용
* **`Material` vs `MatMul`**: 3.4절 표 5, 그림 3, 그림 4 등에서 `MatMul`이 `Material`로 표기되어 있습니다. (예: "Material category 분석 결과", "Material 비중"). 이는 논문의 핵심 키워드를 잘못 쓴 것으로, 심사위원으로 하여금 논문 전체의 신뢰도를 의심하게 만듭니다.
* **`prefetch` vs `prefill`**: 2.3절, 3.1절 등에서 `prefill`이 `prefetch`로 잘못 표기되었습니다. LLM 추론에서 Prefill과 CPU의 Prefetch는 완전히 다른 개념입니다.
* **영문 초록의 띄어쓰기 오류**: `CPUE xecutionProvider`, `warmu p`, `a lone` 등 PDF 변환 또는 카피-페이스트 과정에서 발생한 것으로 보이는 오타가 다수 존재합니다.

### 1.3. 내부 아티팩트 ID의 부적절한 노출
표 1~14의 '출처' 란에 `c01`, `c08`, `c16` 등의 코드가 적혀있습니다. 이는 저자의 실험 로그 파일명이나 내부 아티팩트 ID로 판단됩니다. 학술지 표에서는 이를 **"Authors' experiment"** 또는 **"Proposed profiling"** 등으로 표기하거나 아예 생략해야 합니다.

---

## 2. 문장의 함의, 중의성 및 '방어적 서술'의 문제점

현재 논문은 **"이 결과는 ~가 아니다"** 라는 면책 조항(Defensive writing)을 매 섹션마다 반복하고 있습니다. 이는 정직해 보일 수 있으나, 박사논문 수준에서는 **연구의 자신감 부족과 기여점의 희석**으로 비칩니다.

### 2.1. JTAG 오버헤드에 대한 과도한 변명
JTAGtotal latency(약 7.7초)가 호스트 오버헤드이며 FPGA 순수 연산 시간(1.3 us)과 다르다는 점을 **표 8, 표 13, 표 14, 그리고 본문에서 최소 5번 이상 반복**하여 해명하고 있습니다. 
* **비평**: 심사위원은 JTAG이 디버깅용 인터페이스임을 이미 알고 있습니다. 이를 반복해서 변명할수록 "저자는 실제 End-to-End 가속 결과를 내지 못했다는 것을 알고 과도하게 방어하고 있다"는 인상을 줍니다.
* **수정**: 3.6절에서 **"JTAG은 기능 검증(Correctness)용으로만 사용되었으며, 성능 지표는 내부 Cycle Counter 값을 사용한다"** 고 한 번만 명확히 선언한 뒤, 표와 본문에서의 반복 서술을 모두 삭제하십시오.

### 2.2. 한계점의 분산 배치
"~로 해석하지 않는다", "~에 한정된다"는 문장이 서론, 본론, 결론에 산재해 있습니다. 
* **수정**: 실험 결과(3절)에서는 관측된 사실(Fact)만 담백하게 서술하고, 이러한 실험의 전제 조건과 한계는 **2.6절(증거 계층 구분)** 과 **III. 결론(연구의 한계)** 으로 통폐합하여 논문의 흐름(FLOW)이 끊기지 않게 해야 합니다.

---

## 3. 학문적 깊이(Technical Depth)에 대한 비판

박사 학위논문은 '현상 관측'을 넘어 '원인 분석'과 '시스템적 해결'을 요구합니다.

### 3.1. `attention_qk_score`가 0%인 이유에 대한 분석 부재
논문에서는 `attention_qk_score`가 0%인 원인을 "node name/path 기반 분류 규칙의 한계" 및 "이름 매칭 실패"로 돌리고 있습니다. 
* **비평**: 이는 ONNX Runtime(ORT)의 내부 구조에 대한 이해가 부족해 보입니다. ORT는 기본적으로 **Graph Optimization(Fusion)** 을 수행합니다. `MatMul`과 `Add`가 결합되거나, QK dot-product가 `Attention`이라는 단일 Custom Operator로 Fuse되었기 때문에 프로파일러 상에서 `MatMul` 이벤트가 사라진 것일 확률이 99%입니다. 
* **수정**: ORT의 `ORT_ENABLE_ALL` (Graph Optimization Level) 설정에 따라 Fusion이 어떻게 발생했는지, `session.get_providers()` 또는 Graph dump를 통해 Fusion된 Operator를 분석하는 내용을 추가해야 학문적 깊이가 확보됩니다.

### 3.2. Long-decode에서 `Expand + Concat + Unsqueeze` 증가의 본질적 원인
Context 2048에서 해당 연산들의 오버헤드가 17.71%까지 증가하는 현상을 관측한 것은 훌륭한 발견입니다. 하지만 단순히 "shape-related overhead가 증가한다"고만 서술하고 있습니다.
* **비평**: 이는 ORT가 KV-cache를 정적 버퍼(Static Buffer)가 아닌 **동적 텐서(Dynamic Tensor)로 처리**하기 때문입니다. 매 Decode step마다 기존 Cache 텐서와 새로운 KV 텐서를 `Concat`으로 이어붙이면서 Memory Re-allocation과 Copy 오버헤드가 $O(N)$으로 누적되는 것입니다.
* **수정**: 이를 수학적으로 명시하고, 이를 해결하기 위한 시스템적 제안(예: PagedAttention의 ORT 적용, 혹은 Static Shape Buffer 할당 및 In-place update)을 논의(4절)에 포함해야 합니다.

$$ \text{Overhead}_{\text{concat}} \propto \sum_{i=1}^{L} (i \times \text{Hidden\_Dim} \times \text{Head\_Dim}) $$

### 3.3. FPGA 구조 제안의 모호성 (Section 5)
5절의 '가속기 구조 제안'이 너무 일반적인 용어(Activation buffer, Weight streamer 등)로 점철되어 있습니다. 
* **비평**: Gemma 3 1B의 특정 스펙(Hidden size 1152, Vocabulary 262144 등)에 맞춘 **Concrete한 Tiling Strategy**가 빠져있습니다. 
* **수정**: Roofline 모델 분석 시 단순 표기 대신, 대역폭 제한(Bandwidth-bound) 조건을 수식으로 증명하십시오.

$$ t_{\text{stream}} = \frac{W_{\text{bytes}}}{\text{Memory Bandwidth}}, \quad t_{\text{compute}} = \frac{2 \cdot M \cdot N \cdot K}{\text{FLOPS}_{\text{peak}}} $$
$$ \text{If } t_{\text{stream}} > t_{\text{compute}} \text{, then Memory Bound} $$
위 수식을 기반으로 `lm_head` (1152 $\rightarrow$ 262144)가 왜 Memory Bound인지, 이를 해결하기 위해 FPGA 내부 BRAM을 어떻게 Tiling Buffer로 활용할 것인지에 대한 메모리 계층(Memory Hierarchy) 설계도를 추가해야 합니다.

---

## 4. 논문 구조 및 형식적 문제

### 4.1. 장(Chapter) 번호 체계의 불일치
현재 목차는 `I. 서론` $\rightarrow$ `II. 본론` $\rightarrow$ `1. 배경` $\rightarrow$ `1.1` ... $\rightarrow$ `III. 결론` 형태로 되어 있습니다. 
* **수정**: 학술지 표준 형식에 맞게 아라비아 숫자 체계로 통일하십시오.
  * **1. 서론** (1.1 배경, 1.2 필요성, 1.3 기여)
  * **2. 관련 연구**
  * **3. 배경 및 연구 방법** (3.1 ONNX 프로파일링, 3.2 FPGA 설계 방법론)
  * **4. 실험 결과**
  * **5. 논의 및 구조 제안**
  * **6. 결론**

### 4.2. 타이틀과 내용의 괴리 (Overclaim)
* **현재 타이틀**: "... 및 FPGA 기반 Decode 가속기 구조 설계"
* **비평**: 실제 구현 및 검증된 것은 16x4 크기의 'Primitive' 수준입니다. '가속기 구조 설계'라는 타이틀은 심사위원으로 하여금 Full-system 구현을 기대하게 만든 뒤 실망하게 만듭니다.
* **수정**: "... 및 FPGA 기반 Decode **MatVec Primitive 검증과 가속기 구조 제안**"으로 수정하여 타이틀과 내용의 눈높이를 맞추십시오.

---

## 5. 세부 수정 로드맵 (Actionable Items)

<details>
<summary><b>[클릭] 주요 문장 및 섹션별 구체적인 Before/After 수정안</b></summary>

### A. 초록 (Abstract)
* **Before**: "다만 이 long-decode sweep은 runs 1, warmup 0 조건이므로 latency benchmark가 아니라 operator share 경향 확인용 trace로 해석한다."
* **After**: "추가적인 Long-decode Sweep 분석을 통해, 컨텍스트 길이가 증가할수록 MatMul 외의 동적 Shape manipulation 오버헤드가 누적됨을 규명하였다." *(면책 조항은 본문 연구 방법/한계점으로 이동)*

### B. 서론 (Introduction)
* **Before**: "본 연구에서 온디바이스 조건은 cloud offload 없이... 이는 실제 모바일 NPU...에서의 end-to-end inference 결과를 의미하지 않으며..."
* **After**: "본 연구는 온디바이스 엣지 환경을 선행 분석하기 위해, 호스트 CPU의 ONNX Runtime 실행 계층과 FPGA Primitive 검증 계층을 체계적으로 분리한 병목 분석 프레임워크를 제안한다." *(부정적 정의 대신 긍정적 정의로 서술)*

### C. 실험 결과 (Results) - JTAG 변명 삭제
* **Before**: (표 8, 13, 14 및 본문에서 JTAG이 느리다는 것을 장황하게 해명)
* **After**: "FPGA 보드 검증은 기능적 정합성(Correctness) 확인을 위해 JTAG-to-Avalon 인터페이스를 활용하였으며, 호스트 오버헤드를 배제하기 위해 RTL 내부에 구현된 Cycle Counter 레지스터 값을 순수 연산 성능 지표로 채택하였다." *(이 한 문장으로 모든 표의 Note를 대체)*

### D. 논의 (Discussion) - KV-cache Concat 오버헤드 분석 추가
* **추가할 내용**: "ORT의 기본 Graph 실행 방식은 KV-cache 업데이트 시 `Concat` 연산을 사용하며, 이는 매 Decode step마다 $O(L \cdot D)$ 크기의 메모리 재할당과 복사를 유발한다. 2048 컨텍스트에서 17.71%의 오버헤드는 이러한 동적 텐서 관리 비용에서 기인한 것으로 분석된다."

</details>

---

## 💡 총평 및 심사위원의 제언

최윤혁 연구자님의 논문은 **"무엇을 하지 않았는가(What we didn't do)"를 설명하는 데 너무 많은 에너지**를 쓰고 있습니다. 박사와 석사의 논문의 가장 큰 차이는 '방어의 완전성'이 아니라 **'통찰의 깊이와 시스템적 제안의 구체성'** 에 있습니다.

1. **AI 생성 캡션과 오타(`Material` 등)를 즉시 수정**하여 논문의 기본적 품격을 갖추십시오.
2. ORT의 **Operator Fusion**과 **동적 KV-cache Concat 오버헤드**에 대한 기술적 통찰을 본문에 녹이십시오.
3. JTAG 오버헤드에 대한 변명을 지우고, 그 지면에 **Gemma 3 1B에 최적화된 FPGA Tiling 전략(수식 및 메모리 계층 분석)** 을 채우십시오.

이 세 가지 방향성만 수정된다면, 본 논문은 단순한 '학생 수준의 실험 보고서'를 넘어, 온디바이스 LLM 추론 스택(Runtime-Hardware Boundary)의 병목을 날카롭게 짚어낸 **매우 우수한 학술지 논문**으로 재탄생할 수 있을 것입니다. 수정을 응원합니다.

**User - --**

다시 개선해왔어. 2차 수정안을 동일한 조건으로 평가해줘
```markdown
# 한국정보기술진흥원 학술지 / Vol.3 No.2, 2026 하계

# 온디바이스 ONNX Runtime sLLM 추론의 Decode 병목 분석과 FPGA 기반 INT8 MatVec 가속기 구조 제안

**Decode Bottleneck Analysis of On-device ONNX Runtime sLLM Inference and an FPGA-based INT8 MatVec Accelerator Architecture Proposal**

최윤혁

한국디지털미디어고등학교

Yunhyuk Choi

Korea Digital Media High School

## 초록

온디바이스 소형 언어모델(sLLM) 추론에서는 모델 크기뿐 아니라 ONNX graph 구조, execution provider, quantization 상태, decode cache 처리 방식, host/offload interface가 token 단위 실행 비용을 결정한다. 본 연구는 Gemma 계열 sLLM의 ONNX Runtime profiling 결과와 대표 projection micrograph manifest를 바탕으로 decode 단계의 병목을 분석하고, 이를 FPGA 기반 INT8 MatVec 구조 요구사항 및 저자 후속 구조 제안으로 정리한다. 기존 ONNX Runtime CPUExecutionProvider profiling에서는 MatMul이 decode trace node 시간의 81.1%를 차지했으며, MatMul 내부에서는 `mlp_projection`과 `lm_head`가 88.90%를 차지했다. Lenovo Y700(TB320FC, Snapdragon 8+ Gen 1급 taro platform)에서는 ONNX Runtime 1.27.0 Android APK로 representative projection micrograph를 실행했다. INT8 MatMulInteger p50 latency는 CPU EP에서 attention output 0.738 ms, `lm_head` tile 3.582 ms, MLP projection 3.428 ms였고, NNAPI EP에서는 각각 0.518 ms, 2.989 ms, 3.333 ms였다. QNN EP는 사용한 AAR build에서 지원되지 않아 integration blocked로 기록했다. FPGA 측면에서는 DE10-Lite에서 16x4 INT8 MatVec primitive의 board-level correctness를 확인했고, 20회 JTAG-to-Avalon 호출에서 CPU reference와 동일한 결과 및 internal cycle counter 기준 65 cycles, 1.3 us @ 50 MHz를 확보했다. 이 1.3 us 값은 64 MAC smoke-test core의 기능 검증 anchor이며, 빠른 AI 가속 성능이나 ONNX Runtime 대비 우위로 해석하지 않는다. JTAG total latency는 host-tool invocation overhead로만 분리한다. 저자 후속 구조 제안은 1.58bit 계열 변환 기반 가산기 accelerator, 병목 offload FPGA, SRAM-like scratchpad FPGA, DDR2/LPDDR2 다채널 weight memory를 결합하는 memory-centric low-bit MatVec 방향으로 정리한다.

**키워드:** ONNX Runtime, 온디바이스 추론, 소형 언어모델, decode, MatMul, MatVec, FPGA, INT8, DE10-Lite

## Abstract

On-device small language model inference is shaped not only by model size, but also by ONNX graph structure, execution providers, quantization state, decode-cache handling, and host/offload interfaces. This study analyzes decode-stage bottlenecks using ONNX Runtime profiling results and representative projection micrograph manifests for Gemma-class sLLM workloads, then summarizes the observed workload characteristics as requirements for an FPGA-based INT8 MatVec path and as an author-proposed follow-up architecture direction. In the existing ONNX Runtime CPUExecutionProvider profile, MatMul accounts for 81.1% of traced decode node time, while `mlp_projection` and `lm_head` together account for 88.90% of MatMul time. On a Lenovo Y700 Android tablet, an ONNX Runtime 1.27.0 APK benchmark reports INT8 MatMulInteger p50 latencies of 0.738 ms, 3.582 ms, and 3.428 ms for attention-output, `lm_head` tile, and MLP projection micrographs on the CPU EP; the corresponding NNAPI EP p50 latencies are 0.518 ms, 2.989 ms, and 3.333 ms. QNN EP is recorded as integration blocked because it is not supported in the tested AAR build. On the FPGA side, a 16x4 INT8 MatVec primitive is validated on DE10-Lite with board-level correctness: 20 JTAG-to-Avalon invocations match the CPU reference, and the internal cycle counter reports 65 cycles, or 1.3 us at 50 MHz. The 1.3 us value is a functional verification anchor for a 64-MAC smoke-test core, not evidence of fast AI acceleration or superiority over ONNX Runtime. JTAG total latency is separated as host-tool invocation overhead. The follow-up architecture direction is framed as a memory-centric low-bit MatVec design that combines 1.58-bit-family conversion, adder-based acceleration, bottleneck offload FPGA logic, SRAM-like scratchpad reuse, and multi-channel DDR2/LPDDR2 weight memory.

**Keyword:** ONNX Runtime, on-device inference, small language model, decode, MatMul, MatVec, FPGA, INT8, DE10-Lite

## 1. 서론

온디바이스 sLLM 추론은 클라우드 의존성을 낮추고 개인정보 보호와 저지연 응답 가능성을 제공하지만, 실제 배포 계층에서는 모델 파라미터 수만으로 병목을 설명하기 어렵다. Autoregressive language model은 prompt 전체를 처리하는 prefill과 다음 token을 반복 생성하는 decode로 나뉜다. Decode에서는 token dimension이 작아지더라도 hidden dimension, projection dimension, cache tensor의 lifetime은 유지되므로 각 token마다 projection, cache access, graph-level shape operation이 결합된다.

본 연구는 FPGA가 전체 모델을 더 빠르게 실행했다는 성능 주장이 아니라, ONNX Runtime에서 관측되는 decode 병목을 분석하고 이를 FPGA INT8 MatVec/MatMul 구조 요구사항으로 변환하는 것을 목표로 한다. 특히 기존 LLM accelerator 논의가 attention 또는 QK score 중심으로 흐르기 쉬운 점을 고려하여, 실제 ONNX Runtime trace에서 MLP projection과 `lm_head`가 차지하는 비중을 확인하고, QK-only가 아닌 projection-heavy low-bit MatVec/MatMul 경로의 필요성을 검토한다.

본 연구의 기여는 세 가지이다. 첫째, ONNX export, graph inspection, runtime profiling, Android/Y700 실행 하네스, FPGA primitive 검증을 증거 계층별로 분리한다. 둘째, MatMul 중에서도 `mlp_projection`과 `lm_head`가 큰 비중을 차지한다는 점을 바탕으로 memory-centric low-bit MatVec/MatMul 구조 요구사항을 도출한다. 셋째, DE10-Lite 16x4 INT8 MatVec primitive의 board-level correctness와 cycle-counter anchor를 제시하되, 이를 full accelerator 성능으로 해석하지 않고 저자 후속 구조 제안의 검증 출발점으로 둔다.

![그림 1. 전체 연구 흐름](../../paper_assets/figures/research_flow.png)

그림 1은 Android/Y700 실행 경로, ONNX Runtime 분석, FPGA core validation, projection-scale roofline/interface model을 서로 다른 증거 계층으로 분리한 연구 흐름을 나타낸다.

## 2. 관련 연구 및 배경

Transformer 추론에서 prefill은 입력 prompt 전체를 한 번에 처리하고, decode는 cache를 참조하며 token을 순차적으로 생성한다. Decode 단계는 batch와 token dimension이 작아질 수 있지만, 각 layer의 MLP projection, attention projection, `lm_head` projection은 반복된다. 따라서 decode 병목은 attention score 계산뿐 아니라 dense projection, cache movement, graph-level shape operation을 함께 보아야 한다.

KV-cache는 long-context decode에서 핵심 구조이다. Orca는 autoregressive serving에서 iteration-level scheduling의 중요성을 보였고[10], vLLM/PagedAttention은 KV-cache를 block 단위로 관리하여 memory fragmentation과 scheduling 문제를 줄이는 방향을 제시했다[3]. FlashAttention 계열 연구는 attention kernel의 I/O-aware tiling과 work partitioning을 최적화한다[4][11]. 이러한 연구들은 decode와 memory movement의 중요성을 보여주지만, 본 연구는 serving scheduler나 attention kernel 자체를 구현하지 않는다.

ONNX Runtime은 graph optimization과 execution provider를 통해 같은 ONNX graph라도 CPU, NNAPI, QNN 등 다양한 경로로 실행할 수 있다[9]. 온디바이스 배포에서는 provider 선택, quantization state, graph rewrite가 병목을 크게 바꿀 수 있다. 본 연구는 현재 확보된 CPUExecutionProvider trace와 Android 실행 하네스를 분리하여, 측정된 값과 아직 실행되지 않은 경로를 혼동하지 않는다.

FPGA 기반 transformer accelerator 연구로는 FTRANS, DFX, FlightLLM 등이 있다[8][12][13]. 이 연구들은 full model mapping, multi-FPGA appliance, complete mapping flow 등 더 큰 시스템 범위를 다룬다. 본 연구는 이와 달리 full model FPGA 실행이나 custom ONNX Runtime execution provider를 제시하지 않는다. 대신 ONNX Runtime profiling에서 도출된 projection-heavy primitive를 대상으로, 어떤 memory-centric low-bit MatVec 요구사항이 필요한지 분석하고, 최소 INT8 MatVec core가 실제 보드에서 동작함을 확인한다.

## 3. 실험 방법

본 연구의 증거 계층은 표 1과 같이 구분한다. 이 구분은 측정값, 시뮬레이션, projected model, invocation overhead가 같은 성능 순위처럼 읽히지 않도록 하기 위한 핵심 방법론이다.

**표 1. 실험 환경 및 증거 계층 요약**

| 환경 | evidence type | 상태 | claim boundary |
| --- | --- | --- | --- |
| Lenovo Y700 Android | measured APK micrograph | completed | CPU/NNAPI latency 확보, QNN integration blocked |
| ONNX Runtime CPU profile | measured host profile | 기존 profiling artifact | Ryzen/host CPUExecutionProvider trace, Y700 측정 아님 |
| ONNX micrograph manifest | graph evidence | available | 대표 graph shape 확인, Gemma 전체 모델 실행 아님 |
| DE10-Lite INT8 MatVec | board_measured | pass 20/0 | 16x4 core correctness 및 internal cycle anchor |
| Projection roofline | projected | model only | measured latency가 아닌 bandwidth/weight-movement estimate |
| 저자 후속 구조 제안 | proposal | not implemented | 1.58bit 변환, scratchpad FPGA, DDR2/LPDDR2 다채널 memory는 구현 결과가 아님 |

Lenovo Y700 경로에서는 `adb`로 연결된 TB320FC 장치에서 ONNX Runtime 1.27.0 Android APK를 실행했다. 장치는 Android 15, arm64-v8a ABI, Qualcomm taro platform으로 확인되었으며, `/proc/meminfo`의 MemTotal은 15,578,208 kB로 기록되었다. APK는 ONNX model을 asset으로 포함하고 `session.run` wall-clock latency를 warmup 3회, 측정 20회로 기록한다. CPUExecutionProvider와 NNAPIExecutionProvider는 실행되었고, QNNExecutionProvider는 사용한 AAR build의 available provider 목록에 없어 integration blocked로 기록했다.

**표 2. Lenovo Y700 ONNX Runtime projection micrograph 결과**

| micrograph | dtype/op | CPU EP p50 | NNAPI EP p50 | QNN EP |
| --- | --- | ---: | ---: | --- |
| attention output 1024x1152 | INT8 MatMulInteger | 0.738 ms | 0.518 ms | integration blocked |
| `lm_head` tile 1152x4096 | INT8 MatMulInteger | 3.582 ms | 2.989 ms | integration blocked |
| MLP projection 1152x6912 | INT8 MatMulInteger | 3.428 ms | 3.333 ms | integration blocked |
| smoke 16x4 | INT8 MatMulInteger | 0.051 ms | 0.159 ms | integration blocked |

대표 micrograph는 표 3과 같이 생성하였다. 파일명은 intended role을 나타낼 수 있으나, 본 논문에서는 graph inspection으로 확인한 operator, dtype, tensor shape를 기준으로 해석한다.

**표 3. ONNX micrograph manifest 요약**

| model | op | input x weight -> output | dtype |
| --- | --- | --- | --- |
| `matvec_cpu_baseline.onnx` | MatMul | 1x16 x 16x4 -> 1x4 | FLOAT |
| `matvec_int8_matmulinteger.onnx` | MatMulInteger | 1x16 x 16x4 -> 1x4 | INT8 -> INT32 |
| `gemma_mlp_projection_1152x6912_float.onnx` | MatMul | 1x1152 x 1152x6912 -> 1x6912 | FLOAT |
| `gemma_mlp_projection_1152x6912_matmulinteger.onnx` | MatMulInteger | 1x1152 x 1152x6912 -> 1x6912 | INT8 -> INT32 |
| `gemma_lm_head_tile_1152x4096_float.onnx` | MatMul | 1x1152 x 1152x4096 -> 1x4096 | FLOAT |
| `gemma_lm_head_tile_1152x4096_matmulinteger.onnx` | MatMulInteger | 1x1152 x 1152x4096 -> 1x4096 | INT8 -> INT32 |
| `gemma_attention_output_projection_1024x1152_float.onnx` | MatMul | 1x1024 x 1024x1152 -> 1x1152 | FLOAT |
| `gemma_attention_output_projection_1024x1152_matmulinteger.onnx` | MatMulInteger | 1x1024 x 1024x1152 -> 1x1152 | INT8 -> INT32 |

FPGA 검증은 SpinalHDL 기반 INT8 MatVec core, Verilator simulation, Quartus clean rebuild, DE10-Lite JTAG-to-Avalon register invocation으로 구성된다. JTAG path는 correctness/debug path이며, performance interface로 해석하지 않는다.

## 4. ONNX Runtime 및 Micrograph 병목 분석

기존 ONNX Runtime CPUExecutionProvider profiling에서는 decode trace node 시간 중 MatMul이 81.1%를 차지했다. Prefill과 decode를 합산한 trace node 시간에서는 MatMul share가 67.5%, prefill에서는 53.4%였다. Long-decode trace에서도 MatMul은 주요 operator group으로 유지되지만, context 2048과 decode 256 조건에서는 `Expand + Concat + Unsqueeze` 합산 비중이 17.71%까지 증가했다. 이 결과는 decode 병목이 dense projection만으로도, KV-cache만으로도 완전히 설명되지 않으며 두 계층을 함께 다뤄야 함을 의미한다.

**표 4. ONNX Runtime profiling 기반 decode 병목 요약**

| 측정 범위 | 주요 결과 | 해석 |
| --- | ---: | --- |
| decode MatMul share | 81.1% | CPUExecutionProvider trace node time 기준 |
| prefill+decode MatMul share | 67.5% | host CPU profiling artifact |
| `mlp_projection + lm_head` share | 88.90% of MatMul | projection-heavy workload |
| context 2048, decode 256 shape/cache ops | 17.71% | `Expand + Concat + Unsqueeze`, exploratory trace |

MatMul category 분석에서는 `mlp_projection`과 `lm_head`가 전체 MatMul 시간의 88.90%를 차지했다. 따라서 후속 FPGA 구조 요구사항은 QK dot-product 전용 block보다 MLP, attention projection, `lm_head`에 공통 적용 가능한 low-bit MatVec/MatMul 처리를 우선 고려해야 한다. `attention_qk_score`가 runtime classifier에서 0.00%로 나타난 것은 QK 연산 부재가 아니라, 현재 event classifier에서 확정 가능한 MatMul event가 없었다는 뜻으로 제한한다.

Long-decode sweep의 일부 결과는 runs 1, warmup 0 조건으로 수집된 exploratory trace이다. 그러므로 latency benchmark로 해석하지 않고 operator share 경향으로만 사용한다. 최종 온디바이스 latency 판단은 Y700 APK micrograph benchmark를 우선한다.

![그림 2. Lenovo Y700 ONNX Runtime INT8 projection micrograph 결과](../../paper_assets/figures/y700_onnx_runtime_bottleneck.png)

그림 2는 INT8 MatMulInteger projection micrograph의 p50 latency를 CPU EP와 NNAPI EP로 나누어 나타낸다. 16x4 smoke graph에서는 provider dispatch overhead가 지배적이므로 구조 비교에 쓰지 않고, 1024~6912 output dimension의 projection micrograph를 decode offload 후보의 대표 latency로 본다.

## 5. 병목 분석 기반 FPGA 구조 요구사항과 저자 후속 구조 제안

**저자 검토 필요:** 본 절은 사용자가 제시한 후속 구조 아이디어를 논문 문장으로 정리한 초안이다. 본 연구에서 구현하고 실측한 FPGA 하드웨어는 DE10-Lite 16x4 INT8 MatVec primitive에 한정된다.

Y700 micrograph와 기존 ONNX Runtime profiling은 같은 결론을 가리킨다. Decode 경로에서 반복되는 projection-heavy MatVec/MatMul은 작은 16x4 연산보다 1024~6912 output dimension을 갖는 projection tile에서 의미 있게 관측된다. 따라서 후속 FPGA 구조는 단순히 MAC core cycle을 줄이는 방향보다 weight movement, activation reuse, partial sum reuse, output tile 처리, provider/runtime 호출 경계의 비용을 함께 줄이는 memory-centric low-bit MatVec 구조가 되어야 한다.

**표 5. ONNX Runtime 병목에서 도출한 하드웨어 요구사항**

| 요구사항 | 근거 | 구조적 의미 | 본 논문 상태 |
| --- | --- | --- | --- |
| projection-heavy MatVec/MatMul 우선 | `mlp_projection + lm_head`가 MatMul 시간의 88.90% | QK 전용보다 MLP, attention output, `lm_head` 공통 경로 고려 | 분석 결과 |
| low-bit weight resident 경로 | `lm_head`/MLP tile의 weight movement가 큼 | weight를 반복 전송하지 않는 memory-centric 배치 필요 | 요구사항 |
| activation/partial sum 재사용 | decode는 token 단위 반복 실행 | activation, partial sum, hot tile, output tile buffer 재사용 필요 | 저자 후속 제안 |
| provider/runtime 호출 경계 축소 | 16x4 micrograph는 dispatch overhead 영향이 큼 | 작은 primitive 비교보다 projection-scale boundary 설계 필요 | 분석 결과 |
| graph/cache 처리와 분리된 claim | long-decode에서 shape/cache op 비중 증가 | accelerator 단독 주장보다 graph/runtime specialization과 함께 검토 | 후속 과제 |

저자 후속 구조 제안은 일반 모델을 1.58bit 계열 모델로 변환한 뒤, 곱셈기 중심 datapath 대신 가산기 기반 accelerator를 구성하는 방향이다. 이 제안은 본 논문에서 구현한 결과가 아니라, Y700 병목 분석에서 도출된 projection-heavy MatVec/MatMul 요구사항을 바탕으로 한 후속 연구 방향이다. 구체적으로는 병목 offload용 FPGA NPU, activation과 partial sum 및 hot tile을 재사용하기 위한 SRAM-like scratchpad FPGA, 그리고 DDR2 또는 LPDDR2 기반 low-power weight memory를 결합하는 custom board 방향을 검토한다.

DDR2/LPDDR2는 최신 HBM이나 LPDDR5보다 die당 용량과 단일 채널 대역폭은 작지만, controller 구조가 비교적 단순하고 독립 channel 또는 interleaved group을 늘려 aggregate bandwidth를 높일 수 있다는 장점이 있다. 예를 들어 4Gbit DRAM die 8개 또는 16개를 weight memory로 구성하면 이론 용량은 각각 4GB 또는 8GB가 된다. 본 논문은 이러한 custom board, SRAM-like FPGA, 1.58bit 변환기, Y700-FPGA offload path를 구현했다고 주장하지 않는다.

## 6. DE10-Lite INT8 MatVec primitive 검증 결과

현재 board-measured 결과는 DE10-Lite의 fixed 16x4 INT8 MatVec primitive에 한정된다. 해당 core는 64 MAC smoke-test workload를 수행하며, 새 Verilog mirror를 Windows Pocket4의 Quartus 25.1std Lite에서 clean compile한 뒤 DE10-Lite에 programming하여 20회 JTAG-to-Avalon invocation을 수행했다. 결과는 `pass_count=20`, `fail_count=0`이며 CPU reference와 동일한 result vector를 기록했다. Internal cycle counter는 65 cycles, 50 MHz 기준 1.3 us를 보고했다.

이 1.3 us 값은 빠른 AI 가속 성능이 아니다. 64 MAC smoke-test core가 보드에서 올바르게 동작하고 내부 cycle counter가 예상 범위의 cycle을 보고했다는 기능 검증 anchor이다. 또한 JTAG total latency의 mean/p50/p95 7756.114875 / 7755.08985 / 7775.94519 ms는 System Console host-tool invocation overhead이며, 1.3 us internal compute time과 별개의 물리량이다. 따라서 두 값을 ONNX Runtime latency와 같은 축의 성능 비교로 배치하지 않는다.

**표 6. DE10-Lite board validation summary**

| 항목 | 값 |
| --- | ---: |
| input/output dimension | 16 / 4 |
| MACs | 64 |
| pass_count / fail_count | 20 / 0 |
| compute cycles | 65 |
| compute time | 1.3 us @ 50 MHz |
| logic elements | 2,560 / 49,760 |
| DSP 9-bit elements | 1 / 288 |
| memory bits | 512 / 1,677,312 |
| Fmax | 56.670 MHz |

## 7. Memory/Interface 요구사항과 후속 구조 방향

Projection-scale model은 weight movement와 interface bandwidth가 실제 offload 가능성을 지배할 수 있음을 보여준다. 예를 들어 full `lm_head` 1152->262144 projection은 token당 약 3.02억 MAC과 약 302 MB의 INT8 weight movement를 요구한다. 16 lanes, 50 MHz 가정에서 compute estimate는 약 377 ms이고, USB3 320 MB/s streaming estimate는 약 947 ms이므로, 단순히 FPGA core cycle만 줄인다고 실사용 latency 개선을 주장할 수 없다.

![그림 3. Projection-scale roofline 해석](../../paper_assets/figures/fpga_roofline_or_latency_decomposition.png)

**표 7. Projection tile roofline/interface model 요약**

| component | evidence type | shape | lanes | interface case | compute/stream model |
| --- | --- | --- | ---: | --- | --- |
| MLP gate/up projection | projected | 1152->6912 | 16 | USB3 320 MB/s | compute 9.95 ms, stream 24.97 ms |
| lm_head full projection | projected | 1152->262144 | 16 | USB3 320 MB/s | compute 377.49 ms, stream 947.00 ms |
| lm_head tile | projected | 1152->4096 | 16 | USB3 320 MB/s | projection tile model |

FPGA 간 연결은 본질적으로 불가능하거나 반드시 매우 느린 경로가 아니다. 다만 연산용 FPGA와 SRAM-like scratchpad용 FPGA를 custom connector로 연결하려면 pin count, signal integrity, clock-domain crossing, protocol, aggregate bandwidth, board design 난이도가 함께 증가한다. 따라서 본 논문에서는 해당 custom board를 구현 결과로 쓰지 않고, 병목 분석에서 도출된 후속 구조 요구사항으로만 정리한다.

**표 8. 저자 후속 구조 제안과 해결하려는 병목**

| 구조 후보 | 해결하려는 병목 | 논문 내 지위 | 주의할 claim boundary |
| --- | --- | --- | --- |
| 1.58bit 계열 변환 + 가산기 accelerator | INT8/FP16 곱셈기 중심 MatVec의 area/energy 부담 | 저자 후속 구조 제안 | 변환기나 학습/양자화 flow를 제작한 결과가 아님 |
| 병목 offload FPGA NPU | projection-heavy MatVec/MatMul 반복 비용 | 저자 후속 구조 제안 | Android-FPGA 통합 실측 결과가 아님 |
| SRAM-like scratchpad FPGA | activation, partial sum, hot tile, cache metadata, output tile buffer 재사용 | 저자 후속 구조 제안 | scratchpad board 구현 결과가 아님 |
| DDR2/LPDDR2 다채널 weight memory | large projection weight residency와 aggregate bandwidth | custom board 후보 | 4Gbit die 8~16개는 이론적 4GB~8GB 구성 예시 |
| compute FPGA와 scratchpad FPGA 간 custom connector | memory와 compute 분리 시 bandwidth 제공 | 후속 산출물/포트폴리오 방향 | pin 수, SI, CDC, protocol, board design 검증 필요 |

## 8. 논의 및 결론

본 연구의 결론은 FPGA의 전체 실행 우위를 보였다는 것이 아니라, ONNX Runtime decode trace와 Y700 micrograph에서 projection-heavy workload가 뚜렷하게 나타나며, 이를 FPGA로 옮기려면 memory-centric low-bit MatVec/MatMul 구조 요구사항을 먼저 만족해야 한다는 것이다. KV-cache와 shape-related operator는 long-context decode에서 중요하지만, 현재 evidence에서는 dense projection을 배제한 QK-only 설계가 충분하지 않다.

Y700 실험은 Gemma 전체 모델 실행이 아니라 representative ONNX micrograph benchmark이다. 그럼에도 CPU EP와 NNAPI EP에서 projection-scale MatMul/MatMulInteger latency를 확보했기 때문에, 기존 host-only profiling보다 온디바이스 근거가 강화되었다. QNN EP는 tested AAR build에서 지원되지 않아 integration blocked로 기록했으며, QNN SDK/Qualcomm AI Engine Direct 기반 build가 확보되면 별도 비교가 필요하다.

FPGA 측면에서는 DE10-Lite 16x4 INT8 MatVec 결과가 기능 검증과 cycle 측정 anchor로는 의미가 있지만, projection-scale acceleration을 주장하기에는 interface와 bandwidth가 결정적이다. 저자 후속 구조 제안은 1.58bit 계열 변환 기반 가산기 accelerator, 병목 offload FPGA, SRAM-like scratchpad FPGA, DDR2/LPDDR2 다채널 weight memory를 결합하는 방향이다. 이 제안은 본 논문의 구현 결과가 아니라, 온디바이스 ONNX Runtime 병목 분석에서 출발한 다음 설계 과제이다.

## 참고문헌

[1] Shuming Ma, Hongyu Wang, Lingxiao Ma, Lei Wang, Wenhui Wang, Shaohan Huang, Li Dong, Ruiping Wang, Jilong Xue, and Furu Wei. "The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits." arXiv preprint arXiv:2402.17764, 2024.

[2] Rui-Jie Zhu, Yu Zhang, Steven Abreu, Ethan Sifferman, Tyler Sheaves, Yiqiao Wang, Dustin Richmond, Sumit Bam Shrestha, Peng Zhou, and Jason K. Eshraghian. "Scalable MatMul-free Language Modeling." arXiv preprint arXiv:2406.02528, 2024.

[3] Woosuk Kwon, Zhuohan Li, Siyuan Zhuang, Ying Sheng, Lianmin Zheng, Cody Hao Yu, Joseph E. Gonzalez, Hao Zhang, and Ion Stoica. "Efficient Memory Management for Large Language Model Serving with PagedAttention." arXiv preprint arXiv:2309.06180, 2023.

[4] Tri Dao, Daniel Y. Fu, Stefano Ermon, Atri Rudra, and Christopher Ré. "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness." arXiv preprint arXiv:2205.14135, 2022.

[5] Elias Frantar, Saleh Ashkboos, Torsten Hoefler, and Dan Alistarh. "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers." arXiv preprint arXiv:2210.17323, 2022.

[6] Guangxuan Xiao, Ji Lin, Mickael Seznec, Hao Wu, Julien Demouth, and Song Han. "SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models." arXiv preprint arXiv:2211.10438, 2022.

[7] Ji Lin, Jiaming Tang, Haotian Tang, Shang Yang, Wei-Ming Chen, Wei-Chen Wang, Guangxuan Xiao, Xingyu Dang, Chuang Gan, and Song Han. "AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration." arXiv preprint arXiv:2306.00978, 2023.

[8] Shulin Zeng, Jun Liu, Guohao Dai, Xinhao Yang, Tianyu Fu, Hongyi Wang, Wenheng Ma, Hanbo Sun, Shiyao Li, Zixiao Huang, Yadong Dai, Jintao Li, Zehao Wang, Ruoyu Zhang, Kairui Wen, Xuefei Ning, and Yu Wang. "FlightLLM: Efficient Large Language Model Inference with a Complete Mapping Flow on FPGAs." arXiv preprint arXiv:2401.03868, 2024.

[9] Microsoft. "ONNX Runtime Execution Providers" and "Graph Optimizations." ONNX Runtime Documentation, https://onnxruntime.ai/docs/execution-providers/ and https://onnxruntime.ai/docs/performance/model-optimizations/graph-optimizations.html, accessed 2026-06-29.

[10] Gyeong-In Yu, Joo Seong Jeong, Geon-Woo Kim, Soojeong Kim, and Byung-Gon Chun. "Orca: A Distributed Serving System for Transformer-Based Generative Models." In 16th USENIX Symposium on Operating Systems Design and Implementation (OSDI 22), pp. 521-538, 2022.

[11] Tri Dao. "FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning." In 12th International Conference on Learning Representations (ICLR), 2024.

[12] Seongmin Hong, Seungjae Moon, Junsoo Kim, Sungjae Lee, Minsub Kim, Dongsoo Lee, and Joo-Young Kim. "DFX: A Low-latency Multi-FPGA Appliance for Accelerating Transformer-based Text Generation." In Proceedings of the 55th IEEE/ACM International Symposium on Microarchitecture (MICRO), pp. 616-630, 2022.

[13] Bingbing Li, Santosh Pandey, Haowen Fang, Yanjun Lv, Ji Li, Jieyang Chen, Mimi Xie, Lipeng Wan, Hang Liu, and Caiwen Ding. "FTRANS: Energy-Efficient Acceleration of Transformers using FPGA." In ACM/IEEE International Symposium on Low Power Electronics and Design (ISLPED), pp. 175-180, 2020.

## 저자정보

최윤혁

한국디지털미디어고등학교

ORCID: [0009-0006-3537-0249](https://orcid.org/0009-0006-3537-0249)

```

**Assistant - --**

2차 수정안을 1차와 동일한 기준(학회·학위 심사 톤)으로 평가합니다. 결론부터 말하면 **원고의 완성도(craft)는 분명히 올라갔으나, 1차에서 지적한 근본 결함은 해결되지 않았고, 오히려 새로 추가한 부분에서 새로운 약점이 생겼습니다.**

## 총평 (Verdict)

<details open>
<summary><b>핵심 진단: "정직함"은 유지·강화됐지만, 이번엔 논문의 데이터가 스스로 자기 주장을 반증한다</b></summary>

1차의 핵심 비판은 "두 축(병목 분석 ↔ FPGA)이 측정으로 연결되지 않는다"였습니다. 2차는 Y700 온디바이스 측정을 추가해 *동기(motivation)의 대표성*을 상당히 보강했습니다. 이건 진짜 진전입니다.

그러나 대가로 **roofline에 실제 숫자가 들어오면서, 그 숫자들이 이 논문의 FPGA 방향이 무의미하다는 것을 정량적으로 증명해 버렸습니다.** 표 7을 보면:

- `lm_head` full projection: FPGA compute 377 ms, USB3 stream **947 ms**
- 같은 `lm_head` tile: Y700 NNAPI EP **2.989 ms**

즉 논문이 제안하는 FPGA offload 경로는, 그것이 도우려는 대상인 **휴대폰 NNAPI보다 두세 자릿수 느립니다.** 저자는 이 숫자를 정직하게 실었지만, **"그러므로 이 방향이 왜 정당한가"라는 질문에 답하지 않고 넘어갑니다.** 1차에서는 "다리가 없다"였다면, 2차에서는 "다리를 놓아 보니 절벽으로 이어진다"는 것을 저자가 스스로 보여주고도 그 함의를 회피하는 상태입니다.
</details>

---

## 1. 실제로 개선된 점 (공정하게)

| 1차 지적 | 2차 대응 | 평가 |
|---|---|---|
| float32 프로파일의 비대표성 | Y700에서 INT8 MatMulInteger 실측 | **상당한 진전** |
| 온디바이스 근거 부재 | 실제 Android(TB320FC) CPU/NNAPI 측정 | **진전** |
| 제목 overclaim("가속기 설계") | "가속기 구조 제안"으로 축소 | 적절 |
| offload 역설 미직면 | roofline에 USB3 stream 수치 추가 | 데이터는 넣었으나 해석 회피(아래 참조) |
| 면책 문구 남발 | 다소 정돈, 증거계층 표(표 1)로 집약 | 개선 |

표 1의 evidence-layer 분리와 claim boundary 표기는 여전히 이 논문의 가장 방어 가능한 강점입니다.

---

## 2. 해결되지 않은 치명적 결함

### 2.1 여전히 "세 개의 연결되지 않는 섬"이다 — 그리고 새 섬은 병목을 증명하지 못한다

2차는 증거를 셋으로 늘렸을 뿐, 서로 연결하지 못했습니다.

1. **81.1% decode MatMul share** — 표 1이 명시하듯 *"기존 profiling artifact, Ryzen host, Y700 측정 아님"*. 즉 1차의 그 CPU 프로파일 그대로입니다.
2. **Y700 micrograph latency** — INT8이지만 **고립된 단일 연산(isolated micrograph)** 측정입니다.
3. **DE10-Lite 16×4** — 여전히 toy.

여기서 심사에서 가장 아프게 찌를 지점:

> **단일 projection micrograph가 3.4 ms 걸린다는 사실은, projection이 decode 병목이라는 것을 증명하지 않습니다.**

병목은 *비중(share)* 의 문제인데, 고립 micrograph의 절대 latency는 share가 아닙니다. Y700에서 projection이 decode를 지배한다고 주장하려면 **full decode step latency를 재고, 그 안에서 projection이 차지하는 비율**을 보여야 합니다. 현재는 "projection 연산 하나가 몇 ms"만 있고, 그것이 전체 forward의 몇 %인지에 대한 온디바이스 증거는 없습니다. 결국 "projection이 병목"이라는 결론은 **여전히 옛 Ryzen float32 프로파일에만 의존**하며, Y700 데이터는 그 결론을 *보강한 것처럼 배치*되었을 뿐 실제로는 다른 질문에 답하고 있습니다.

### 2.2 Roofline이 논문의 결론을 반증하는데, 저자가 이를 직면하지 않는다

표 7의 숫자를 정면으로 해석하면:

$$
t_{\text{stream}}^{\text{lm\_head}} \approx 947\ \text{ms} \quad\gg\quad t_{\text{NNAPI}}^{\text{lm\_head tile}} \approx 2.989\ \text{ms}
$$

- USB3 320 MB/s 가정에서 lm_head weight 302 MB를 매 token마다 옮기면 offload 자체가 파멸적입니다.
- 저자의 처방(DDR2/LPDDR2 다채널)은 이 gap을 닫는다는 **정량적 논증이 전혀 없습니다.** Snapdragon 8+ Gen 1은 이미 LPDDR5(~51 GB/s급)를 씁니다. **밴드폭이 병목인 문제에서, 폰이 쓰는 LPDDR5보다 세대가 낮은 DDR2/LPDDR2로 이기겠다**는 제안은 aggregate bandwidth 수치 없이는 심사에서 즉시 기각됩니다. "채널을 늘리면 된다"는 것은 pin/SI/board 비용과 함께 정량화되어야 하며, 현재는 희망적 서술입니다.

**이것이 2차의 가장 큰 문제입니다.** 데이터를 정직하게 넣었더니 결론이 반증되는데, 논문은 그 반증을 "custom board는 구현 안 함"이라는 면책으로 우회할 뿐, **"그렇다면 이 연구가 시사하는 정직한 결론은 무엇인가(예: 이 스케일/인터페이스에서 FPGA offload는 부적합하다)"** 를 쓰지 않습니다. 진정한 기여는 오히려 여기에 있습니다 — negative result로서 정직하게 프레이밍하면 논문의 가치가 살아납니다.

### 2.3 제안 섹션이 "미구현 5종 세트 선언문"으로 비대해졌다 (신규 약점)

5·7·8절의 "저자 후속 구조 제안"은 다음을 한꺼번에 제안합니다.

1. 1.58bit 계열 변환 + 가산기 accelerator
2. 병목 offload FPGA NPU
3. SRAM-like scratchpad FPGA
4. DDR2/LPDDR2 다채널 weight memory
5. compute-FPGA ↔ scratchpad-FPGA custom connector

**다섯 개의 미구현 서브시스템**은 연구 논문에서 기여가 아니라 speculation manifesto로 읽힙니다. 1차 때 "future architecture sketch"였던 것이 오히려 더 크고 더 검증되지 않은 형태로 팽창했습니다. 심사 관점에서는 "무엇을 했는가"보다 "무엇을 하고 싶은가"가 지면을 더 차지하는 역전 현상입니다.

### 2.4 INT8 검증이 1.58bit 제안을 검증하지 못한다 (논리 단절)

- 구현·실측한 하드웨어: **INT8 MatMulInteger** MatVec.
- 제안하는 방향: **1.58bit ternary + 가산기 기반** datapath.

이 둘은 **다른 datapath**입니다. INT8 곱셈-누산 core의 board correctness는 ternary 가산기 accelerator를 전혀 검증하지 않습니다. 그런데 6·8절은 16×4 primitive를 "후속 구조 제안의 검증 출발점"이라 부릅니다. **출발점이 아닙니다** — 제안의 핵심 아이디어(곱셈 제거)는 검증된 것과 무관합니다. 또한 이 제안은 사실상 BitNet b1.58[1] + MatMul-free[2]의 재진술인데, **그들 대비 본 연구의 새로움이 무엇인지**가 없습니다("FPGA와 DDR2에 얹는다" 외).

---

## 3. 방법론·통계 문제

<details>
<summary>세부 사항 (펼치기)</summary>

- **Y700 통계 빈약**: warmup 3, 측정 20회인데 p50만 보고. p95·분산·thermal throttling 여부가 없습니다. 단일 기기·단일 세션이라 재현성 진술도 부족.
- **QNN(NPU) 미측정**: Snapdragon에서 sLLM의 실제 배포 타깃은 Hexagon/QNN NPU입니다. CPU/NNAPI는 현실 배포 경로가 아닐 수 있습니다. "integration blocked"는 정직하나, **가장 중요한 비교가 빠진 채 온디바이스 근거를 주장**하는 셈이라 동기의 설득력이 제한됩니다.
- **0.00% qk_score / 17.71% Expand+Concat**: 1차에서 지적한 분류기 결함과 exploratory trace 문제가 그대로 남아 있습니다.
- **16×4 → 실제 차원 scaling 모델 부재**: toy의 Fmax가 이미 56.67 MHz입니다. lane 16개·큰 tile로 확장 시 Fmax·DSP·BRAM이 어떻게 열화되는지의 합성 기반 모델이 없어, 표 7의 "16 lanes, 50 MHz, 377 ms"는 실제 core가 아니라 봉투 뒷면 계산입니다.
- **표 4 vs 본문 수치 정합성**: 1차에서 지적한 "72.91~87.29%" 류 오기는 이번엔 표를 단순화하며 회피했으나, 근거 데이터(c-코드 출처)가 사라져 **추적성(traceability)이 오히려 약화**됐습니다. 재현성 강점이 줄었습니다.
</details>

---

## 4. 원고 위생(Manuscript Hygiene) — 반드시 제거

- **5절 첫 줄 "저자 검토 필요:"** — 내부 편집 코멘트가 본문에 노출됨. 제출본에서는 치명적 감점.
- **그림 경로 `../../paper_assets/figures/...`** — 상대 경로가 그대로 노출. 렌더링 실패 상태.
- 참고문헌 [5][6][7](GPTQ/SmoothQuant/AWQ)이 본문에서 **한 번도 인용되지 않음**. 양자화 논의를 뺐다면 참고문헌도 정리해야 함.
- 감사의 말·저자 상세정보 등 1차에 있던 요소 일부가 사라짐(의도라면 무방하나 일관성 확인 필요).

---

## 5. 수정 로드맵 (우선순위 순)

1. **[필수] 2.2의 반증을 직면하라.** 지금 데이터는 "이 스케일·인터페이스(USB3/JTAG, DDR2)에서 FPGA offload는 폰 NNAPI보다 느리다"를 보여줍니다. 이를 숨기지 말고 **정직한 결론(부분적 negative result + 어떤 조건이 갖춰져야 offload가 유의미해지는가에 대한 손익분기 분석)** 으로 프레이밍하면 논문의 가치가 오히려 상승합니다. 예: "weight-resident, 온칩 대역폭 $B$가 몇 GB/s 이상일 때 손익분기"를 부등식으로 제시.
2. **[필수] Y700에서 decode share를 실제로 측정하라.** 고립 micrograph latency가 아니라, full(또는 축소) forward에서 projection이 차지하는 비율을 재야 "projection이 병목"이라는 온디바이스 근거가 성립합니다. 안 되면, 결론을 "옛 host 프로파일 기반 가설 + 온디바이스 절대 latency 확인"으로 정확히 한정.
3. **[필수] 제안 섹션 대폭 축소.** 5종 세트를 나열하지 말고, **분석에서 직접 도출되는 1개 요구사항(memory-centric weight residency)** 으로 좁히고 나머지는 "future work" 한 문단으로. DDR2/LPDDR2를 유지하려면 aggregate bandwidth 목표치를 폰 LPDDR5와 정량 비교.
4. **[필수] 1.58bit 제안과 INT8 검증의 논리 분리 명시.** "검증 출발점"이라는 표현을 버리고, "INT8 core는 곱셈 경로 타당성만 확인, ternary 가산기 경로는 별도 검증 필요"로 명확히.
5. **[권장] QNN/NPU 경로를 확보하거나, 못하면 "온디바이스 대표성의 상한"을 한계 절에 명시.**
6. **[권장] 내부 코멘트·그림 경로·미인용 참고문헌 등 원고 위생 정리, 출처 코드(c-코드) 복원으로 추적성 회복.**

---

## 결론적 코멘트

1차 대비 **정직성·온디바이스 근거·제목 정합성**은 확실히 좋아졌고, 저자의 성실함은 다시 한 번 인정합니다. 그러나 심사 기준에서 핵심 명제는 여전히 다음 한 문장으로 요약됩니다.

> **이 연구는 "projection이 무겁다"는 (부분적으로만 온디바이스로 확인된) 관찰과, 그것을 옮길 수 없다는 (자기 roofline이 보여주는) 결론을 동시에 담고 있으면서, 후자를 정면으로 인정하는 대신 미구현 5종 하드웨어 제안으로 회피한다.**

역설적으로, **가장 정직한 결론이 가장 좋은 논문을 만듭니다.** 현재 데이터는 "DE10-Lite/USB3/DDR2 급 구성에서는 decode projection offload가 폰보다 불리하며, 유의미해지려면 온칩 weight residency와 특정 대역폭 임계값이 필요하다"는 **정량적 negative/boundary result**를 지지합니다. 이 방향으로 재구성하면, toy primitive와 speculative 제안이라는 두 약점이 오히려 "손익분기 분석의 근거"로 전환됩니다.

어느 항목(예: 손익분기 부등식 설계, 또는 Y700 decode-share 측정 설계)부터 구체적으로 함께 파고들지 알려주시면 실험/서술 설계를 이어서 돕겠습니다.

**Assistant - --**

해당 2차 수정안은 1차 평가에서 지적된 치명적인 오타(Material 등)를 수정하고, 온디바이스(Android Y700) 환경에서의 실측 데이터를 추가하여 병목 분석의 신뢰성을 크게 높인 점이 돋보입니다. 그러나 박사 학위 논문 수준의 평가 기준을 적용할 때, 분석 결과와 하드웨어 제안 사이의 논리적 단절과 잔존하는 방어적 서술 방식은 여전히 논문의 가치를 떨어뜨리고 있습니다. 

조목조목 비평하고 수정 방향을 제시합니다.

---

## 1. 논리적 단절: INT8 분석에서 1.58bit/가산기 구조 제안으로의 비약

이번 수정안에서 가장 치명적인 문제는 **분석 대상과 제안 구조 간의 논리적 연결성이 붕괴되었다**는 점입니다.

- **문제점:** 4장까지는 ONNX Runtime에서 INT8 `MatMulInteger` 연산의 병목(MLP projection, `lm_head`)을 분석합니다. 그러나 5장과 7장에 이르러 갑자기 "1.58bit 계열 변환 기반 가산기 accelerator", "SRAM-like scratchpad FPGA", "DDR2/LPDDR2 다채널 memory"라는 전혀 새로운 개념이 등장합니다. 
- **가치 하락 지점:** 왜 INT8 곱셈기 기반의 병목을 분석했는데, 갑자기 1.58bit 가산기 기반 구조를 제안하는지 논리적 징검다리가 없습니다. 박사 논문에서는 관측된 문제(INT8 MatMul의 메모리/연산 병목)를 해결하기 위해 특정 아키텍처(저정밀 가산기 기반)를 선택한 당위성을 수학적 또는 실험적 근거를 통해 증명해야 합니다. 단순히 "후속 연구 방향"이라는 문장으로 이를 덮을 수 없습니다.
- **수정 방향:** 5장에서 INT8 MatMul의 한계(예: 곱셈기의 하드웨어 면적/전력 비용, 대역폭 병목)를 지적하고, 이를 극복하기 위해 BitNet b1.58 등에서 제시된 가산기 기반 연산이 하드웨어 관점에서 유리함을 설명하는 논리적 전환점을 만드십시오. 아니면, 1.58bit 제안을 과감히 삭제하고 현재 분석한 INT8 projection 병목을 해결하기 위한 INT8 tiled MatVec 아키텍처 제안으로 일관성을 유지하십시오.

## 2. 잔존하는 방어적 서술 (면책 조항의 잔재)

1차 평가에서 지적한 "과도한 면책 조항"이 일부 개선되었으나, 여전히 본문 곳곳에 방어적 태도가 남아 있습니다.

- **문장의 함의:** 
  - *6장:* "이 1.3 us 값은 빠른 AI 가속 성능이 아니다. 64 MAC smoke-test core가 보드에서 올바르게 동작하고... 기능 검증 anchor이다."
  - *5장:* "본 논문에서는 이러한 custom board, SRAM-like FPGA, 1.58bit 변환기, Y700-FPGA offload path를 구현했다고 주장하지 않는다."
- **문제점:** 연구자가 자신의 결과를 '기능 검증용'이라며 스스로 가치를 깎아내리는 서술입니다. $16 \times 4$ 규모의 하드웨어는 분명 작지만, 이를 "성능이 아님"이라고 부정할 것이 아니라 "제안 아키텍처의 가장 기본이 되는 연산 유닛(PE)의 물리적 구현 가능성과 타이밍 클로저(timing closure)를 확인한 단계"라고 긍정적으로 재해석해야 합니다.
- **수정 방향:** "~~가 아니다"라는 부정적 서술을 전부 삭제하고, "본 연구는 ~을 증명하기 위한 초일차 프로토타입 단계에 해당하며" 또는 "~의 하드웨어 구현 가능성을 확인했다"는 객관적이고 발전적인 서술로 변경하십시오.

## 3. 데이터 해석의 중의성 및 표 현화 문제

- **표 2의 해석 중의성:** 표 2에서 `smoke 16x4` 연산의 경우 CPU EP(0.051ms)보다 NNAPI EP(0.159ms)가 느립니다. 반면 실제 projection 크기에서는 NNAPI가 더 빠릅니다. 이는 온디바이스 NPU 디스패치 오버헤드의 존재를 보여주는 매우 훌륭한 데이터입니다. 그러나 본문(그림 2 설명)에서는 "provider dispatch overhead가 지배적이므로 구조 비교에 쓰지 않는다"고만 서술합니다.
- **수정 방향:** 이 데이터를 적극적으로 활용하십시오. "온디바이스 환경에서는 NPU 디스패치 오버헤드가 존재하므로, 작은 연산(16x4)을 NPU로 오프로드하는 것은 오히려 성능 저하를 초래한다. 따라서 FPGA 가속기 설계 시에도 연산의 세분화(Granularity)를 projection 단위로 묶어 오프로드해야 함을 시사한다"라고 논리적 근거로 승화시켜야 합니다.

## 4. 하드웨어 요구사항 도출의 구체성 부족

표 5와 표 7에서 도출한 하드웨어 요구사항이 여전히 추상적입니다.
- **문제점:** `lm_head`의 경우 1152->262144 projection이 약 302MB의 weight movement를 요구한다는 점(7장)은 매우 훌륭한 지적입니다. 하지만 이를 해결하기 위해 "DDR2/LPDDR2 다채널 memory"를 제안하는데, 현재 DE10-Lite(단일 채널 SDRAM) 환경에서 이것이 어떻게 가능한지, 혹은 이는 완전히 별도의 보드 설계(Future board)를 가정한 것인지 명확하지 않습니다.
- **수정 방향:** 표 7의 roofline model은 매우 좋은 접근입니다. 여기에 제안하는 아키텍처가 compute-bound인지 memory-bound인지 명확히 진단하고, 1.58bit 가산기 기반 구조가 이 memory-bound 문제를 어떻게 해결하는지(예: 가중치 비트폭 감소로 인한 대역폭 요구량 1/8 절감 효과)를 수치적으로 연결해야 합니다.

---

## 5. 요약 및 최종 수정 가이드라인

1. **논리적 일관성 확보:** 4장(INT8 분석)과 5장(1.58bit 제안) 사이의 논리적 점프를 복구하십시오. 1.58bit를 제안하려면 INT8 MatMul의 메모리 대역폭 병목을 수치화하고, 1.58bit가 이를 어떻게 해결하는지 설명하는 단락을 추가해야 합니다.
2. **표현의 긍정화:** "이것은 성능 주장이 아님", "구현했다고 주장하지 않음" 등의 자기 부정적 문구를 모두 제거하고, 현재 결과가 가지는 의미(예: PE 수준 검증, 타이밍 달성)를 객관적으로 서술하십시오.
3. **데이터 활용 극대화:** Y700 측정 데이터(표 2)를 단순 나열에 그치지 않고, NPU 디스패치 오버헤드 분석 등 온디바이스 하드웨어 설계 인사이트를 도출하는 데 적극 활용하십시오.

이번 2차 수정안은 방향성이 매우 좋습니다. Y700 실측 데이터를 추가하고 증거 계층을 명확히 구분한 점은 학술 논문으로서의 체계를 크게 높였습니다. 논리적 연결성만 보완한다면 우수한 연구 논문으로 완성될 수 있을 것입니다.

**Assistant - --**

1차 심사 지적사항을 반영하여 연구의 범위(Scope)를 조정하고, 파편화되었던 증거들을 계층별로 정리한 점은 긍정적입니다. 특히 Android(Lenovo Y700) 환경에서의 Micrograph 단위 실측 결과를 추가하여 온디바이스 맥락을 보강한 것은 논문의 신뢰도를 한층 높여줍니다.

그러나 2차 수정안 역시 **"학술 논문(Academic Paper)"이라기보다는 "엔지니어링 개발 일지(Lab Log)"에 가까운 서술**이 짙게 남아있으며, 추가된 제안(Proposal) 파트에서 심각한 논리적 비약이 발생했습니다. 박사 학위 논문 심사(Defense) 기준에서 여전히 통과하기 어려운 치명적인 결함과 수정 방향을 아래에 조목조목 짚어드립니다.

---

<details>
<summary><b>1. 치명적 실수: 편집자 주석(Draft Note)의 잔존</b></summary>

*   **비판:** 5절 도입부에 `**저자 검토 필요:** 본 절은 사용자가 제시한 후속 구조 아이디어를 논문 문장으로 정리한 초안이다...`라는 문장이 그대로 남아있습니다. 이는 심사위원에게 논문의 완성도에 대한 치명적인 불신을 초래합니다. 제출 전 원고 교정(Proofreading)이 전혀 이루어지지 않았다는 증거입니다.
*   **조치:** 즉시 삭제하십시오.
</details>

<details>
<summary><b>2. 논리적 비약 (Logical Leaps): INT8 검증에서 1.58-bit 제안으로의 급발진</b></summary>

*   **현상:** 본 논문의 1~4절, 6절은 철저하게 `INT8` (`MatMulInteger`) 환경에서의 프로파일링과 하드웨어 구현(DE10-Lite `fixed 16x4 INT8 MatVec primitive`)을 다루고 있습니다. 그러나 5절과 7절의 후속 구조 제안에서는 갑자기 **"1.58bit 계열 변환 기반 가산기 accelerator"**를 핵심 구조로 제안합니다.
*   **비판:** 학술 논문의 결론과 제안은 본론의 실험 데이터로부터 논리적으로 유도되어야 합니다. INT8 환경에서 병목을 분석해 놓고, 대안으로는 1.58-bit 하드웨어를 제안하는 것은 앞뒤가 맞지 않습니다. 1.58-bit(Ternary) 네트워크로 변환했을 때 모델의 정확도(Accuracy) 손실이나 메모리 대역폭 이득에 대한 **정량적 분석이 전무**한 상태에서 구조만 제안하는 것은 공상에 불과합니다.
*   **조치:** 
    *   [옵션 1] INT8 중심의 Memory-centric Architecture (SRAM scratchpad 등) 제안으로만 한정하고 1.58-bit 관련 서술을 완전히 제거하십시오.
    *   [옵션 2] 정 1.58-bit 제안을 유지하고 싶다면, "INT8 환경에서는 여전히 $M \times N$ 곱셈기의 Area/Power 오버헤드가 크므로, 이를 대체하기 위한 극단적 양자화(1.58-bit 등) 기반의 가산기 전용 하드웨어 탐색이 요구된다"는 형태로 짧은 Future Work 수준으로만 축소하십시오.
</details>

<details>
<summary><b>3. 엔지니어링 일지(Lab Log)식 서술과 여전한 방어적 태도</b></summary>

*   **현상:** 초록 및 본문에서 `integration blocked`, `smoke-test core`, `anchor`, `빠른 AI 가속 성능이나 ONNX Runtime 대비 우위로 해석하지 않는다` 등의 표현이 반복됩니다.
*   **비판:** 
    *   `QNN EP는 사용한 AAR build에서 지원되지 않아 integration blocked로 기록했다.` $\rightarrow$ 이것은 개발팀의 Jira 티켓이나 회의록에 적을 내용입니다. 학술 논문에서는 평가하지 못한 (혹은 불필요한) 환경은 아예 언급을 생략하거나, "본 실험에서는 CPU와 NNAPI EP의 성능 비교에 집중하였다"라고만 명시하면 됩니다.
    *   자신의 연구 결과를 "smoke-test(작동 확인용 테스트)"라고 칭하거나 "성능 우위로 해석하지 않는다"고 반복해서 방어선을 치는 것은 학문적 기여도를 스스로 폄하하는 행위입니다.
*   **조치:** 
    *   `integration blocked` 관련 서술 전면 삭제.
    *   방어적 문구를 "본 연구의 FPGA 구현은 제안하는 INT8 MatVec 구조의 하드웨어 실현 가능성(Feasibility) 및 타이밍 분석을 위한 Proof-of-Concept(PoC)으로 활용되었다." 수준으로 세련되게 순화하십시오.
</details>

<details>
<summary><b>4. 수학적/비용 모델링(Cost Modeling)의 부재</b></summary>

*   **현상:** 7절 '표 7. Projection tile roofline/interface model 요약'에서 compute 9.95 ms, stream 24.97 ms 등을 제시하고 있으나, 이 수치들이 어떻게 도출되었는지 수식이 전혀 없습니다.
*   **비판:** 아키텍처 논문에서 Estimate(추정치)를 제시할 때는 반드시 이론적 수식이 동반되어야 합니다. 그렇지 않으면 숫자의 신뢰성을 검증할 수 없습니다. 
*   **조치:** 아래와 같은 지배 방정식(Governing Equation)을 본문에 추가하십시오.
    *   연산 시간(Compute Time) 모델: 
        $$ T_{compute} = \frac{M \times N}{P_{lanes} \times f_{CLK}} $$
    *   스트리밍 시간(Stream Time) 모델: 
        $$ T_{stream} = \frac{W_{size}}{B_{USB3}} $$
        (여기서 $P_{lanes}$는 병렬 MAC 수, $f_{CLK}$는 동작 주파수, $W_{size}$는 가중치 크기, $B_{USB3}$는 실효 대역폭)
    *   이 수식을 본문에 명시한 뒤 표 7의 결과가 도출되었음을 설명해야 Roofline 모델로서의 가치가 생깁니다.
</details>

<details>
<summary><b>5. 문단 및 용어 교정 지시사항 (Action Items)</b></summary>

1.  **초록 및 서론:** "본 연구는 FPGA가 전체 모델을 더 빠르게 실행했다는 성능 주장이 아니라..." $\rightarrow$ "본 연구는 온디바이스 환경에서 sLLM의 Decode 병목을 분석하고, 이를 해소하기 위한 하드웨어 마이크로아키텍처(Microarchitecture) 설계와 검증에 집중한다."로 수정.
2.  **표 2 및 표 3 통합 고려:** 단순히 파일 이름을 나열한 표 3(`gemma_..._float.onnx` 등)은 지면 낭비입니다. 표 2와 병합하거나, 본문에서 문장으로 "각 연산별로 Float 및 INT8 양자화 모델을 독립적인 ONNX 마이크로그래프로 추출하여 평가하였다"라고 갈음하십시오.
3.  **JTAG 관련 서술 최소화:** 6절에서 JTAG overhead 수치(`7756.114875 ms...`)를 장황하게 적는 것은 여전히 불필요합니다. "호스트 통신 오버헤드를 제외한 FPGA 내부의 순수 연산 Latency는 $1.3 \mu s$ 사이클 임을 확인하였다."로 1문장으로 압축하십시오.
</details>

---

### 총평 (Summary)

2차 수정안은 1차 초안의 치명적인 문제(Scope 불일치)를 일정 부분 해결하였고 증거를 계층화(Evidence Layering)한 논리적 구성은 훌륭합니다. 그러나 **① 남아있는 개발 일지 톤의 비학술적 단어들(`integration blocked` 등)**과 **② 실험하지 않은 1.58-bit 구조를 결론부에서 핵심 대안으로 내세우는 논리적 단절**을 반드시 해결해야 합니다. 

제시해 드린 수식(수학적 모델링)을 추가하여 공학적 추정(Estimate)의 근거를 단단히 하고, 방어적이고 위축된 문장들을 학술적 단어(PoC, Feasibility, Proof of concept)로 치환한다면 훌륭한 학문적 가치를 지닌 논문이 될 것입니다.

**Assistant - --**

### Reasoning

The user has provided a revised 2nd draft. I need to evaluate it critically under the same standards: as if reviewing a PhD thesis or top-conference submission.

**2차 수정안 종합 평가** (PhD-level / Top-conference 기준)

전체적으로 1차 대비 **명확히 개선**되었다. 특히 

- Abstract와 서론에서 “full acceleration 주장 아님”을 훨씬 솔직하고 체계적으로 명시한 점
- Lenovo Y700 Android micrograph benchmark를 추가해 온디바이스 근거를 강화한 점
- Table 1로 evidence 계층을 시각화한 점
- “저자 후속 구조 제안”을 명확히 구분한 점

은 긍정적이다. 그러나 **근본적인 문제**는 여전히 남아 있다.

### 종합 판정

| 항목 | 1차 | 2차 | 평가 |
|------|-----|-----|------|
| Claim 과장 수준 | 심각 | 중간 | 많이 줄었으나 여전히 과함 |
| Evidence 명확성 | 약함 | 좋음 | Table 1이 큰 기여 |
| FPGA 결과의 학술적 가치 | 매우 낮음 | 매우 낮음 | 변화 없음 |
| 논문으로서의 초점 | 분산 | 여전히 분산 | 4가지 다른 것을 동시에 하려 함 |
| 게재 가능성 (저널/학회) | 거의 없음 | 낮음 | 아직 부족 |

**결론**: 1차보다는 훨씬 나아졌지만, **여전히 박사 졸업 논문이나 정상 학회 논문 수준에는 크게 미치지 못한다**. 현재 형태로는 **학부 연구보고서**나 **워크숍 포스터** 수준에 더 가깝다.

### 1. 가장 큰 문제점 (순위별)

**1) FPGA 결과의 실질적 기여가 극도로 약함 (가장 치명적)**
- DE10-Lite 16×4 INT8 MatVec primitive (64 MAC)는 **고등학생 프로젝트** 이상의 의미를 갖기 어렵다.
- Android Y700 micrograph 결과(0.5~3.5 ms)를 추가하면서 FPGA 결과(1.3 µs)가 오히려 **더 고립**되어 보인다. 
- 1.3 µs가 “functional verification anchor”라는 설명은 옳지만, 그렇다면 이 결과를 논문의 핵심으로 둘 이유가 거의 없다.

**2) 논문이 4가지를 동시에 하려는 구조적 문제**
현재 논문은 다음 네 가지를 한 papers에 담으려 한다:
1. ONNX Runtime profiling 분석
2. Android (Y700) micrograph benchmark
3. DE10-Lite primitive 검증
4. 저자 후속 구조 제안 (1.58bit + scratchpad + DDR2 multi-channel)

이 중 3과 4는 **학술적 무게**가 너무 가볍다. 특히 4번(후속 구조 제안)은 “아이디어” 수준이라 논문의 본질을 흐린다.

**3) Title과 Abstract의 framing이 여전히 과장**
- Title: “… FPGA 기반 INT8 MatVec 가속기 구조 제안”
- Abstract: “memory-centric low-bit MatVec design that combines…” 

→ 이는 **구현된 결과**가 아니라 **아이디어**를 제목에 넣은 것이다. reviewer가 가장 먼저 공격할 부분이다.

### 2. 섹션별 구체적 비판

**Abstract**
- 상당히 개선되었으나, 마지막 문장(“The follow-up architecture direction is framed as…”)이 여전히 **미래 아이디어를 현재형으로 서술**하고 있다.
- **수정 제안**: Abstract 마지막 부분을 “The authors outline a potential follow-up direction…” 식으로 완전히 proposal로 명확히 해야 한다.

**1. 서론**
- 기여 3가지를 제시한 것은 좋았으나, **셋째 기여**(FPGA primitive)가 너무 약해서 전체 기여의 무게가 떨어진다.
- “저자 후속 구조 제안”을 기여로 넣은 것은 과도하다. 이는 contribution이 아니라 future work이다.

**3. 실험 방법**
- Table 1은 잘 만들었다. 다만 “claim boundary” 열이 너무 길고 반복적이다. 더 간결하게 정리할 필요가 있다.

**5. 병목 분석 기반 FPGA 구조 요구사항과 저자 후속 구조 제안**
- 이 섹션이 논문에서 가장 약한 부분이다.
- “저자 후속 구조 제안”이라는 이름으로 1.58bit 변환, SRAM-like scratchpad, DDR2/LPDDR2 다채널 memory 등을 나열했지만, **모두 미구현**이다.
- 이 섹션을 과감하게 줄이거나, **부록**으로 옮기는 것을 강력히 권장한다. 현재는 논문의 초점을 크게 흐린다.

**6. DE10-Lite INT8 MatVec primitive 검증 결과**
- 가장 솔직하게 쓴 부분이다. 
- 다만 이 결과를 **독립된 섹션(Section 6)**으로 둘 가치가 있는지 의문이다. 16×4 primitive 결과는 1~2페이지 분량으로 충분히 압축 가능하다.

**7. Memory/Interface 요구사항과 후속 구조 방향**
- Roofline 분석은 의미가 있으나, USB3 320 MB/s라는 가정이 실제 FPGA 보드 환경과 잘 맞지 않는다.
- “custom board” 제안을 너무 구체적으로 서술한 점이 문제다 (pin count, signal integrity 등).

### 3. 추천하는 대대적 수정 방향 (우선순위 순)

**강력 추천 옵션 A (가장 현실적)**
- **FPGA primitive 결과와 저자 후속 구조 제안을 대폭 축소**하거나 삭제
- 논문을 **“ONNX Runtime + Android micrograph 기반 decode bottleneck analysis”**에 집중
- FPGA 부분은 “preliminary primitive validation” 정도로만 간단히 언급

**옵션 B (현재 방향 유지 시)**
- Title을 다음과 같이 변경:
  > “Decode Bottleneck Analysis of On-device ONNX Runtime sLLM Inference with Preliminary INT8 MatVec Primitive Validation”

- Section 5, 7을 각각 1/3~1/2 분량으로 줄이고, “future work” 성격을 명확히 함
- Abstract에서 “저자 후속 구조 제안” 관련 문장을 최소화

**옵션 C (가장 과감한 수정)**
- FPGA 관련 내용(Section 5, 6, 7 상당 부분)을 모두 빼고, **온디바이스 Android micrograph benchmark + ONNX profiling**만으로 논문을 재구성. 이 경우 논문의 무게감이 오히려 올라갈 가능성이 높음.

### 최종 의견

2차 수정으로 **방어적인 글쓰기**와 **evidence 구분**은 많이 개선되었지만, **논문의 본질적인 스코프 문제**는 해결되지 않았다. 

고등학생이 이 정도의 profiling과 micro-benchmark를 수행한 것은 충분히 훌륭한 작업이지만, 현재처럼 “FPGA 가속기 구조 제안”까지 끌고 가려다 보니 논문이 산만하고 약해 보인다.

**진지한 조언**: 
FPGA primitive와 미래 구조 제안을 과감하게 포기하고, **Y700 Android micrograph + ONNX Runtime profiling**에 집중하는 방향으로 가는 것이 현재 시점에서 논문의 완성도를 가장 높이는 길이다.

필요하면 위 옵션 A/B/C 중 하나를 선택해서 **구체적인 섹션 재구성안**까지 작성해 드릴 수 있습니다.

**Assistant - --**

최윤혁 연구자님, 2차 수정안을 잘 받아보았습니다. 

먼저 심사위원으로서 **경의를 표하고 싶습니다.** 1차에서 지적했던 치명적 오류(AI 생성 캡션, 오타, 과도한 방어기제)를 완벽하게 도려냈을 뿐만 아니라, **실제 온디바이스 하드웨어(Lenovo Y700, Snapdragon 8+ Gen 1)를 활용한 Micrograph 벤치마크를 추가**하면서 논문의 실험적 가치(Empirical Value)와 '온디바이스'라는 제목의 정당성이 비약적으로 상승했습니다. 

현재 초안은 학술지 심사에서 **'Minor Revision(수정 후 게재)'** 수준에 도달했습니다. 증거 계층(Evidence Layer)을 표 1로 명시한 것은 매우 탁월한 방법론적 선택이었습니다.

하지만 **박사 학위논문 및 우수 학술지 게재를 위한 최종 관문**으로서, 논문의 **응집력(Cohesion)을 해치는 몇 가지 구조적 문제**와 **기술적 깊이(Technical Depth)가 여전히 회피된 지점**을 짚어드리겠습니다.

---

## 1. 논문 가치가 하락하는 치명적 지점 (Critical Flaws)

### 1.1. 논문의 응집력(Cohesion) 붕괴: 느닷없는 '1.58bit'와 'Multi-FPGA Custom Board'
5절과 7절, 8절에서 갑자기 **1.58bit(BitNet) 변환, SRAM-like scratchpad FPGA, DDR2/LPDDR2 다채널, Custom connector** 이야기가 등장합니다. 
* **비평**: 1~4절까지 Gemma 3 1B(INT8/FP32)와 상용 보드(DE10-Lite, Y700)를 분석해놓고, 결론에서 갑자기 "사실 나는 1.58bit 커스텀 보드를 만들고 싶다"고 선언하는 것은 **학술 논문의 논리적 일관성을 심각하게 훼손**합니다. 심사위원은 *"현재 INT8 ONNX 병목도 다 해결하지 못한 상태에서, 왜 양자화 알고리즘(1.58bit)과 커스텀 PCB 설계 이야기가 나오는가?"* 라고 반문할 것입니다. 이는 저자의 '개인적 미래 포트폴리오'이지, '본 연구 데이터가 도출한 결론'이 아닙니다.
* **수정**: 1.58bit 및 Multi-FPGA Custom Board 제안은 본문의 핵심에서 **완전히 삭제하거나, 결론의 마지막 한 줄(Future Work)로만 축소**하십시오. 본 논문의 결론은 **"Memory-centric INT8 Projection Offload Architecture의 필요성"** 으로 귀결되어야 합니다.

### 1.2. 메타 언어(Meta-language)의 본문 포함
5절 서두에 다음과 같은 문장이 있습니다.
> **"저자 검토 필요:** 본 절은 사용자가 제시한 후속 구조 아이디어를 논문 문장으로 정리한 초안이다..."

* **비평**: 이는 AI와의 대화나 초안 메모에서 쓰이는 **메타 텍스트**입니다. 학술지 본문에 이런 문장이 그대로 실리면 즉각적인 Reject 사유가 됩니다.
* **수정**: 해당 문장을 **즉시 삭제**하고, 객관적인 학술적 어조로 서술을 시작하십시오.

### 1.3. Roofline 모델의 인터페이스 가정 불일치 (표 7)
표 7에서 Roofline 분석을 위해 **USB3 320 MB/s**를 가정했습니다.
* **비평**: 본 논문이 실증한 하드웨어는 DE10-Lite(JTAG/USB-Blaster)와 Y700(Android)입니다. DE10-Lite에는 USB3 대역폭을 활용할 수 있는 경로가 없으며, Y700은 USB-C를 지원하지만 ONNX Runtime EP와 FPGA를 USB3로 직접 연결한 실험을 하지 않았습니다. 근거 없는 인터페이스 가정은 Roofline 모델의 신뢰도를 떨어뜨립니다.
* **수정**: USB3 가정을 유지하려면, 이것이 **"추후 외부 Accelerator Board(예: Zynq UltraScale+ 또는 PCIe/USB3 연결 FPGA)를 호스트에 물렸을 때의 이론적 상한선"** 을 가정한 것임을 표 7의 캡션이나 각주에 명시해야 합니다.

---

## 2. 문장의 함의 및 중의성 개선 (Technical Depth)

### 2.1. `attention_qk_score` 0%의 진정한 원인 회피
1차에서 지적했던 ORT의 **Operator Fusion**에 대한 분석이 여전히 빠져있습니다. 4절에서 여전히 *"현재 event classifier에서 확정 가능한 MatMul event가 없었다"* 고만 서술하고 있습니다.
* **비평**: 이는 프로파일러 탓으로 돌리는 방어적 서술입니다. ONNX Runtime은 기본적으로 `ORT_ENABLE_ALL` 등의 Graph Optimization을 통해 `MatMul`과 `Add`를 `FusedConv`나 `Attention` 같은 단일 Custom Operator로 합쳐버립니다. 즉, QK Score 연산이 존재하지 않는 것이 아니라 **Fusion되어 프로파일러 노드 이름이 바뀌었을 뿐**입니다.
* **수정**: ORT의 Graph Optimization(Fusion) 메커니즘을 언급하며, QK 연산이 `Attention` 또는 `FusedMatMul` 노드 내부로 흡수되었을 것임을 기술적으로 추론하는 문장을 추가해야 학문적 깊이가 생깁니다.

### 2.2. Micrograph 벤치마크의 한계에 대한 당위성 부족
Y700에서 전체 모델이 아닌 'Micrograph'만 실행한 이유는 솔직하게 밝히고 있지만, **왜 하필 Micrograph여야만 했는지**에 대한 시스템적 당위성이 약합니다.
* **수정**: "단일 Layer의 Projection 연산을 추출한 Micrograph를 사용한 이유는, Android 환경에서의 전체 모델 Export 한계 및 KV-cache Dynamic Shape 오버헤드를 배제하고 **순수한 Dense Projection 연산의 EP(CPU vs NNAPI)별 Dispatch 및 Compute 비용만을 격리(Isolate)하여 분석하기 위함**"이라는 명확한 실험 설계 의도를 추가하십시오.

---

## 3. 세부 수정 로드맵 (Actionable Items)

<details>
<summary><b>[클릭] 주요 섹션별 구체적인 Before/After 수정안</b></summary>

### A. 5절 및 7절의 '1.58bit / Custom Board' 과감히 축소
* **Before**: (5절) "저자 후속 구조 제안은 일반 모델을 1.58bit 계열 모델로 변환한 뒤... DDR2 또는 LPDDR2 기반 low-power weight memory를 결합하는 custom board 방향을 검토한다."
* **After**: "본 연구의 병목 분석은 FPGA 가속기가 단순한 MAC 연산기(Array)가 아닌, **Weight Movement를 최소화하는 Memory-Centric Architecture**여야 함을 시사한다. 특히 `lm_head`와 같은 대규모 Projection은 온디바이스 환경의 제한된 Memory Bandwidth 내에서 Weight Streaming과 Tiling Buffer(SRAM) 최적화가 필수적이며, 이는 추후 저정밀(Low-bit) 양자화 및 전용 Memory Interface 연구로 확장될 수 있다." *(1.58bit, DDR2, Custom Connector 등의 구체적인 스펙은 삭제하고 방향성만 제시)*

### B. 4절: ORT Fusion에 대한 기술적 통찰 추가
* **추가할 문장**: "`attention_qk_score`가 0.00%로 관측된 현상은 해당 연산이 소실되었음을 의미하지 않는다. ONNX Runtime의 Graph Optimization 단계에서 `MatMul`, `Add`, `Softmax`가 결합된 `Attention` 또는 `FusedMatMul` 커스텀 노드로 Fusion되었을 가능성이 높다. 따라서 실제 QK 연산 비용은 해당 Fused Node 내부에 내재되어 있으며, 추후 ORT의 Node-level Profiling이 아닌 Kernel-level Profiling을 통한 추가 분석이 요구된다."

### C. 표 7: Roofline 모델의 가정(Assumption) 명시
* **Before**: (표 7) interface case: USB3 320 MB/s
* **After**: (표 7 하단 Note 추가) *"Note: USB3 320 MB/s는 DE10-Lite의 현재 인터페이스가 아닌, 추후 호스트-액셀러레이터 간 전용 인터페이스(예: USB-C Direct, PCIe 등)를 적용했을 때의 이론적 대역폭 상한선을 가정한 Projected Model임."*

### D. 메타 텍스트 삭제 및 학술적 어조 전환
* **Before**: "**저자 검토 필요:** 본 절은 사용자가 제시한 후속 구조 아이디어를..."
* **After**: (해당 문장 완전 삭제 후 바로 본론 진입) "Y700 micrograph와 기존 ONNX Runtime profiling은..."

</details>

---

## 💡 총평 및 심사위원의 최종 제언

최윤혁 연구자님, 2차 수정안은 **고등학생이 썼다는 사실을 의심케 할 만큼 훌륭한 '시스템적 사고(System-level Thinking)'** 를 갖추고 있습니다. 특히 Evidence Layer를 표로 정리하고, Overclaim을 스스로 경계하는 태도는 많은 대학원생들도 갖추지 못한 연구자의 미덕입니다.

다만, 논문이란 **'내가 앞으로 하고 싶은 꿈(1.58bit, Custom PCB)'을 적는 일기장**이 아니라, **'현재 수집한 데이터가 무엇을 증명하는가'** 를 차갑게 꿰뚫는 보고서여야 합니다. 

1. **1.58bit 및 커스텀 보드에 대한 미련을 버리십시오.** 그것들은 이 논문의 결론이 아니라, 이 논문을 바탕으로 연구자가 쓸 **'다음 논문(Next Paper)'의 주제**입니다.
2. 본 논문의 대미는 **"온디바이스 환경에서 LLM의 Decode 병목은 Attention이 아닌 Projection(Memory Movement)에 있으며, 이를 입증하기 위해 Y700과 FPGA Primitive로 교차 검증했다"** 는 fact에서 화려하게 마무리되어야 합니다.

이 세 가지 구조적 정리만 이루어진다면, 본 논문은 한국정보기술진흥원 학술지는 물론, 추후 국제 학회(IEEE/ACM 관련 워크숍 등)에 도전해도 손색이 없는 **매우 단단한 아키텍처 분석 논문**으로 완성될 것입니다. 최종 게재를 진심으로 응원합니다.