# ai_accel_paper Test Package

This package contains the Windows CPU/ONNX Runtime baselines, optional FPGA UART
and JTAG validation runners, ONNX micrograph artifacts, claim-boundary notes, and
paper-facing tables prepared from the repository.

Run locally:

```powershell
python install.py --local . --run-cpu --run-ort
```

Run strict non-hardware smoke checks:

```powershell
python install.py --local . --run-cpu --run-ort --extract-quartus-summary --strict
```

Run the optional ONNX Runtime integer micrograph baseline:

```powershell
python install.py --local . --run-ort-integer
```

List serial ports:

```powershell
python install.py --local . --list-ports
```

Run optional FPGA UART validation:

```powershell
python install.py --local . --run-fpga --port COM5 --baud 115200
```

Run optional USB-Blaster JTAG register validation:

```powershell
python install.py --local . --run-jtag --cable "USB-Blaster [USB-0]"
```

Require a real passing JTAG hardware run:

```powershell
python install.py --local . --run-jtag --require-jtag-pass
```

Extract packaged Quartus resource/timing summaries and rebuild the comparison table:

```powershell
python install.py --local . --extract-quartus-summary --run-full-eval
```

The FPGA UART path is a low-speed validation/control path. It is not a full
Gemma ONNX execution path and does not imply end-to-end speedup. The JTAG path
is now the preferred no-external-UART board validation route, but it is also a
correctness/overhead validation path rather than a performance interface unless
a real passing cycle-counter board log is archived. The full-eval option
preserves failed or skipped hardware runs instead of converting them into
passing measurements.
