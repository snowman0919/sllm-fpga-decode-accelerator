# DE10-Lite UART MatVec Wiring

This note prepares the UART Decode MatVec design for board execution. It intentionally does not assign arbitrary GPIO pins: the actual DE10-Lite header pins must be chosen during board wiring and then copied into the Quartus QSF.

## Hardware Assumptions

- Board: Terasic DE10-Lite / MAX 10
- Host link: external USB-UART adapter connected to a DE10-Lite GPIO header
- UART logic level: 3.3 V TTL
- Default baudrate: 115200 baud
- Protocol: binary packets documented in `docs/uart_protocol.md`
- FPGA top: `UartDecodeMatVecTop`

Do not connect a 5 V UART adapter directly to the FPGA GPIO header. Use a 3.3 V adapter or a level shifter.

## Required Connections

Use a common ground:

| USB-UART adapter | DE10-Lite signal | Notes |
| --- | --- | --- |
| GND | GND on selected GPIO header | Required common reference |
| TXD | `UART_RXD` | Host transmit goes to FPGA receive |
| RXD | `UART_TXD` | Host receive goes to FPGA transmit |

`UART_RXD` and `UART_TXD` are TBD by board wiring. Select two available 3.3 V GPIO pins, then update the UART QSF assignments in `quartus/de10_lite_uart_matvec/qsf/uart_pins.template.qsf`.

## QSF Items To Resolve

The UART project needs these assignments before board compile/programming should be treated as board-ready:

- `CLOCK_50`
- `UART_RXD`
- `UART_TXD`
- `SW[9:0]`
- `KEY[1:0]`
- `LEDR[9:0]`
- `HEX0` through `HEX5`

The current top uses SpinalHDL boot reset. `KEY[0]` is exposed for debug display/status input, not as a full asynchronous board reset.

## Windows COM Port Check

After plugging in the USB-UART adapter:

```powershell
python windows\run_fpga_uart_matvec.py --list-ports
```

Windows Device Manager can also show the COM port under "Ports (COM & LPT)". Use that name with the runner, for example:

```powershell
python windows\run_fpga_uart_matvec.py --port COM5 --baud 115200 --runs 10 --dump-request-hex --dump-response-hex
```

## Quartus Programming Order

1. Generate/mirror Verilog:

   ```bash
   nix develop -c just fpga-uart-verilog
   ```

2. Resolve UART GPIO pins in a QSF. Start from:

   ```text
   quartus/de10_lite_uart_matvec/qsf/uart_pins.template.qsf
   ```

3. Create and compile the Quartus project only after pin assignments are real:

   ```bash
   nix develop -c just fpga-uart-quartus
   ```

4. Program the generated `.sof` from the Windows machine connected to the board.

## Debug LED/HEX Status

`UartDecodeMatVecTop` exposes simple debug status:

- `LEDR[0]`: idle state
- `LEDR[1]`: header receive state
- `LEDR[2]`: payload receive state
- `LEDR[3]`: MatVec core running
- `LEDR[4]`: response transmit state
- `LEDR[5]`: RX byte valid pulse
- `LEDR[6]`: TX busy
- `LEDR[7]`: MatVec done pulse/status
- `LEDR[9:8]`: low status bits
- `HEX0`: status low nibble
- `HEX1`: command low nibble
- `HEX2`: sequence low nibble
- `HEX3`: transmit byte index low nibble
- `HEX4`: state/debug flags
- `HEX5`: switch/key debug nibble

Expected first test behavior: `--list-ports` finds the adapter, programming succeeds, the board returns a MATVEC response, and the host runner reports `correctness_pass=true`. Until that real COM-port log exists, FPGA latency remains pending.
