# HWP 변환 안내

현재 작업 환경에서는 legacy `.hwp` 직접 저장 도구가 확인되지 않았다. 자동 생성된 제출용 중간 산출물은 다음과 같다.

- `paper/current/manuscript.md`
- `paper/final/final_manuscript_intermediate.md`
- `paper/final/final_manuscript_intermediate.html`
- `paper/final/final_manuscript.docx`
- `paper/final/final_manuscript.hwpx`
- `paper/final/final_manuscript.pdf`

## 권장 변환 절차: HOP 사용

1. HOP 최신 릴리즈를 설치한다.
   - GitHub: `https://github.com/golbin/hop`
   - HOP README 기준 HOP는 HWP/HWPX 열기, HWP 저장, PDF 내보내기, 인쇄, 파일 연결을 지원한다.
2. HOP에서 `paper/final/final_manuscript.hwpx`를 연다.
3. 표, 그림, 2단 조판, 제목, 초록, 참고문헌, 저자정보를 확인한다.
4. 조판이 유지되면 HOP의 저장/다른 이름으로 저장 기능으로 legacy `.hwp`를 생성한다.
5. HOP에서 조판이나 저장이 깨지면 Hancom Office에서 `paper/final/final_manuscript.hwpx` 또는 `paper/final/final_manuscript.docx`를 열어 공식 HWP 양식에 맞게 재저장한다.
6. 최종 HWP에서 페이지 수, 표 분할, 그림 해상도, 한글 글꼴 대체 여부를 확인한다.

## 자동 변환 한계

- Pandoc은 `.hwp` writer를 제공하지 않는다.
- LibreOffice는 `docx -> pdf` 변환은 가능했지만 `docx -> hwp` export filter가 없었다.
- 현재 Linux 작업 환경의 PATH에는 HOP 실행 파일이 없었다.
- HOP v0.3.1 Linux x64 `.deb`를 임시 확인한 결과 실행 파일은 `hop-desktop` GUI 앱이며, 현재 headless 세션에서는 GTK backend 초기화가 실패해 자동 `.hwp` 저장을 수행할 수 없었다.
- 현재 `ssh win` Windows 환경에서 Hancom 실행 파일, registry 항목, COM 자동화 ProgID가 확인되지 않았다.

따라서 legacy `.hwp` 제출본은 HOP 또는 Hancom Office가 설치된 GUI 환경에서 최종 저장해야 한다.
