# ONNX Profile Utilities

이 디렉터리는 ONNX Runtime profiling과 graph inspection을 재현하기 위한 host-side source를 담는다. `main`에는 논문에서 쓰는 요약 CSV/PNG만 남기고, raw profiler JSON과 긴 sweep raw output은 `examine` 브랜치에 보존한다.

주요 스크립트:

- `inspect_hf_model_dir.py`: Hugging Face model directory 구조 점검
- `export_gemma_to_onnx.py`: ONNX export preflight/dry-run wrapper
- `inspect_onnx_model.py`: ONNX graph input/output 및 cache I/O 검사
- `run_profile.py`: ONNX Runtime session profiling scaffold
- `decode_context_sweep.py`: prefill/decode context sweep와 paper-facing summary 생성
- `kv_cache_size.py`: theoretical KV-cache size summary 생성
- `export_vectors.py`: fixed INT8 primitive 검증용 deterministic vector 생성

예시:

```bash
python3 onnx_profile/inspect_onnx_model.py --model /path/to/model.onnx --out-dir onnx_profile/results
python3 onnx_profile/run_profile.py --model /path/to/model.onnx --provider CPUExecutionProvider --prompt-len 128 --decode-tokens 16 --profile --out-dir onnx_profile/results/raw
python3 onnx_profile/decode_context_sweep.py --model /path/to/model.onnx --provider CPUExecutionProvider --prompt-lens 128 512 1024 2048 --decode-tokens 8 --layers 18 --kv-heads 1 --head-dim 256 --bytes-per-element 2 --out-dir onnx_profile/results
```

해석 경계:

- PyTorch 결과는 host-side reference baseline이며 ONNX Runtime 결과를 대체하지 않는다.
- raw Hugging Face `safetensors` directory는 ONNX Runtime에서 직접 실행하는 graph가 아니다.
- RSS 변화는 KV-cache allocation의 직접 측정값으로 단정하지 않는다.
- 이 디렉터리의 profiling evidence는 FPGA full-model execution 또는 end-to-end speedup 주장이 아니다.
