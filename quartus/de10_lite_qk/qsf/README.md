# Verified QSF Workflow

Do not place guessed DE10-Lite pin assignments here.

Use `just import-qsf /path/to/verified.qsf` to copy a trusted board-specific QSF into:

- `verified_de10_lite_pins.qsf`

Trusted sources include:

- Terasic System Builder output
- an official DE10-Lite reference project
- a user-validated DE10-Lite project already known to match the board in use

The file `de10_lite_pins.placeholder.qsf` exists only to document the required signals. It is not sufficient for real board compilation.
