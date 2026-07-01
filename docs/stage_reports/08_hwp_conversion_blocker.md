# 08단계 HWP 변환 가능성 점검 보고

작성 시점: 2026-07-01

## 결론

현재 실행 환경에서는 최종 `.hwp` 파일을 자동 생성하거나 변환할 수 있는 도구가 확인되지 않았다. `pandoc` 설치 후 DOCX 중간본을 생성했고, 상위 `../paper/`의 학술지 HWPX 양식을 이용해 `paper/final/final_manuscript.hwpx` 중간본도 생성했다. 이후 Nix LibreOffice를 추가로 확인하여 PDF 검토본은 생성했지만, legacy `.hwp` 저장은 export filter 부재로 실패했다. 따라서 `paper/final/final_manuscript.hwp` 산출은 현재 환경만으로는 막혀 있다.

## 확인한 사항

- 저장소 상위 `../paper/`에서 HWP/HWPX 양식 파일을 확인했다.
  - `template_original.hwp`
  - `한국정보기술진흥원_논문양식.hwp`
  - `한국정보기술진흥원_논문양식.noimg.hwpx`
  - `manuscript_논문양식.hwp`
- 로컬 PATH에서 `pandoc`은 확인되었고 DOCX 변환에 사용했다.
- 로컬 PATH에서 `libreoffice`, `soffice`, `hwp5txt`, `hwp5odt`, `pyhwp`는 확인되지 않았다.
- Nix LibreOffice 25.8.5.2를 임시로 실행해 `docx -> hwp`를 시도했으나 `no export filter`로 실패했다.
- Nix LibreOffice 25.8.5.2에서 `hwpx` 입력은 `source file could not be loaded`로 실패했다.
- Nix LibreOffice 25.8.5.2에서 `docx -> pdf`는 성공했고, 검토용 PDF는 14쪽으로 생성되었다.
- PyPI `hwp5`/`hwpx` 패키지를 확인했으나 legacy `.hwp` writer 또는 HWPX-to-HWP converter가 아니었다.
- `ssh win`의 Windows PATH 및 Program Files/User profile 검색에서도 `hwp.exe`, `soffice.exe`, `pandoc.exe`가 확인되지 않았다.
- `scripts/build_final_hwpx.py`로 HWPX 양식 기반 중간본을 생성했고 ZIP 무결성 검사를 통과했다.

## 필요한 사용자 판단

아래 중 하나가 필요하다.

1. Hancom Office가 설치된 환경 또는 변환 가능한 Windows 경로 제공
2. 생성된 `.hwpx` 중간본을 수동으로 `.hwp` 저장하는 절차 허용
3. DOCX/HTML/PDF 중간본을 만든 뒤 사용자가 HWP 양식에 수동 삽입하는 절차 허용

## 현재 가능한 산출물

- 최종 Markdown: `paper/current/manuscript.md`
- DOCX 중간본: `paper/final/final_manuscript.docx`
- HWPX 중간본: `paper/final/final_manuscript.hwpx`
- Markdown 중간본: `paper/final/final_manuscript_intermediate.md`
- HTML 중간본: `paper/final/final_manuscript_intermediate.html`
- PDF 검토본: `paper/final/final_manuscript.pdf`

## 제출 리스크

HWP 최종본이 필수이면, 현재 환경에서 goal을 완료 상태로 둘 수 없다. HWP 변환 도구, Hancom Office 저장 경로, 또는 사용자 승인된 수동 변환 절차가 확보되어야 한다. 현재 LibreOffice 기준 PDF는 14쪽으로 생성되므로, HWP 조판에서도 10쪽 이하 보장은 별도 확인이 필요하다.
