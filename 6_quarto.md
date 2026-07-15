# AI 현황판 셋업 노트 — 비개발자 동료에게 설치해주며 설명하기

> README는 개발자용이라 이 노트로 대신 설명. 설치는 내가 직접 해주고,
> 상대방은 "평소에 쓰는 법" 섹션만 기억하면 됨.

## 0. 먼저 말로 설명할 개념 (2분)

- **이 사이트가 만들어지는 원리**: 우리가 쓰는 건 문서 파일(글 + 차트 코드)이고,
  "Quarto"라는 프로그램이 이걸 웹페이지로 변환해준다.
- **차트의 숫자**는 사내 데이터베이스(PocketBase)에서 가져온다.
  그래서 "데이터 받아오기"라는 별도 단계가 있다.
- **준비물 4가지**: Quarto(변환기), Node.js(데이터 받아오는 도구),
  Python(차트 그리는 도구), Positron(편집 프로그램 — 워드 같은 것).

## 1. 설치 순서 (내가 해줄 것, 위에서부터 차례로)

1. **Quarto 설치** — 터미널에서:
   ~~~bash
   brew install quarto
   ~~~
   (Homebrew 없으면 그것부터. 관리자 비밀번호 필요할 수 있음)
2. **프로젝트 받기**:
   ~~~bash
   git clone https://gitlab.gabia.com/ai/docs/ai-status-doc
   cd ai-status-doc
   npm install
   ~~~
3. **API 키 설정** — 데이터베이스 접속용 열쇠:
   ~~~bash
   cp .env.example .env
   ~~~
   `.env` 파일을 열어 `POCKETBASE_APIKEY` 값 입력 (키는 내가 전달)
4. **Python 도구함 만들기** (최초 1회):
   ~~~bash
   bash scripts/setup-venv.sh
   ~~~
   → 설명 멘트: "차트 그리는 도구들을 이 폴더 전용으로 설치하는 것"
5. **데이터 최초 1회 받아오기**:
   ~~~bash
   npm run sync:data
   ~~~
   → 이걸 안 하면 미리보기가 "데이터 파일 없음" 오류로 실패함
6. **Positron 설치** — https://positron.posit.co/ 에서 다운로드 (Mac은 Apple Silicon 선택)
   → 설치 후 Positron으로 프로젝트 폴더 열기

## 2. 평소에 쓰는 법 (상대방이 기억할 것은 이게 전부)

1. Positron 실행 → ai-status-doc 폴더 열기
2. Positron 안의 터미널에 입력:
   ~~~bash
   npm run preview
   ~~~
3. 브라우저가 열리면 → 문서 파일을 수정하고 저장할 때마다 화면이 자동으로 바뀜
4. 차트 숫자를 최신으로 갱신하고 싶으면:
   ~~~bash
   npm run sync:data
   ~~~

⚠️ **꼭 Positron 안의 터미널에서 실행할 것.**
맥 기본 터미널에서 하면 Python 도구를 못 찾아서 오류가 남.
(Positron은 프로젝트를 열 때 도구함을 자동으로 연결해줘서 되는 것)

## 3. 오류가 나면 (전화 오면 이렇게 안내)

| 증상 | 원인 | 해결 |
|---|---|---|
| "pandas가 없다", "jupyter 못 찾음" | Positron 밖에서 실행함 | Positron 터미널에서 다시 실행 |
| "데이터 파일이 없다" (aichat-stats-data.json) | 데이터를 안 받아옴 | `npm run sync:data` 먼저 실행 |
| 그래도 안 되면 | — | 나한테 연락 📞 |