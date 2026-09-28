# 삼성전자 DART 재무 분석 에이전트

[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97-%EB%8C%80%EC%8B%9C%EB%B3%B4%EB%93%9C%20%EB%B0%94%EB%A1%9C%EA%B0%80%EA%B8%B0-1751D0?style=for-the-badge)](https://OWNER.github.io/REPOSITORY/)

OpenDART로 삼성전자(005930)의 사업·반기·분기보고서를 수집하고, 재무수치 및 재무비율을 계산해 GitHub Pages 대시보드에 게시하는 정적 분석 에이전트입니다.

> **배지 링크 설정:** 위 `OWNER`와 `REPOSITORY`를 실제 GitHub 계정명과 저장소명으로 교체하세요. 사용자가 제공하려던 배지 이미지가 이 대화에 첨부되지 않아, 기본 배지를 넣었습니다. `assets/dashboard-badge.png`에 원하는 이미지를 추가한 뒤 Markdown 이미지 URL만 교체하면 됩니다.

## 범위와 데이터 기준

- **보고서 메타데이터:** 2010년부터 사업보고서(annual), 반기보고서(half-year), 분기보고서(quarterly)를 수집합니다.
- **재무 수치:** OpenDART의 XBRL 단일회사 전체재무제표 API를 이용합니다. API 기반 수치 수집 시작연도는 `config.json`에서 **2015년**으로 설정했습니다. 2010~2014년은 보고서 목록과 DART 열람 링크를 보존합니다.
- **지표:** 매출액, 영업이익, 당기순이익, 자산·부채·자본, 유동자산·유동부채 / 영업이익률, 순이익률, ROE, ROA, 부채비율, 유동비율.
- **연결 우선:** 동일 계정이 존재하면 CFS(연결), 없으면 OFS(별도)를 선택합니다.

## API 키 설정 및 최초 데이터 생성

1. [OpenDART](https://opendart.fss.or.kr/)에서 인증키를 발급받습니다.
2. GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret**에서 이름을 정확히 `DART_API_KEY`로 하여 키를 저장합니다. API 키를 파일·코드·커밋에 넣지 마세요.
3. 저장소의 **Actions → Monthly DART update → Run workflow**를 실행합니다. `docs/data/financials.json`과 `reports.json`이 생성되어 커밋됩니다.
4. **Settings → Pages → Build and deployment → Source: GitHub Actions**를 한 번 선택합니다. 이후 `Deploy dashboard to GitHub Pages` 작업이 자동 배포합니다.
5. 배포 URL은 `https://OWNER.github.io/REPOSITORY/`입니다. 이 URL을 저장소 오른쪽 **About → Website**에 넣으면 About에서 바로 대시보드로 이동합니다.

## 자동 업데이트

`.github/workflows/monthly-update.yml`은 매월 **1일 09:00 KST**(GitHub cron UTC 기준 `0 0 1 * *`)에 실행됩니다. 변경된 데이터만 봇 커밋으로 저장하고, 해당 커밋이 Pages 배포 워크플로를 실행합니다. 두 워크플로 모두 현재 GitHub Actions 문법/액션 버전으로 작성되었고, API 키 미설정 시 의도적으로 실패 메시지를 남깁니다.

## 원문 보고서 저장 정책

기본값은 Git 저장소 용량을 보호하기 위해 수신번호, 제출일, DART 열람 URL을 `docs/data/reports.json`에 저장합니다. 원문 ZIP까지 보관하려면 `config.json`의 `download_raw_reports`를 `true`로 바꾸세요. 대형 ZIP이 누적되면 GitHub 일반 저장소 제한을 넘을 수 있으므로 Git LFS 또는 별도 스토리지를 권장합니다.

## 국내 Peer Firms

| 기업 | 종목코드 | 선정 근거 |
|---|---:|---|
| SK하이닉스 | 000660 | 메모리 반도체 |
| LG전자 | 066570 | 소비자 전자·가전 |
| DB하이텍 | 000990 | 파운드리 |
| 삼성전기 | 009150 | 전자부품 |

## 구조

```text
src/update_dart.py                 수집·정규화·비율계산
config.json                        지표 계정명, 수집 범위, peers 설정
docs/index.html                    GitHub Pages 대시보드
docs/data/*.json                   Actions가 생성/갱신하는 데이터
.github/workflows/monthly-update.yml  월간 수집
.github/workflows/deploy-pages.yml    Pages 배포
```

## 로컬 테스트

```bash
export DART_API_KEY='발급받은_키'
pip install -r requirements.txt
python src/update_dart.py
```

`docs/index.html`은 정적 파일입니다. 로컬에서 확인할 때는 `python -m http.server --directory docs 8000` 후 `http://localhost:8000`을 여세요.
