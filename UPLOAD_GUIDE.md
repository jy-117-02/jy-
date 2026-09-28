# GitHub 업로드·배포 안내

이 패키지는 웹 업로드가 막히지 않도록 **숨김 파일과 숨김 폴더를 포함하지 않습니다.** GitHub Actions가 요구하는 `.github` 폴더만 GitHub 웹에서 생성하면 됩니다.

## 1. 프로젝트 파일 업로드

1. <https://github.com/HSC-Class02/JY_SAMSUNG>에서 `Add file → Upload files`를 선택합니다.
2. ZIP을 먼저 압축 해제합니다.
3. 압축 해제한 `JY_SAMSUNG` 폴더 안의 파일·폴더를 모두 업로드합니다.
4. `Commit changes`를 선택합니다.

## 2. 워크플로 파일 2개 생성

GitHub 저장소에서 `Add file → Create new file`을 선택해 다음 두 파일을 만듭니다.

| GitHub에 만들 경로 | 복사할 파일 |
|---|---|
| `.github/workflows/monthly-update.yml` | `github-workflows/monthly-update.yml` 전체 내용 |
| `.github/workflows/pages.yml` | `github-workflows/pages.yml` 전체 내용 |

파일명 입력칸에 `.github/workflows/monthly-update.yml`처럼 전체 경로를 입력하면 GitHub가 폴더를 자동 생성합니다. 이 방법은 로컬 숨김 폴더 업로드 문제를 피합니다.

## 3. OpenDART API 키 등록

1. <https://opendart.fss.or.kr/>에서 인증키를 발급받습니다.
2. 저장소 `Settings → Secrets and variables → Actions`로 이동합니다.
3. `New repository secret`을 누릅니다.
4. Name에 `DART_API_KEY`, Secret에 발급받은 키를 입력합니다.

API 키는 코드나 README에 직접 적지 마세요. GitHub Secret은 로그에 키가 노출되는 것을 방지합니다.

## 4. 첫 수집 및 Pages 배포

1. `Actions → Monthly DART Update → Run workflow`를 누릅니다.
2. 최초 실행은 2010년 이후 데이터를 수집하므로 이후 월별 실행보다 오래 걸릴 수 있습니다.
3. `Settings → Pages → Build and deployment → Source`에서 `GitHub Actions`를 선택합니다.
4. 배포 후 <https://hsc-class02.github.io/JY_SAMSUNG/>에서 대시보드를 확인합니다.

워크플로는 매월 1일 09:17 KST에 실행됩니다. GitHub 스케줄은 혼잡 상황에서 몇 분 늦게 시작할 수 있습니다.

## 5. 저장소 About 링크 설정

1. 저장소 첫 화면 오른쪽 `About` 옆 톱니바퀴를 누릅니다.
2. Website에 `https://hsc-class02.github.io/JY_SAMSUNG/`를 입력합니다.
3. `Save changes`를 누릅니다.

README 최상단의 파란색 `🔗 대시보드 바로가기` 배지는 이미 같은 주소로 연결되어 있습니다.

## 오류가 날 때

- `DART_API_KEY is not configured`: Secret 이름의 철자와 대문자를 확인합니다.
- Pages 권한 오류: `Settings → Actions → General → Workflow permissions`에서 Read and write permissions를 허용합니다.
- Pages 배포 오류: `Settings → Pages`의 Source를 GitHub Actions로 다시 지정합니다.
- 일부 2010~2014 수치가 비어 있음: 구형 원문 표 형식 차이입니다. `data/financials.json`의 `warnings`를 확인하세요.
