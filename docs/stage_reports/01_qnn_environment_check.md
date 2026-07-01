# Phase 1 QNN 설치 및 실행 가능성 점검

## 실행한 확인

목표 파일은 Windows/QNN 설치 경로를 다음과 같이 지정했다.

- 접속: `ssh win`
- QNN 설치 위치: `C:\Users\dbsgu\dev\qinst`

`ssh win` 접속 자체는 성공했다. 그러나 bash home, `/mnt/c/Users/dbsgu`, Windows PowerShell `$HOME` 기준 모두에서 지정 경로를 찾지 못했다.

## 명령 결과 요약

```text
$ ssh win 'bash -lc "pwd; ls -la ~/dev/qinst; find ~/dev/qinst -maxdepth 3 -type f | head -100"'
/mnt/c/Users/dbsgu
ls: cannot access '/home/kotori9/dev/qinst': No such file or directory
find: '/home/kotori9/dev/qinst': No such file or directory
```

```text
$ ssh win 'bash -lc "ls -la /mnt/c/Users/dbsgu/dev/qinst 2>/dev/null; find /mnt/c/Users/dbsgu/dev/qinst -maxdepth 3 -type f 2>/dev/null | head -100"'
<no output>
```

```text
$ ssh win "powershell -NoProfile -Command '$p = Join-Path $HOME \"dev/qinst\"; ...'"
HOME=C:\Users\dbsgu
QNN=C:\Users\dbsgu\dev\qinst
False
```

## 판정

현재 확인 가능한 Windows 환경에는 지정된 QNN 설치 경로 `C:\Users\dbsgu\dev\qinst`가 없다.

따라서 다음 항목은 아직 판단할 수 없다.

- QNN SDK 버전
- Android AAR 또는 native library 존재 여부
- ONNX Runtime QNN EP artifact 존재 여부
- QNN backend library 존재 여부
- Y700에서 QNN EP micrograph benchmark 가능 여부

## 중단 조건

목표 파일의 중단 조건 2번에 해당한다.

> `~/dev/qinst`에 QNN 설치가 없거나 구조를 파악할 수 없는 경우

따라서 QNN 추가 실험, QNN 결과 반영, QNN 관련 원고 수정은 사용자 확인 전 임의로 진행하지 않는다.

## 사용자 확인 필요

다음 중 하나가 필요하다.

1. Windows의 실제 QNN 설치 경로 제공
2. `ssh win`에서 접근 가능한 위치로 QNN SDK 또는 ONNX Runtime QNN artifact 배치
3. 이번 제출본에서는 QNN 추가 실험 없이 CPU/NNAPI 결과로 제한하라는 승인
