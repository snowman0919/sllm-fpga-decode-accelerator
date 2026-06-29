# Paper Figures

Use this directory for paper-ready figures that you intend to cite directly in the manuscript.

Recommended contents:

- selected DE10-Lite board photo after hardware validation
- cleaned plots copied from `onnx_profile/results/figures/`
- figure captions or placeholder notes while evidence is still being collected

Manual capture policy:

- Raw board photos and videos should be recorded first in `fpga_test/captured/`.
- When you pick one image for the paper, copy it here with a stable filename such as `de10_lite_board_photo.jpg`.
- If the real image is not available yet, keep `de10_lite_board_photo.placeholder.md` as the placeholder.

Interpretation limit:

- A board photo in this directory documents the DE10-Lite validation setup for the INT8 QK dot-product block only.
- It must not be presented as evidence that the FPGA runs Gemma 3 1B or as end-to-end ONNX Runtime comparison data.
