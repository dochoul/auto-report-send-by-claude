#!/usr/bin/env python3
"""저장소의 마크다운 문서를 하이웍스 SMTP로 발송 (클라우드 루틴용).

- 새로 추가되었거나 내용이 변경된 .md 파일을 찾아 메일로 발송한다.
- README.md, CLAUDE.md는 발송 대상에서 제외한다.
- 발송 이력은 저장소 루트의 sent-state.json(파일경로 -> 내용 해시)으로 관리한다.
  발송 후 이 파일을 커밋/푸시해야 다음 실행에서 중복 발송되지 않는다.
- 필요한 환경변수: HIWORKS_SMTP_HOST, HIWORKS_SMTP_PORT, HIWORKS_SMTP_USER,
  HIWORKS_SMTP_PASSWORD, (선택) REPORT_TO
- 사용법: python3 send_report.py [--dry-run] [--to EMAIL]
"""
import argparse
import hashlib
import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
STATE_FILE = REPO_DIR / "sent-state.json"
EXCLUDE = {"readme.md", "claude.md"}


def require_env():
    keys = ["HIWORKS_SMTP_HOST", "HIWORKS_SMTP_PORT", "HIWORKS_SMTP_USER", "HIWORKS_SMTP_PASSWORD"]
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        print(f"ERROR: 환경변수 미설정: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    return {k: os.environ[k] for k in keys}


def find_docs():
    return sorted(
        p for p in REPO_DIR.rglob("*.md")
        if ".git" not in p.parts and p.name.lower() not in EXCLUDE
    )


def subject_for(path, text):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return path.stem


def send_mail(env, to, subject, body):
    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = env["HIWORKS_SMTP_USER"]
    msg["To"] = to
    msg["Date"] = formatdate(localtime=True)
    with smtplib.SMTP_SSL(env["HIWORKS_SMTP_HOST"], int(env["HIWORKS_SMTP_PORT"]), timeout=30) as s:
        s.login(env["HIWORKS_SMTP_USER"], env["HIWORKS_SMTP_PASSWORD"])
        s.send_message(msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="발송하지 않고 대상만 출력")
    ap.add_argument("--to", default=os.environ.get("REPORT_TO", "kiki@gabia.com"))
    args = ap.parse_args()

    env = require_env()
    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}

    sent, failed = [], []
    for doc in find_docs():
        text = doc.read_text(encoding="utf-8")
        digest = hashlib.sha256(text.encode()).hexdigest()
        rel = str(doc.relative_to(REPO_DIR))
        if state.get(rel) == digest:
            continue
        subject = subject_for(doc, text)
        if args.dry_run:
            print(f"DRY-RUN: would send '{subject}' ({rel}) -> {args.to}")
            continue
        try:
            send_mail(env, args.to, subject, text)
            state[rel] = digest
            sent.append(f"{subject} ({rel})")
            print(f"SENT: {subject} ({rel}) -> {args.to}")
        except Exception as e:
            failed.append(f"{rel}: {e}")
            print(f"ERROR: {rel} 발송 실패: {e}", file=sys.stderr)

    if not args.dry_run and sent:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")

    print(f"RESULT: sent={len(sent)} failed={len(failed)}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
