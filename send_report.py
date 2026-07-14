#!/usr/bin/env python3
"""FileBrowser Quantum 파일서버의 마크다운 문서를 하이웍스 SMTP로 발송.

- 파일서버(olive_report 폴더)에서 .md 파일 목록을 조회해, 새로 추가되었거나
  내용이 변경된 것만 메일로 발송한다.
- 발송 이력은 이 스크립트 옆의 sent-state.json(파일명 -> 내용 해시)으로 관리한다.
  클라우드 루틴에서는 발송 후 이 파일을 커밋/푸시해야 중복 발송되지 않는다.
- 필요한 환경변수:
  OLIVE_FB_URL, OLIVE_FB_USER, OLIVE_FB_PASSWORD, (선택) OLIVE_FB_PATH
  HIWORKS_SMTP_HOST, HIWORKS_SMTP_PORT, HIWORKS_SMTP_USER, HIWORKS_SMTP_PASSWORD
  (선택) REPORT_TO
- 사용법: python3 send_report.py [--dry-run] [--to EMAIL]
"""
import argparse
import hashlib
import json
import os
import smtplib
import ssl
import sys
import urllib.parse
import urllib.request
from email.mime.text import MIMEText
from email.utils import formatdate
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent / "sent-state.json"
FB_SOURCE = "files"

# 파일서버 인증서가 확장 필드(SAN/AKI) 없는 사설 CA 발급이라 표준 TLS 검증 불가.
# OLIVE_FB_INSECURE=1 이면 파일서버 요청에 한해 인증서 검증을 끈다.
if os.environ.get("OLIVE_FB_INSECURE") == "1":
    _FB_CTX = ssl._create_unverified_context()
else:
    _FB_CTX = ssl.create_default_context()


def require_env(keys):
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        print(f"ERROR: 환경변수 미설정: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    return {k: os.environ[k] for k in keys}


def http(url, method="GET", headers=None, timeout=30):
    req = urllib.request.Request(url, method=method, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout, context=_FB_CTX) as resp:
        return resp.read().decode("utf-8")


def fb_login(base, user, password):
    q = urllib.parse.urlencode({"username": user, "recaptcha": ""})
    return http(f"{base}/api/auth/login?{q}", method="POST",
                headers={"X-Password": password, "X-Secret": ""}).strip()


def fb_list_md(base, token, path):
    q = urllib.parse.urlencode({"path": path, "source": FB_SOURCE})
    data = json.loads(http(f"{base}/api/resources?{q}",
                           headers={"Cookie": f"filebrowser_quantum_jwt={token}"}))
    return sorted(
        f["name"] for f in data.get("files") or []
        if f.get("type") != "directory" and f["name"].lower().endswith(".md")
        and f["name"].lower() not in ("readme.md", "claude.md")
    )


def fb_download(base, token, path, name):
    ref = urllib.parse.quote(f"{FB_SOURCE}::{path}{name}", safe="")
    return http(f"{base}/api/raw?files={ref}",
                headers={"Cookie": f"filebrowser_quantum_jwt={token}"})


def subject_for(name, text):
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip()
    return Path(name).stem


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

    fb = require_env(["OLIVE_FB_URL", "OLIVE_FB_USER", "OLIVE_FB_PASSWORD"])
    smtp = require_env(["HIWORKS_SMTP_HOST", "HIWORKS_SMTP_PORT",
                        "HIWORKS_SMTP_USER", "HIWORKS_SMTP_PASSWORD"])
    fb_path = os.environ.get("OLIVE_FB_PATH", "/olive_report/")

    try:
        token = fb_login(fb["OLIVE_FB_URL"], fb["OLIVE_FB_USER"], fb["OLIVE_FB_PASSWORD"])
    except Exception as e:
        print(f"ERROR: 파일서버 로그인 실패: {e}", file=sys.stderr)
        sys.exit(2)

    state = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    sent, failed = [], []
    for name in fb_list_md(fb["OLIVE_FB_URL"], token, fb_path):
        try:
            text = fb_download(fb["OLIVE_FB_URL"], token, fb_path, name)
        except Exception as e:
            failed.append(f"{name}: 다운로드 실패: {e}")
            print(f"ERROR: {name} 다운로드 실패: {e}", file=sys.stderr)
            continue
        digest = hashlib.sha256(text.encode()).hexdigest()
        if state.get(name) == digest:
            continue
        subject = subject_for(name, text)
        if args.dry_run:
            print(f"DRY-RUN: would send '{subject}' ({name}) -> {args.to}")
            continue
        try:
            send_mail(smtp, args.to, subject, text)
            state[name] = digest
            sent.append(f"{subject} ({name})")
            print(f"SENT: {subject} ({name}) -> {args.to}")
        except Exception as e:
            failed.append(f"{name}: {e}")
            print(f"ERROR: {name} 발송 실패: {e}", file=sys.stderr)

    if not args.dry_run and sent:
        STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")

    print(f"RESULT: sent={len(sent)} failed={len(failed)}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
