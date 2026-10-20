# 삼성전자 DART 재무 분석 에이전트

[![🔗 대시보드 바로가기](https://img.shields.io/badge/%F0%9F%94%97-%EB%8C%80시보드%20바로가기-1751D0?style=for-the-badge)](https://hsc-class01.github.io/cs-samsung/)

OpenDART에서 삼성전자(005930)의 사업·반기·분기 재무제표를 수집하고, 주요 재무수치와 재무비율을 계산해 GitHub Pages 대시보드에 게시합니다.

## 실행 전 설정

1. [OpenDART](https://opendart.fss.or.kr/)에서 API 인증키를 발급합니다.
2. GitHub 저장소 **Settings → Secrets and variables → Actions → New repository secret**에서 이름을 `DART_API_KEY`로 지정해 인증키를 등록합니다. 키를 소스 코드나 커밋에 직접 넣지 마세요.
3. **Settings → Pages → Build and deployment → Source**에서 **GitHub Actions**를 선택합니다.
4. **Actions → Monthly DART update → Run workflow**로 최초 수집을 실행합니다. 이후 매월 1일 09:00 KST에 자동 갱신됩니다.
5. **Actions → Deploy dashboard to GitHub Pages → Run workflow**를 실행하거나 main에 변경을 push하면 대시보드가 배포됩니다.

대시보드: [https://hsc-class01.github.io/cs-samsung/](https://hsc-class01.github.io/cs-samsung/)

## API 키 설정 및 로컬 실행

Windows PowerShell:

```powershell
$env:DART_API_KEY = "발급받은_API_키"
python -m pip install -r requirements.txt
python src/update_dart.py
```

macOS/Linux:

```bash
export DART_API_KEY="발급받은_API_키"
python -m pip install -r requirements.txt
python src/update_dart.py
```

## 데이터 범위와 해석

- 보고서 목록은 2010년부터 수집하고 재무제표 API 수치는 `config.json`에 설정된 시작연도부터 수집합니다.
- 연결재무제표(CFS)를 우선 사용하고, 해당 계정이 없으면 별도재무제표(OFS)를 사용합니다.
- 대시보드의 금액은 원 단위 데이터를 억원으로 환산해 표시합니다.
- 영업이익률·순이익률·ROE·ROA·부채비율·유동비율을 계산합니다. 분기/반기 손익계정은 DART API 제공 금액 기준이며 기간 간 단순 비교 시 공시 원문을 함께 확인하세요.
- 원문 공시 ZIP 저장은 기본 비활성화되어 있습니다. 설정을 켜면 저장소 크기가 빠르게 증가할 수 있습니다.

## 국내 Peer Firms

| 기업 | 종목코드 | 비교 관점 |
|---|---:|---|
| SK하이닉스 | 000660 | 메모리 반도체·DS 사업 비교 |
| LG전자 | 066570 | 종합 전자·가전 사업 비교 |
| DB하이텍 | 000990 | 반도체 파운드리 비교 |
| 삼성전기 | 009150 | 전자부품·부품 밸류체인 비교 |

## 구성

- `src/update_dart.py`: DART 수집, 재무지표 계산, JSON 출력
- `config.json`: 기업, 기간, 계정명, peer 설정
- `docs/index.html`: 시각화 및 연간/반기/분기 표
- `docs/data/`: 대시보드 JSON 데이터
- `.github/workflows/monthly-update.yml`: 월간 데이터 갱신
- `.github/workflows/deploy-pages.yml`: GitHub Pages 배포

대시보드는 투자 판단을 위한 참고 자료이며, 공시 원문과 수치를 함께 확인하세요.
