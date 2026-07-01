# HWP 변환 안내

현재 작업 환경에서는 legacy `.hwp` 직접 저장 도구가 확인되지 않았다. 자동 생성된 제출용 중간 산출물은 다음과 같다.

- `paper/current/manuscript.md`
- `paper/final/final_manuscript_intermediate.md`
- `paper/final/final_manuscript_intermediate.html`
- `paper/final/final_manuscript.docx`
- `paper/final/final_manuscript.hwpx`
- `paper/final/final_manuscript.pdf`

## 권장 변환 절차

1. Hancom Office가 설치된 Windows 환경에서 `paper/final/final_manuscript.hwpx`를 연다.
2. 표, 그림, 2단 조판, 제목, 초록, 참고문헌, 저자정보를 확인한다.
3. 조판이 유지되면 Hancom Office에서 `paper/final/final_manuscript.hwp`로 저장한다.
4. HWPX 조판이 깨지면 `paper/final/final_manuscript.docx`를 공식 HWP 양식에 붙여 넣고, `paper_assets/figures/`의 PNG 원본을 사용해 그림을 재삽입한다.
5. 최종 HWP에서 페이지 수, 표 분할, 그림 해상도, 한글 글꼴 대체 여부를 확인한다.

## 자동 변환 한계

- Pandoc은 `.hwp` writer를 제공하지 않는다.
- LibreOffice는 `docx -> pdf` 변환은 가능했지만 `docx -> hwp` export filter가 없었다.
- 현재 `ssh win` Windows 환경에서 Hancom 실행 파일, registry 항목, COM 자동화 ProgID가 확인되지 않았다.

따라서 legacy `.hwp` 제출본은 Hancom Office가 설치된 환경에서 최종 저장해야 한다.
