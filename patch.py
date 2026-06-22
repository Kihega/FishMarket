#!/usr/bin/env python3
"""
PATCH v7 — SmartFish Frontend: Fix Tailwind CSS v4 Setup (Styling Not Applied)
Run from project ROOT, on the `develop` branch.

ROOT CAUSE (verified directly on the live repo, not assumed):
  - tailwindcss@4.3.1 IS installed in package.json
  - @tailwindcss/vite is MISSING (required plugin for v4 + Vite)
  - vite.config.js has NO tailwindcss() plugin entry
  - src/index.css still contains Vite's DEFAULT SCAFFOLD CSS
    (the purple #aa3bff starter theme), never replaced with Tailwind's
    v4 import syntax. This is why every className="bg-blue-700 ..." in
    the app has been doing nothing — Tailwind was never actually running.

Tailwind v4 setup differs from v3:
  - No tailwind.config.js, no postcss.config.js (zero-config, automatic
    content detection — do NOT create these, they're not needed and can
    cause conflicts if mixed with v4's CSS-first approach)
  - Single line: @import "tailwindcss"; in the CSS file
  - Plugin goes in vite.config.js, not postcss

This patch:
  1. Replaces src/index.css entirely with Tailwind's v4 import +
     a small set of custom utility classes (.input, .btn-primary) that
     our components already reference.
  2. Updates vite.config.js to add the @tailwindcss/vite plugin AND
     restores the dev-server API proxy (mentioned in earlier sprints,
     useful for local debugging even though .env points to Render).
  3. Lists the exact npm install command needed (this patch cannot run
     npm itself — Kali has no network restriction issue here, but the
     install must happen on your machine).

Run:
    cd FishMarket
    python3 patch_tailwind_v4.py
"""

import os
import textwrap

ROOT = os.getcwd()
FRONTEND = os.path.join(ROOT, "frontend")

FILES = {}

# ── index.css — REPLACE entirely: remove Vite's default scaffold CSS,
#    add Tailwind v4's import syntax + our custom component classes ────
FILES["src/index.css"] = textwrap.dedent("""\
    @import "tailwindcss";

    /*
      Custom utility classes referenced across our components
      (LoginModal, SellerSignupModal, BuyerSignupModal, etc.)

      Tailwind v4 changed how custom classes work: @layer components +
      @apply (the v3 way) no longer compiles — it throws "Cannot apply
      unknown utility class". The v4-correct approach is the @utility
      directive, which still supports @apply *inside* it.
      See: https://tailwindcss.com/docs/functions-and-directives#utility-directive
    */
    @utility input {
      @apply w-full border border-gray-300 rounded-lg px-4 py-2
             focus:outline-none focus:ring-2 focus:ring-blue-400;
    }

    @utility btn-primary {
      @apply bg-blue-700 text-white font-semibold py-2.5 px-6 rounded-lg
             hover:bg-blue-800 transition disabled:opacity-50;
    }

    body {
      margin: 0;
    }
""")

# ── vite.config.js — add @tailwindcss/vite plugin + dev proxy ──────────
FILES["vite.config.js"] = textwrap.dedent("""\
    import { defineConfig } from 'vite'
    import react from '@vitejs/plugin-react'
    import tailwindcss from '@tailwindcss/vite'

    // https://vite.dev/config/
    export default defineConfig({
      plugins: [react(), tailwindcss()],
      server: {
        port: 5173,
        // Not used while VITE_API_BASE_URL points at Render, but kept
        // here in case a local backend is ever spun up for debugging.
        proxy: {
          '/api': {
            target: 'http://localhost:8000',
            changeOrigin: true,
          },
        },
      },
    })
""")

def main():
    if not os.path.isdir(FRONTEND):
        print(f"❌  frontend/ folder not found at {FRONTEND}")
        print("    Run this script from your project ROOT (e.g. ~/FishMarket).")
        return

    for rel_path, content in FILES.items():
        full_path = os.path.join(FRONTEND, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄  frontend/{rel_path}")

    print()
    print("✅  Tailwind v4 config files written.")
    print("""
⚠️  ONE MANUAL STEP REQUIRED — this patch cannot run npm for you:

    cd frontend
    npm install @tailwindcss/vite

Then verify it worked:

    npm run dev

Open localhost:5173 — the homepage should now show the ocean-blue
navbar, hero section with background gradient, rounded feature cards,
and proper spacing instead of plain black-on-white default browser styling.

If styles STILL don't apply after this:
  1. Hard-stop the dev server (Ctrl+C) and restart it — Vite config
     changes require a full restart, not just hot-reload.
  2. Clear Vite's cache: rm -rf node_modules/.vite

NEXT STEPS
──────────
  1. cd frontend && npm install @tailwindcss/vite
  2. npm run dev   — confirm styling now appears
  3. npm run build — confirm production build still succeeds
  4. Commit on develop:
       git add frontend/src/index.css
       git add frontend/vite.config.js
       git add frontend/package.json frontend/package-lock.json
       git commit -m "Fix: wire up Tailwind v4 (@tailwindcss/vite plugin + CSS import)"
       git push origin develop
""")

if __name__ == "__main__":
    main()
