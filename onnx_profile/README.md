# ONNX Profile Utilities

This directory contains host-side scripts for:

- ONNX Runtime profiling scaffolding
- prefill/decode-separated latency sweeps across prompt lengths
- raw Hugging Face directory inspection
- ONNX export preflight and dry-run planning
- ONNX graph inspection
- theoretical KV-cache size analysis as one long-context memory-pressure factor
- deterministic test vector export for FPGA validation

## Scripts

- `inspect_hf_model_dir.py`: raw Hugging Face directory inspection and metadata extraction
- `profile_torch_gemma.py`: raw Hugging Face Gemma profiling with Transformers/PyTorch as a host-side reference baseline
- `export_gemma_to_onnx.py`: Gemma ONNX export preflight, dry-run, and export wrapper
- `inspect_onnx_model.py`: ONNX graph input/output inspection with cache-I/O detection
- `run_profile.py`: session setup plus prefill/decode profiling scaffolding
- `decode_context_sweep.py`: prompt-length sweep, decode latency table generation, theoretical KV-cache size versus process-RSS comparison, and FPGA primitive bridge summary
- `kv_cache_size.py`: CSV and PNG generation for theoretical KV-cache size
- `export_vectors.py`: deterministic INT8 Q/K vector export with expected scores

## Example Usage

```bash
python3 onnx_profile/inspect_hf_model_dir.py --model-dir /home/monad/develop/ai_accel/gemma3-1B --out-dir onnx_profile/results
python3 onnx_profile/profile_torch_gemma.py --model-dir /home/monad/develop/ai_accel/gemma3-1B --prompt "Explain KV cache in one sentence." --new-tokens 8 --device cpu --dtype bfloat16
python3 onnx_profile/export_gemma_to_onnx.py --model-dir /home/monad/develop/ai_accel/gemma3-1B --out-dir /home/monad/develop/ai_accel/gemma3-1B-onnx --dry-run
python3 onnx_profile/inspect_onnx_model.py --model /home/monad/develop/ai_accel/gemma3-1B-onnx/model.onnx --out-dir onnx_profile/results
python3 onnx_profile/run_profile.py --model /path/to/model.onnx --provider CPUExecutionProvider --prompt-len 128 --decode-tokens 16 --profile --out-dir onnx_profile/results/raw
python3 onnx_profile/decode_context_sweep.py --model /path/to/model.onnx --provider CPUExecutionProvider --prompt-lens 128 512 1024 2048 --decode-tokens 8 --layers 18 --kv-heads 1 --head-dim 256 --bytes-per-element 2 --out-dir onnx_profile/results
python3 onnx_profile/kv_cache_size.py --layers 18 --kv-heads 1 --head-dim 256 --bytes-per-element 2 --out-dir onnx_profile/results
python3 onnx_profile/export_vectors.py --dim 16 --num-keys 8 --seed 7 --out-dir fpga_test/vectors
```

Generated sweep outputs:

- `onnx_profile/results/tables/decode_latency_by_context.csv`
- `onnx_profile/results/tables/kv_memory_comparison.csv`
- `onnx_profile/results/decode_fpga_bridge_summary.md`
- copies of the two CSV tables in `paper_assets/tables/`
- `onnx_profile/README_export.md` for the raw-HF-to-ONNX preparation flow

Caution:

- Raw Hugging Face `safetensors` directories are not directly executable by ONNX Runtime.
- If the ONNX export does not expose reusable past-KV tensors, the scripts mark that explicitly and fall back to single-token runs without cache feedback.
- Measured RSS growth is only an approximation and should not be reported as pure KV-cache allocation without caveats.
- PyTorch results in this directory are host-side reference baselines, not ONNX Runtime results.
