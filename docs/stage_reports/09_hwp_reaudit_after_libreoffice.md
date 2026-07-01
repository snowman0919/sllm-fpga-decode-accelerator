# 09단계 HWP 재점검 보고

작성 시점: 2026-07-01

## 목적

이전 최종 보고 이후 goal audit 기준에서 `paper/final/final_manuscript.hwp`가 실제로 존재하지 않는 문제가 남아 있음을 확인했다. 따라서 현재 환경에서 legacy `.hwp` 직접 생성 가능성을 추가로 재점검했다.

## 재점검 결과

- `paper/final/final_manuscript.hwpx`는 존재하며 ZIP 무결성 검사를 통과했다.
- `paper/final/final_manuscript.docx`는 pandoc으로 생성되어 있다.
- Nix LibreOffice 25.8.5.2를 실행해 `docx -> hwp`를 시도했으나 `no export filter`로 실패했다.
- 같은 LibreOffice 실행에서 `hwpx` 입력은 `source file could not be loaded`로 실패했다.
- LibreOffice를 통한 `docx -> pdf`는 성공했고, `paper/final/final_manuscript.pdf` 검토본을 생성했다. PDF는 14쪽이다.
- PyPI의 `hwp5` 0.1.0은 calendar/ICS 분석용 패키지였고 HWP 문서 writer가 아니었다.
- PyPI의 `hwpx` 1.1.1은 실사용 가능한 HWPX/HWP 변환기를 포함하지 않았다.
- `ssh win` Windows 환경에서 `hwp.exe`, `Hwp.exe`, `HwpConverter.exe`, `soffice.exe`, `libreoffice.exe`, `pandoc.exe`를 `Get-Command`로 확인했지만 PATH에 등록된 변환 도구가 없었다.
- 같은 Windows 환경의 uninstall registry에서 Hancom/HWP/Hangul/한컴/LibreOffice/OpenOffice/Pandoc 항목이 확인되지 않았다.
- Hancom 자동화 COM 후보인 `HWPFrame.HwpObject`, `HWPFrame.HwpObject.1`, `HwpCtrl.HwpCtrl`, `HwpObject.HwpObject`는 모두 `REGDB_E_CLASSNOTREG`로 실패했다.

## 결론

현재 Linux/Nix/pandoc/Python 패키지 경로와 `ssh win` Windows 경로 모두에서 legacy `.hwp`를 생성할 수 있는 검증된 writer가 없다. `paper/final/final_manuscript.hwp`는 아직 미생성 상태이며, Hancom Office가 설치된 환경에서 `paper/final/final_manuscript.hwpx` 또는 `paper/final/final_manuscript.docx`를 열어 `.hwp`로 저장하는 절차가 필요하다.

## 산출물 상태

- Markdown: 완료
- DOCX: 완료
- HWPX: 완료
- PDF: 완료, 14쪽
- legacy HWP: 미완료

## 제출 리스크

학술지 접수가 `.hwp`만 허용하면 현재 goal은 완료로 볼 수 없다. HWPX 또는 DOCX 제출이 허용되거나, Hancom Office 저장 단계가 완료되어야 한다.
