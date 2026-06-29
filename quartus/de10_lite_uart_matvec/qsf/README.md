# QSF Notes

The UART project reuses the verified DE10-Lite QSF when available:

```text
quartus/de10_lite_qk/qsf/verified_de10_lite_pins.qsf
```

Before claiming board validation, verify that the imported QSF assigns `UART_RXD` and `UART_TXD` to the physical pins used by the Windows host UART adapter.
