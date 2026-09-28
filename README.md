[![대시보드 바로가기](docs/assets/dashboard-badge.svg)](https://hsc-class02.github.io/JY_SAMSUNG/)

# Samsung Financial Intelligence

OpenDART에서 삼성전자(고유번호 `00126380`)의 사업보고서·반기보고서·분기보고서를 수집하고, 핵심 재무수치와 재무비율을 계산해 GitHub Pages 대시보드로 배포하는 자동화 프로젝트입니다.

## 주요 기능

- 2010년 이후 사업·반기·분기보고서 수집
- 연결재무제표(CFS) 우선, 미제공 시 별도재무제표(OFS) 사용
- 매출액, 영업이익, 순이익, 자산·부채·자본, 현금흐름, CAPEX, FCF, EBITDA 추출
- 수익성·안정성·효율성·현금흐름 비율 자동 계산
- 매월 1일 오전 9시 17분(KST) GitHub Actions 자동 갱신
- GitHub Pages 반응형 대시보드 및 카테고리별 CSV 내보내기

> OpenDART 정형 재무제표 API는 2015년 이후 데이터를 제공합니다. 2010~2014년은 공시 목록·원문 API에서 대상 보고서를 찾아 표를 보완 파싱하므로 문서 서식에 따라 일부 항목이 비어 있을 수 있습니다. 경고 내역은 `data/financials.json`의 `warnings`에서 확인할 수 있습니다.

## 빠른 설치

1. 이 ZIP의 모든 파일을 저장소 루트에 업로드합니다.
2. `github-workflows/monthly-update.yml`과 `github-workflows/pages.yml`을 GitHub 웹에서 각각 `.github/workflows/` 아래에 생성합니다. 자세한 방법은 `UPLOAD_GUIDE.md`를 참고하세요.
3. OpenDART 인증키를 저장소의 `Settings → Secrets and variables → Actions → New repository secret`에서 등록합니다.
   - Name: `DART_API_KEY`
   - Secret: OpenDART에서 발급받은 인증키
4. `Actions → Monthly DART Update → Run workflow`를 한 번 실행합니다.
5. `Settings → Pages → Source`가 `GitHub Actions`인지 확인합니다.

대시보드: <https://hsc-class02.github.io/JY_SAMSUNG/>

## 로컬 실행

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DART_API_KEY="발급받은_인증키"
python -m src.collect --start-year 2010
python -m http.server 8000 --directory docs
```

브라우저에서 <http://localhost:8000>을 엽니다. Windows PowerShell에서는 환경변수를 `$env:DART_API_KEY="발급받은_인증키"`로 설정합니다.

## 계산 지표

| 구분 | 지표 |
|---|---|
| 재무상태 | 자산, 유동자산, 현금성자산, 매출채권, 재고자산, 유형자산, 부채, 차입금·사채·리스부채, 자본 |
| 손익 | 매출액, 매출총이익, 판관비, 영업이익, 세전이익, 순이익, 지배주주순이익, EBITDA |
| 현금흐름 | 영업·투자·재무현금흐름, CAPEX, FCF, 순차입금 |
| 수익성 | 매출총이익률, 영업이익률, 순이익률, EBITDA 마진, ROA, ROE, ROIC |
| 안정성 | 유동비율, 당좌비율, 부채비율, 자기자본비율, 차입금의존도, 이자보상배율, 순차입금/EBITDA |
| 효율성·성장 | 총자산회전율, DSO, DIO, DPO, CCC, 매출성장률, CFO/순이익 |

PER·PBR·EV/EBITDA는 주가·시가총액 데이터가 필요하므로 DART 전용 수집 범위에서는 계산하지 않습니다.
상세 산식과 연환산 기준은 [`METHODOLOGY.md`](METHODOLOGY.md)를 참고하세요.

## 국내 Peer Firms

| 기업 | 종목코드 | 비교 영역 | 선정 이유 |
|---|---:|---|---|
| SK하이닉스 | 000660 | 메모리 반도체 | 삼성전자 DS 부문의 국내 핵심 비교기업 |
| LG전자 | 066570 | 가전·전자제품 | 완제품과 글로벌 소비자 전자사업 비교 |
| LG디스플레이 | 034220 | 디스플레이 | 디스플레이 패널 업황과 설비투자 비교 |
| 삼성전기 | 009150 | 전자부품 | MLCC·카메라모듈 등 전자부품 수요 비교 |
| DB하이텍 | 000990 | 파운드리 | 국내 시스템반도체 생산기업 비교 |
| 한미반도체 | 042700 | 반도체 장비 | AI·HBM 투자 사이클의 공급망 비교 |

## 저장소 구조

```text
config/              계정 매핑·비교기업 설정
data/                생성된 JSON·CSV 및 원본 캐시
docs/                GitHub Pages 대시보드
github-workflows/    숨김 폴더 없이 전달하는 Actions 원본
src/                 수집·보완 파싱·비율 계산 코드
tests/               계산 및 파서 단위 테스트
```

데이터는 투자 권유가 아닌 학습·분석용이며, 중요한 판단 전 원문 공시를 확인해야 합니다.
