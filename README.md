# 삼성전자 OpenDART 재무분석 Agent

삼성전자(고유번호 `00126380`) 사업보고서의 연결재무제표를 OpenDART에서 수집하고, 핵심 재무수치와 비율을 계산해 GitHub Pages 대시보드로 보여줍니다. 매일 GitHub Actions가 새 자료를 확인합니다.

## 1. ZIP을 저장소에 올리기

1. 이 ZIP의 **안쪽 파일 전체**를 `https://github.com/jy-117-02/jy-` 저장소 루트에 업로드합니다.
2. 기본 브랜치는 `main`이어야 합니다.
3. OpenDART에서 API 인증키를 발급받습니다: https://opendart.fss.or.kr/

## 2. API 키 입력 (코드에 직접 입력하지 마세요)

GitHub 저장소에서 `Settings` → `Secrets and variables` → `Actions` → `New repository secret`을 선택합니다.

- Name: `DART_API_KEY`
- Secret: OpenDART에서 발급받은 40자리 인증키

저장 후 `Actions` → `Update Samsung financial data` → `Run workflow`를 한 번 실행합니다. 성공하면 `data/`와 `docs/data/`에 JSON 및 CSV가 생성됩니다.

## 3. GitHub Pages 공개

`Settings` → `Pages` → `Build and deployment` → Source를 **GitHub Actions**로 선택합니다. 이후 `Deploy dashboard to GitHub Pages`가 실행되며 주소는 일반적으로 아래와 같습니다.

`https://jy-117-02.github.io/jy-/`

## 4. 로컬 실행

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DART_API_KEY="발급받은키"  # Windows PowerShell: $env:DART_API_KEY="발급받은키"
python -m src.update_data
python -m http.server 8000 -d docs
```

브라우저에서 `http://localhost:8000`을 엽니다.

## 산출 지표

- 주요 수치: 매출액, 영업이익, 당기순이익, 자산·유동자산, 부채·유동부채, 자본, 현금및현금성자산, 영업·투자·재무활동현금흐름
- 비율: 영업이익률, 순이익률, ROE, ROA, 부채비율, 유동비율
- 새 지표 추가: `config/metrics.json`에 표준계정ID 또는 계정명을 추가하고 대시보드 표시 코드를 확장합니다.

## 주의

- API 응답의 계정명 차이를 고려해 표준계정ID를 우선 사용하고 계정명을 보조로 사용합니다.
- 비율은 단순 기말잔액 기준입니다. 엄밀한 평균자산·평균자본 기반 ROA/ROE와 차이가 날 수 있습니다.
- 첨부 지표표가 있다면 `config/metrics.json`을 그 기준에 맞춰 확장하면 됩니다.
