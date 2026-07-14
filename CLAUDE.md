# auto-report-send-by-claude 루틴 지침

이 저장소는 마크다운 문서를 하이웍스 메일로 자동 발송하기 위한 저장소다.
클라우드 루틴이 매일 9시·12시·15시·18시에 실행되어 새/변경된 문서를 발송한다.

## 루틴이 할 일

1. 발송 스크립트를 실행한다:
   ```bash
   python3 send_report.py
   ```
   - 스크립트는 README.md·CLAUDE.md를 제외한 `.md` 파일 중 새로 추가되었거나
     내용이 변경된 것만 골라 SMTP로 발송한다 (이력: `sent-state.json`).
   - SMTP 자격증명은 환경변수(`HIWORKS_SMTP_HOST/PORT/USER/PASSWORD`)에서 읽는다.
     수신자는 `REPORT_TO`, 쉼표로 여러 명 지정
     (기본값 kiki@gabia.com,kimdy@gabia.com).

2. 발송이 1건 이상 성공하면(`RESULT: sent=N`, N>0) `sent-state.json`이 갱신된다.
   **반드시 이 파일을 기본 브랜치(main)에 커밋하고 푸시하라.**
   푸시하지 않으면 다음 실행에서 같은 문서가 중복 발송된다.
   ```bash
   git add sent-state.json
   git commit -m "chore: update sent-state after mail delivery"
   git push origin main
   ```

3. 결과를 보고한다:
   - 발송된 문서 제목 목록과 sent/failed 개수
   - sent=0이면 "발송할 새 문서 없음"

## 오류 처리 규칙

- SMTP 인증 실패(535 등): 재시도하지 말고 "하이웍스 메일 전용 비밀번호 갱신 필요"라고 보고.
- SMTP 접속 자체가 안 되는 경우(connection refused/timeout): 샌드박스 네트워크에서
  포트 465 아웃바운드가 차단된 것이다. 우회를 시도하지 말고 그대로 보고하라.
- 환경변수 미설정 오류: 루틴 환경 설정에 SMTP 환경변수를 추가해야 한다고 보고.
- 스크립트 코드를 수정하지 마라.
