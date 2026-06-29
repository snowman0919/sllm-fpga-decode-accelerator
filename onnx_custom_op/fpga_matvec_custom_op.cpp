// Scaffold only: the repository currently uses the Python ORT-equivalent UART
// harness. Do not report this file as a working ONNX Runtime custom op until it
// is implemented, built, loaded, and validated.

extern "C" __declspec(dllexport) int FpgaMatVecCustomOpScaffold(void) {
  return 0;
}
