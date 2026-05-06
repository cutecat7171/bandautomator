# 네이버 밴드 자동 답변 봇 🤖

GitHub Actions + Playwright로 밴드 게시글 키워드 감지 후 자동 댓글 작성.

## 구조

```
band-bot/
├── .github/workflows/band-bot.yml   ← 1분마다 자동 실행
├── bot.py                           ← 핵심 봇 로직
├── keywords.json                    ← 키워드 & 답변 설정
└── requirements.txt
```

---

## 설치 방법

### 1단계: GitHub Gist 생성 (replied 저장소)

1. https://gist.github.com 접속
2. 파일명: `replied.json`, 내용: `[]` 로 **Secret Gist** 생성
3. Gist URL에서 ID 복사: `https://gist.github.com/{username}/{GIST_ID}`

### 2단계: GitHub Personal Access Token 발급

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 권한: `gist` 체크
3. 토큰 복사해두기

### 3단계: 레포 Secrets 등록

레포 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|------------|---|
| `NAVER_ID` | 네이버 아이디 |
| `NAVER_PW` | 네이버 비밀번호 |
| `BAND_URL` | `https://band.us/band/숫자ID` |
| `GIST_ID`  | 위에서 만든 Gist ID |
| `GH_TOKEN` | 위에서 발급한 토큰 |

### 4단계: keywords.json 수정

```json
{
  "keywords": [
    { "word": "찾는 키워드", "reply": "자동으로 달릴 댓글 내용" }
  ]
}
```

### 5단계: Actions 활성화

레포 → Actions 탭 → `Band Bot` → `Enable workflow`

---

## 주의사항

- **CSS 선택자**: 밴드 UI가 업데이트되면 `bot.py` 안의 선택자를 수정해야 할 수 있음
- **속도**: GitHub Actions cron 최소 단위는 1분 (더 빠르게 하려면 루프 방식으로 변경 필요)
- **보안**: Secrets에 저장된 계정 정보는 로그에 노출되지 않음
- **무료 플랜 한도**: 월 2,000분 → 1분마다 실행 시 약 44시간치 (5일 프로젝트라면 충분)

---

## 선택자가 안 맞을 때

밴드는 SPA라 선택자가 자주 바뀜. 브라우저 개발자도구(F12)로 직접 확인:

```javascript
// 콘솔에서 실행해서 선택자 확인
document.querySelectorAll("div[class*='post']").length
```

`bot.py` 상단의 선택자 부분만 수정하면 됨.
