#!/usr/bin/env python3
"""
fix_aiven_env.py
─────────────────
Run this from inside backend/ on your Kali machine.

What it does:
  1. Updates .env.example with the correct DATABASE_URL + MYSQL_ATTR_SSL_CA
     hybrid format (placeholders only — safe to commit).
  2. Prompts you to paste your REAL Aiven Service URI, strips the
     "?ssl-mode=REQUIRED" suffix automatically, and writes a real .env
     file (NOT committed — already covered by .gitignore).
  3. Verifies aiven-ca.pem exists at docker/aiven-ca.pem and warns if missing.

Usage:
    cd backend
    python3 fix_aiven_env.py
"""

import os
import re
import sys

BACKEND_DIR = os.getcwd()
ENV_EXAMPLE = os.path.join(BACKEND_DIR, ".env.example")
ENV_REAL = os.path.join(BACKEND_DIR, ".env")
CERT_PATH = os.path.join(BACKEND_DIR, "docker", "aiven-ca.pem")
CERT_PATH_IN_CONTAINER = "/var/www/docker/aiven-ca.pem"


ENV_EXAMPLE_CONTENT = """\
APP_NAME=SmartFish
APP_ENV=production
APP_KEY=
APP_DEBUG=false
APP_URL=https://your-app.onrender.com

# ── Aiven MySQL (production only — requires SSL) ─────────────────────────
# Paste Aiven's "Service URI" here, but STRIP the "?ssl-mode=REQUIRED" suffix —
# SSL is handled below via MYSQL_ATTR_SSL_CA instead, since a URL can't carry
# a certificate file path.
#
# Aiven gives you:   mysql://avnadmin:PASS@HOST:PORT/defaultdb?ssl-mode=REQUIRED
# Put this instead:  mysql://avnadmin:PASS@HOST:PORT/defaultdb
DATABASE_URL=mysql://avnadmin:your-password@your-service.aivencloud.com:12691/defaultdb

# Path to the CA cert downloaded from Aiven Console → Overview → CA Certificate.
# Must be committed to the repo at backend/docker/aiven-ca.pem — the Dockerfile's
# "COPY . ." picks it up automatically at build time.
MYSQL_ATTR_SSL_CA={cert_path}

QUEUE_CONNECTION=sync
SESSION_DRIVER=cookie
CACHE_STORE=database

# ── CORS / Sanctum ────────────────────────────────────────────────────────
FRONTEND_URL=https://your-app.vercel.app
SANCTUM_STATEFUL_DOMAINS=your-app.vercel.app,localhost:5173

# ── Cloudinary (fish & logo images) ───────────────────────────────────────
CLOUDINARY_URL=cloudinary://key:secret@cloud_name

LOG_CHANNEL=stderr
LOG_LEVEL=error
""".format(cert_path=CERT_PATH_IN_CONTAINER)


def strip_ssl_mode(uri: str) -> str:
    """Remove ?ssl-mode=... (or &ssl-mode=...) from an Aiven service URI."""
    uri = re.sub(r"[?&]ssl-mode=[^&]*", "", uri)
    # Clean up a dangling "?" if ssl-mode was the only param
    uri = re.sub(r"\?$", "", uri)
    return uri.strip()


def write_env_example():
    with open(ENV_EXAMPLE, "w", encoding="utf-8") as f:
        f.write(ENV_EXAMPLE_CONTENT)
    print(f"✅  Updated {ENV_EXAMPLE}")


def check_cert():
    if os.path.exists(CERT_PATH):
        print(f"✅  Found cert at {CERT_PATH}")
    else:
        print(f"⚠️   Cert NOT found at {CERT_PATH}")
        print(f"     Save your downloaded Aiven CA cert there before deploying.")


def build_real_env():
    print("\n── Paste your real Aiven Service URI ──────────────────────────")
    print("   (looks like: mysql://avnadmin:PASS@host:port/defaultdb?ssl-mode=REQUIRED)")
    raw_uri = input("   URI: ").strip()

    if not raw_uri:
        print("⚠️   No URI entered — skipping .env creation. Run again when ready.")
        return

    clean_uri = strip_ssl_mode(raw_uri)

    if clean_uri != raw_uri:
        print(f"\n   Stripped ssl-mode param:")
        print(f"   Before: {raw_uri}")
        print(f"   After:  {clean_uri}")
    else:
        print("\n   No ssl-mode param found — using URI as-is.")

    frontend_url = input("\n   Your Vercel frontend URL (or press Enter to skip for now): ").strip()
    frontend_url = frontend_url or "https://your-app.vercel.app"

    sanctum_domain = frontend_url.replace("https://", "").replace("http://", "")

    content = f"""\
APP_NAME=SmartFish
APP_ENV=production
APP_KEY=
APP_DEBUG=false
APP_URL=https://your-app.onrender.com

# ── Aiven MySQL ────────────────────────────────────────────────────────────
DATABASE_URL={clean_uri}
MYSQL_ATTR_SSL_CA={CERT_PATH_IN_CONTAINER}

QUEUE_CONNECTION=sync
SESSION_DRIVER=cookie
CACHE_STORE=database

# ── CORS / Sanctum ────────────────────────────────────────────────────────
FRONTEND_URL={frontend_url}
SANCTUM_STATEFUL_DOMAINS={sanctum_domain},localhost:5173

# ── Cloudinary (fish & logo images) ───────────────────────────────────────
CLOUDINARY_URL=cloudinary://key:secret@cloud_name

LOG_CHANNEL=stderr
LOG_LEVEL=error
"""

    if os.path.exists(ENV_REAL):
        confirm = input(f"\n⚠️   {ENV_REAL} already exists. Overwrite? [y/N]: ").strip().lower()
        if confirm != "y":
            print("   Skipped — existing .env left untouched.")
            return

    with open(ENV_REAL, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅  Wrote real credentials to {ENV_REAL}")
    print("   (this file is gitignored — double check with: git check-ignore .env)")


def main():
    print("=" * 60)
    print("SmartFish — Aiven .env fixer")
    print("=" * 60)

    write_env_example()
    check_cert()
    build_real_env()

    print("\nDone. Next: copy the same DATABASE_URL and MYSQL_ATTR_SSL_CA")
    print("values into Render → your service → Environment tab.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(1)
