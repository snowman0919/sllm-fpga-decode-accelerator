# HWP 최종본 변환 절차

현재 환경에서는 `.hwp` 직접 저장 도구가 확인되지 않았다. 생성된 제출용 중간본은 다음과 같다.

- `paper/current/manuscript.md`
- `paper/final/final_manuscript.docx`
- `paper/final/final_manuscript.hwpx`
- `paper/final/final_manuscript_intermediate.html`
- `paper/final/final_manuscript_intermediate.md`

## 권장 수동 변환

1. Hancom Office가 설치된 Windows 환경에서 학술지 HWP 양식을 연다.
2. 우선 `paper/final/final_manuscript.hwpx`를 열어 조판을 확인한다.
3. HWPX 조판이 충분하면 Hancom Office에서 `paper/final/final_manuscript.hwp`로 저장한다.
4. HWPX 조판이 깨지면 `paper/final/final_manuscript.docx`를 열어 본문, 표, 그림, 참고문헌을 양식에 붙여 넣는다.
5. 표 1-8과 그림 1-4의 번호가 유지되는지 확인한다.
6. 그림은 `paper_assets/figures/`의 PNG 원본을 사용한다.
7. 2단 조판, 제목/영문 제목, 초록/Abstract, 키워드, 저자정보, 참고문헌을 확인한다.
8. 최종 파일을 `paper/final/final_manuscript.hwp`로 저장한다.

## 현재 자동 변환 상태

- Markdown -> DOCX: 완료
- Markdown -> HTML: 완료
- Markdown -> HWPX template intermediate: 완료
- DOCX/HWPX -> HWP: 현재 환경에서 실행 도구 없음

## 제출 전 확인

- HWP 페이지 수
- 표가 페이지 경계에서 깨지는지 여부
- 그림 해상도
- 한글 글꼴 대체 여부
- QNN 상태가 integration blocked로 남아 있는지 여부
