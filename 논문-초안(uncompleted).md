## ONNX Runtime 기반 온디바이스 소형 언어모델 추론의 병목 분석 및 FPGA 기반 Decode 가속기 구조 설계
**Bottleneck Analysis of ONNX Runtime-based On-device Small Language Model Inference and Design of an FPGA-based Decode Accelerator Architecture**
## 저자
[최윤혁](https://orcid.org/0009-0006-3537-0249)
한국디지털미디어고등학교
yunhyuk choi
korea digital media high school

## 초록
온디바이스 환경에서 소형 언어모델은 클라우드 의존성을 줄이고 개인정보 보호와 저지연 응답을 제공할 수 있다. 그러나 0.xB~1B급 sLLM이라도 ONNX Runtime 기반 추론에서는 model export, graph structure, runtime execution, memory pressure, prefill/decode 단계의 상호작용에 따라 병목이 달라질 수 있다. 본 연구는 ONNX export, graph inspection, runtime profiling, CPU/CUDA PyTorch host-side reference baseline을 통해 실제 병목 위치를 분석한다. KV-cache는 long-context decode memory pressure를 설명하는 대표적 구조적 요인으로 다루되, 유일한 병목으로 가정하지 않는다. FPGA 구현은 full KV-cache 관리나 Gemma 3 1B 전체 실행이 아니라, profiling으로 도출된 decode-stage primitive 중 INT8 QK dot-product의 feasibility 검증으로 한정하고, 이후 QK dot-product, scale, softmax/approximation, V weighted sum, buffer/stream interface를 포함하는 FPGA Decode 가속기 구조로 확장 가능성을 제시한다.
**키워드:** 
## Abstract
On-device small language models can reduce cloud dependency while improving privacy and response latency. However, in ONNX Runtime-based inference, bottlenecks may arise from model export, graph structure, runtime execution, memory pressure, prefill, decode, or interactions among these factors. This study uses ONNX export, graph inspection, runtime profiling, and CPU/CUDA PyTorch host-side reference baselines to locate practical bottlenecks. KV-cache is treated as a representative structural factor for long-context decode memory pressure, not as the only assumed bottleneck. The FPGA work is limited to INT8 QK dot-product primitive feasibility and frames a future FPGA Decode accelerator architecture that can include QK dot-product, scale, softmax or approximation, V weighted sum, and buffer/stream interfaces.
**keyword:** 

## 목차
1. 서론
   1.1 온디바이스 sLLM의 필요성
   1.2 ONNX Runtime 기반 추론의 장점과 한계
   1.3 기존 AI 하드웨어 가속 연구와의 차별점
   1.4 연구 목표와 기여

2. 본론
   2.1 ONNX 기반 sLLM 추론 구조
   2.2 Prefill과 Decode 단계의 차이
   2.3 ONNX export와 graph inspection
   2.4 ONNX Runtime profiling 방법
   2.5 KV-cache와 long-context memory pressure
   2.6 CPU/CUDA PyTorch host-side reference baseline
   2.7 FPGA 가속 대상 primitive 선정
   2.8 FPGA 기반 Decode 가속기 구조
   2.9 실험 결과 분석

3. 결론
   3.1 연구 결과 요약
   3.2 FPGA 이종 가속 구조의 가능성
   3.3 연구의 한계
   3.4 후속 연구 방향

## 서론
### 온디바이스 sLLM의 필요성
요즘은 AI의 최고점을 가늠하지 못할 정도로 전성기를 맞이하고 있다. 하지만 현재 대부분의 AI 기술은 클라우드 컴퓨팅에 의존하고 있는데, 이 원인은 단연코 온디바이스의 성능 부족일 것이다. 
