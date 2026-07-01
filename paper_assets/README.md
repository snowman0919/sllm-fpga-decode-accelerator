# 제출용 표/그림 자산

이 디렉터리는 최종 논문과 HWP 변환에 들어갈 표/그림 자산을 보관한다.

- `tables/`: 최종 원고에서 참조하는 CSV 표
- `figures/`: 최종 원고에서 참조하는 PNG/SVG 그림

기존 `assets/` 디렉터리는 1차 마감본과 reviewer-facing main에서 사용한 compact artifact 위치이다. 최종 개정에서는 내부 약어(`c01`, `f01`)가 본문에 직접 노출되지 않도록, 필요한 표/그림을 의미 있는 파일명으로 `paper_assets/`에 복사 또는 재생성한다.

`measured`, `board_measured`, `simulation`, `projected`, `invocation_overhead`는 서로 다른 evidence type이다. 최종 표에서는 이 값을 한 latency ranking처럼 배치하지 않는다.
