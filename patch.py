#!/usr/bin/env python3
"""
PATCH v2 – Fish Market / SmartFish
Updates: project_sprints.txt + project structure files
Context: Images reveal true system design (SmartFish branding, Seller platforms,
         Delivery agencies, Subscription billing, Fish stock categories)

DEV ENV REALITY (Kali rootless, no MySQL / Docker / PHP locally):
  - Frontend ONLY runs locally (Vite dev server)
  - Backend  → pushed to GitHub → GitHub Actions runs tests → Render deploys via Docker
  - Database → PlanetScale cloud only (no local DB at all)
  - No local `php artisan serve` / no local Docker
"""

import os, textwrap

BASE = os.path.join(os.path.dirname(__file__), ".")

# ─────────────────────────────────────────────────────────────────────────────
#  UPDATED SPRINT PLAN
# ─────────────────────────────────────────────────────────────────────────────

SPRINTS = """
╔══════════════════════════════════════════════════════════════════════════════╗
║         SMARTFISH – Fish Market Access & Distribution System  v2           ║
║                   AGILE SPRINT PLAN  (7 Days)                              ║
║   Stack : React + Vite (frontend) | Laravel + PHP (backend) | MySQL        ║
║   ─────────────────────────────────────────────────────────────────────    ║
║   DEV ENVIRONMENT  (Kali rootless – no Docker / PHP / MySQL locally)       ║
║     Frontend : npm run dev  →  localhost:5173  (works locally)             ║
║     Backend  : code → push → GitHub Actions tests → Render deploys Docker  ║
║     Database : PlanetScale cloud only (no local DB)                        ║
║   ─────────────────────────────────────────────────────────────────────    ║
║   PROD ENVIRONMENT                                                         ║
║     Frontend : Vercel                                                      ║
║     Backend  : Render  (Docker container)                                  ║
║     Database : PlanetScale  (free Hobby – 5 GB)                            ║
╚══════════════════════════════════════════════════════════════════════════════╝

SYSTEM NAME  : SmartFish
TOTAL TIME   : 7 Days  |  4 Sprints

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SYSTEM ACTORS & CORE USE CASES  (from design notes)
─────────────────────────────────────────────────────

┌─────────┬───────────────────────────────────────────────────────────────────┐
│  ADMIN  │ • Manage users (view, deactivate/delete)                         │
│         │ • View & confirm seller subscription bills (monthly/annual)       │
│         │   – Sellers pay to access the platform; Admin confirms payment    │
│         │ • Manage system performance (CPU, memory, DB health)              │
└─────────┴───────────────────────────────────────────────────────────────────┘

┌─────────┬───────────────────────────────────────────────────────────────────┐
│  SELLER │ • Create fish stock listings                                      │
│ (Fisher)│   – Categorized by fish type/name                                 │
│         │   – Image, stock quantity (kg), price per kg per category         │
│         │   – Stock auto-decreases when buyers place confirmed orders        │
│         │ • Update fish stock (price updates + quantity management)          │
│         │ • Register/manage delivery partnership agencies                    │
│         │   – Seller must register their delivery partners on the platform   │
│         │ • View & confirm orders from buyers (triggered after payment)      │
│         │ • Seller has a public profile page:                                │
│         │   – Brand logo, office/location address, available fish cards      │
└─────────┴───────────────────────────────────────────────────────────────────┘

┌─────────┬───────────────────────────────────────────────────────────────────┐
│  BUYER  │ • Register account (email, phone, password)                       │
│(Trader/ │ • View available seller platforms/agencies (marketplace home)      │
│Customer)│ • Select a seller platform → open seller page → browse fish stock  │
│         │ • Place an order:                                                  │
│         │   – Choose fish, quantity                                          │
│         │   – Choose delivery method & agency (from seller's registered ones)│
│         │   – Pay via mobile money or bank payment                           │
│         │ • View placed orders & statuses:                                   │
│         │   pending → received → confirmed → processed                       │
│         │ • Generate bill (order receipt/invoice)                            │
└─────────┴───────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DEV WORKFLOW  (Kali rootless – how every push works)
──────────────────────────────────────────────────────

  [1] Write code on Kali (VS Code / Neovim)
  [2] git push → GitHub
  [3] GitHub Actions fires:
        • backend-test job  → spins up MySQL service container + PHP
          runs:  composer install → php artisan migrate → php artisan test
        • frontend-build job → npm ci → npm run build
  [4] If both pass → Render auto-deploys backend Docker image
  [5] If frontend push → Vercel auto-deploys
  [6] PlanetScale DB always cloud, shared by Render backend

  Frontend local dev:
        VITE_API_BASE_URL=https://your-app.onrender.com/api
        npm run dev   ← hits the live Render backend directly
        (no need for local PHP at all)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────────────────────┐
│  SPRINT 1  │  Day 1 – Day 2  │  Project Bootstrap & Auth                    │
└──────────────────────────────────────────────────────────────────────────────┘

GOAL: Auth system fully working on Render. Frontend login/register hits
      live Render API. GitHub Actions pipeline is green.

BACKEND (write code → push → test via GitHub Actions → Render deploys)
  [ ] composer create-project laravel/laravel backend
  [ ] Install:  laravel/sanctum
  [ ] Migrations:
        users (id, name, email, password, role[admin|seller|buyer],
               phone, location, brand_logo, office_address, is_active,
               subscription_status[active|pending|inactive], timestamps)
        personal_access_tokens (Sanctum)
  [ ] AuthController: register, login, logout, me
  [ ] Configure CORS:  allow Vercel domain + localhost:5173
  [ ] Configure .env for PlanetScale (SSL cert required):
        DB_CONNECTION=mysql
        MYSQL_ATTR_SSL_CA=/etc/ssl/certs/ca-certificates.crt
  [ ] Push → GitHub Actions must go green (see ci.yml)
  [ ] Render: set env vars, auto-deploy from main branch

FRONTEND (works locally, also deployed to Vercel)
  [ ] npm create vite@latest frontend -- --template react
  [ ] Install: axios, react-router-dom, @tanstack/react-query,
               zustand, tailwindcss, react-hot-toast
  [ ] Set .env:  VITE_API_BASE_URL=https://<app>.onrender.com/api
  [ ] Pages: LoginPage, RegisterPage (email, phone, password, role selector)
  [ ] AuthStore (zustand + persist)
  [ ] Axios client (token interceptor)
  [ ] Protected route (role-aware redirect)
  [ ] Test locally:  npm run dev  → register/login against Render API

GITHUB ACTIONS (ci.yml)
  [ ] backend-test job: PHP 8.2, MySQL service, composer, migrate, test
  [ ] frontend-build job: node 20, npm ci, npm run build
  [ ] Both must pass before Render deploys

SPRINT 1 DELIVERABLE
  ✓ Register as buyer or seller
  ✓ Login → JWT/Sanctum token stored in frontend
  ✓ Role-based redirect: seller → seller dashboard, buyer → marketplace
  ✓ GitHub Actions pipeline green
  ✓ Render backend live, Vercel frontend live

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────────────────────┐
│  SPRINT 2  │  Day 2 – Day 4  │  Seller Platform + Fish Stock Management     │
└──────────────────────────────────────────────────────────────────────────────┘

GOAL: Sellers can build their public profile & manage fish stock.
      Buyers can browse the marketplace and view seller pages.

BACKEND
  [ ] Migrations:
        fish_categories (id, name, description, timestamps)
        fish_stocks (id, seller_id, category_id, fish_name, image,
                     quantity_kg, price_per_kg, status[active|out_of_stock],
                     timestamps)
        delivery_agencies (id, seller_id, agency_name, contact, area_covered,
                           is_active, timestamps)
        seller_profiles (id, user_id, brand_logo, office_address,
                         location_address, bio, timestamps)

  [ ] Controllers:
        SellerProfileController  – update profile (logo, address, bio)
        FishStockController      – CRUD stocks (seller only)
          • store:   create stock with image upload + category
          • index:   list seller's own stocks
          • update:  price update / quantity correction
          • auto-decrease quantity on confirmed orders (via Observer)
        FishCategoryController   – seed default categories (Tilapia, Dagaa,
                                   Perch, Catfish, Sardine, etc.)
        DeliveryAgencyController – seller CRUD for their delivery partners
          • Seller registers agency: name, contact, area_covered
          • Seller can remove/deactivate agency

  [ ] Policies:
        FishStockPolicy  – only owner can edit/delete
        DeliveryAgencyPolicy – only owner seller can manage

  [ ] Public endpoints (no auth):
        GET /api/sellers          – marketplace list of active sellers
        GET /api/sellers/{id}     – seller public profile + stocks
        GET /api/categories       – fish categories

  [ ] Tests (run on GitHub Actions):
        SellerProfileTest
        FishStockTest (CRUD + stock auto-decrease)
        DeliveryAgencyTest

FRONTEND
  [ ] Marketplace home:
        Grid of seller cards:  brand logo, name, location, fish count
        Search/filter by location or fish type
  [ ] Seller public page:
        Hero: brand logo + office address + location
        Fish cards grid: image, name, quantity, price/kg, "Order" button
        Delivery agencies listed
  [ ] Seller Dashboard (authenticated):
        My Fish Stocks table (add / edit / delete)
        Add Stock form: category selector, fish name, image, qty, price
        My Delivery Agencies panel (add / remove)
        Profile editor: logo upload, address
  [ ] Image upload component (multipart form)

SPRINT 2 DELIVERABLE
  ✓ Seller has a public-facing profile page (like a shop page)
  ✓ Seller manages fish stocks with categories
  ✓ Buyer sees marketplace with seller cards + can open seller page
  ✓ Delivery agencies registered by seller are visible on their page

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────────────────────┐
│  SPRINT 3  │  Day 4 – Day 6  │  Orders, Payments & Buyer Flow              │
└──────────────────────────────────────────────────────────────────────────────┘

GOAL: End-to-end order flow: buyer selects fish → chooses delivery →
      pays → seller confirms → stock decreases → buyer gets bill.

BACKEND
  [ ] Migrations:
        orders (id, buyer_id, seller_id, status[pending|received|confirmed|
                processed|cancelled], payment_method[mobile|bank],
                payment_status[unpaid|paid], total_amount, timestamps)
        order_items (id, order_id, stock_id, fish_name, quantity_kg,
                     price_per_kg, subtotal)
        order_delivery (id, order_id, agency_id, delivery_method,
                        delivery_status, timestamps)
        bills (id, order_id, buyer_id, bill_number, issued_at, pdf_path)
        subscriptions (id, seller_id, plan[monthly|annual], amount,
                       status[pending|active|expired], paid_at, timestamps)

  [ ] Controllers:
        OrderController:
          • POST /api/orders  – buyer places order:
              - validate stock quantity available
              - create order + order_items
              - link delivery agency chosen by buyer
              - set status = pending
          • GET /api/orders   – buyer sees own orders with status timeline
          • PUT /api/orders/{id}/status  – seller confirms/processes

        PaymentController:
          • POST /api/orders/{id}/pay  – record payment method (mobile/bank)
              - sets payment_status = paid
              - triggers notification to seller

        BillController:
          • GET  /api/orders/{id}/bill  – generate bill (PDF or JSON invoice)
              - bill_number, buyer info, item list, total, delivery info

        FishStockObserver:
          • on order confirmed → decrease stock quantity_kg automatically

        SubscriptionController (Admin):
          • GET  /api/admin/subscriptions  – list seller subscription bills
          • PUT  /api/admin/subscriptions/{id}/confirm  – admin confirms payment

  [ ] Tests (GitHub Actions):
        OrderFlowTest  (place → pay → confirm → stock decreases)
        BillTest       (bill generated correctly)
        SubscriptionTest

FRONTEND
  [ ] Order placement flow (multi-step):
        Step 1: Review fish items + quantities from seller page
        Step 2: Choose delivery agency + method (from seller's list)
        Step 3: Choose payment method (mobile money | bank transfer)
        Step 4: Confirm → order submitted (status = pending)
  [ ] Buyer Dashboard:
        My Orders list with status badges:
          🟡 Pending  →  🔵 Received  →  🟢 Confirmed  →  ✅ Processed
        View Bill button per order → shows invoice modal
  [ ] Bill/Invoice modal:
        Order #, date, buyer info, items table, delivery info, total
        Print / Download option
  [ ] Seller Dashboard (orders tab):
        Incoming orders list
        Confirm order button (only after payment_status = paid)
        Order detail panel
  [ ] Admin Dashboard:
        Subscription bills table (seller name, plan, amount, status)
        Confirm payment button

SPRINT 3 DELIVERABLE
  ✓ Buyer can place a multi-item order with delivery choice
  ✓ Buyer pays (mobile/bank recorded)
  ✓ Seller sees paid orders and confirms
  ✓ Fish stock auto-decreases after confirmation
  ✓ Buyer can view bill/invoice
  ✓ Admin can see and confirm seller subscription bills

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌──────────────────────────────────────────────────────────────────────────────┐
│  SPRINT 4  │  Day 6 – Day 7  │  Polish, Tests & Final Deployment           │
└──────────────────────────────────────────────────────────────────────────────┘

GOAL: All tests passing on CI, system polished, production fully stable.

TESTING (all backend tests run ONLY on GitHub Actions, not locally)
  [ ] AuthTest           – register, login, invalid credentials, role check
  [ ] FishStockTest      – CRUD, category assignment, auto-decrease
  [ ] DeliveryAgencyTest – seller CRUD, buyer sees only seller's agencies
  [ ] OrderFlowTest      – full lifecycle: place → pay → confirm → processed
  [ ] BillTest           – bill generation, correct totals
  [ ] SubscriptionTest   – admin confirms seller bill
  [ ] PolicyTest         – unauthorized actions blocked (403s)

FRONTEND QA (done locally + on Vercel preview)
  [ ] Auth flow all roles
  [ ] Seller: create stock, upload image, add agency, confirm order
  [ ] Buyer: browse market, open seller page, place order, view bill
  [ ] Admin: view users, confirm subscription
  [ ] Mobile responsive (375px, 768px)
  [ ] Cross-browser: Chrome, Firefox

POLISH
  [ ] Loading skeletons on marketplace + seller page
  [ ] Empty states (no stocks, no orders)
  [ ] Error boundaries
  [ ] 404 page
  [ ] Toast notifications for all key actions
  [ ] Order status timeline component (visual stepper)
  [ ] Seller subscription banner (warns if subscription inactive)

PRODUCTION CHECKLIST
  [ ] PlanetScale: confirm DB schema pushed, indexes on foreign keys
  [ ] Render:
        - APP_ENV=production, APP_DEBUG=false
        - DB_* from PlanetScale connection string
        - FRONTEND_URL=https://<your-vercel-app>.vercel.app
        - php artisan migrate --force (Render start command)
        - UptimeRobot ping every 10 min (prevents free tier sleep)
  [ ] Vercel:
        - VITE_API_BASE_URL=https://<your-render-app>.onrender.com/api
        - Production domain confirmed

SPRINT 4 DELIVERABLE
  ✓ GitHub Actions 100% green (all backend tests pass in CI)
  ✓ Vercel frontend fully functional
  ✓ Render backend stable with Docker
  ✓ PlanetScale DB connected and seeded
  ✓ Full system working end-to-end in production

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DAY-BY-DAY SCHEDULE
────────────────────
  Day 1  │ Sprint 1 – Laravel init, migrations, auth API, CI pipeline setup
  Day 2  │ Sprint 1 done + Sprint 2 start – Seller profile, fish stock API
  Day 3  │ Sprint 2 – Fish categories, delivery agencies, marketplace API
  Day 4  │ Sprint 2 done + Sprint 3 start – Order model, order placement API
  Day 5  │ Sprint 3 – Payment recording, bill generation, seller confirms
  Day 6  │ Sprint 3 done + Sprint 4 start – All tests, admin subscription
  Day 7  │ Sprint 4 – Polish, deploy, final QA on production URLs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ENVIRONMENT SUMMARY
────────────────────
  Tool            Local (Kali)         Production / Cloud
  ─────────────── ──────────────────── ──────────────────────────────────
  Frontend        npm run dev ✓         Vercel (auto-deploy from GitHub)
  Backend         ✗ (no PHP locally)   Render + Docker (auto on push)
  Database        ✗ (no MySQL)          PlanetScale (cloud MySQL)
  Backend tests   ✗ (no PHP locally)   GitHub Actions (MySQL service pod)
  Frontend tests  npm run build ✓       Vercel preview deploy
  ─────────────── ──────────────────── ──────────────────────────────────
  Git flow: write code → push → CI → Render/Vercel auto-deploys

FREE SERVICES
─────────────
  PlanetScale : https://planetscale.com  – 5 GB, free Hobby plan ← RECOMMENDED
  Render      : https://render.com       – free web service (sleeps 15 min idle)
  Vercel      : https://vercel.com       – free hobby, unlimited deploys
  UptimeRobot : https://uptimerobot.com  – free ping to keep Render awake
  Cloudinary  : https://cloudinary.com  – free 25 credits for fish images
"""

# ─────────────────────────────────────────────────────────────────────────────
#  UPDATED / NEW FILES
# ─────────────────────────────────────────────────────────────────────────────

PATCH_FILES = {

# ── CI/CD – updated to match real dev workflow ────────────────────────────
".github/workflows/ci.yml": textwrap.dedent("""\
    name: SmartFish CI

    on:
      push:
        branches: [main, develop]
      pull_request:
        branches: [main]

    jobs:
      # ── Backend tests (run in cloud – Kali has no PHP/MySQL) ─────────────
      backend-test:
        name: Backend – PHPUnit on GitHub Actions
        runs-on: ubuntu-latest

        services:
          mysql:
            image: mysql:8.0
            env:
              MYSQL_ROOT_PASSWORD: secret
              MYSQL_DATABASE: smartfish_test
            ports: ['3306:3306']
            options: >-
              --health-cmd="mysqladmin ping -h 127.0.0.1"
              --health-interval=10s
              --health-timeout=5s
              --health-retries=5

        steps:
          - uses: actions/checkout@v4

          - name: Setup PHP 8.2
            uses: shivammathur/setup-php@v2
            with:
              php-version: '8.2'
              extensions: pdo, pdo_mysql, gd, zip
              coverage: none

          - name: Install Composer dependencies
            working-directory: backend
            run: composer install --no-interaction --prefer-dist --optimize-autoloader

          - name: Copy env + generate key
            working-directory: backend
            run: |
              cp .env.testing .env
              php artisan key:generate

          - name: Run migrations
            working-directory: backend
            env:
              DB_HOST: 127.0.0.1
              DB_PORT: 3306
              DB_DATABASE: smartfish_test
              DB_USERNAME: root
              DB_PASSWORD: secret
            run: php artisan migrate --force

          - name: Run PHPUnit tests
            working-directory: backend
            env:
              DB_HOST: 127.0.0.1
              DB_PORT: 3306
              DB_DATABASE: smartfish_test
              DB_USERNAME: root
              DB_PASSWORD: secret
            run: php artisan test --parallel

      # ── Frontend build (can also run locally) ────────────────────────────
      frontend-build:
        name: Frontend – Vite Build
        runs-on: ubuntu-latest

        steps:
          - uses: actions/checkout@v4

          - uses: actions/setup-node@v4
            with:
              node-version: '20'
              cache: 'npm'
              cache-dependency-path: frontend/package-lock.json

          - name: Install dependencies
            working-directory: frontend
            run: npm ci

          - name: Build
            working-directory: frontend
            env:
              VITE_API_BASE_URL: ${{ secrets.VITE_API_BASE_URL }}
            run: npm run build

      # ── Docker build check (prod image) ──────────────────────────────────
      docker-build-check:
        name: Backend – Docker image builds
        runs-on: ubuntu-latest
        needs: backend-test

        steps:
          - uses: actions/checkout@v4
          - name: Build Docker image
            run: docker build -t smartfish-backend ./backend
"""),

# ── Backend .env.testing (used by GitHub Actions only) ───────────────────
"backend/.env.testing": textwrap.dedent("""\
    APP_NAME=SmartFish
    APP_ENV=testing
    APP_KEY=
    APP_DEBUG=true
    APP_URL=http://localhost

    DB_CONNECTION=mysql
    DB_HOST=127.0.0.1
    DB_PORT=3306
    DB_DATABASE=smartfish_test
    DB_USERNAME=root
    DB_PASSWORD=secret

    QUEUE_CONNECTION=sync
    SESSION_DRIVER=array
    CACHE_DRIVER=array

    # No SSL for test MySQL (GitHub Actions service)
    # Production PlanetScale uses SSL – set in .env on Render
"""),

# ── Backend .env.example (for Render prod) ───────────────────────────────
"backend/.env.example": textwrap.dedent("""\
    APP_NAME=SmartFish
    APP_ENV=production
    APP_KEY=
    APP_DEBUG=false
    APP_URL=https://your-app.onrender.com

    # ── PlanetScale MySQL (production only) ───────────────────────────────
    DB_CONNECTION=mysql
    DB_HOST=<planetscale-host>.connect.psdb.cloud
    DB_PORT=3306
    DB_DATABASE=smartfish
    DB_USERNAME=<planetscale-user>
    DB_PASSWORD=<planetscale-password>
    MYSQL_ATTR_SSL_CA=/etc/ssl/certs/ca-certificates.crt

    QUEUE_CONNECTION=sync
    SESSION_DRIVER=cookie

    # ── CORS ──────────────────────────────────────────────────────────────
    FRONTEND_URL=https://your-app.vercel.app
    SANCTUM_STATEFUL_DOMAINS=your-app.vercel.app,localhost:5173

    # ── Cloudinary (fish images) ──────────────────────────────────────────
    CLOUDINARY_URL=cloudinary://key:secret@cloud_name
"""),

# ── Frontend .env.example ─────────────────────────────────────────────────
"frontend/.env.example": textwrap.dedent("""\
    # Always point to Render backend (no local backend on Kali)
    VITE_API_BASE_URL=https://your-smartfish-api.onrender.com/api

    # Uncomment when testing against a specific Render preview
    # VITE_API_BASE_URL=https://smartfish-api-staging.onrender.com/api
"""),

# ── Updated migrations ────────────────────────────────────────────────────
"backend/database/migrations/2024_01_01_000001_create_users_table.php": textwrap.dedent("""\
    <?php
    use Illuminate\\Database\\Migrations\\Migration;
    use Illuminate\\Database\\Schema\\Blueprint;
    use Illuminate\\Support\\Facades\\Schema;

    return new class extends Migration {
        public function up(): void {
            Schema::create('users', function (Blueprint $table) {
                $table->id();
                $table->string('name');
                $table->string('email')->unique();
                $table->string('password');
                $table->enum('role', ['admin', 'seller', 'buyer'])->default('buyer');
                $table->string('phone')->nullable();
                $table->string('location')->nullable();
                $table->boolean('is_active')->default(true);
                // Seller-specific fields
                $table->string('brand_logo')->nullable();
                $table->string('office_address')->nullable();
                $table->string('location_address')->nullable();
                $table->string('bio')->nullable();
                $table->enum('subscription_status', ['active','pending','inactive'])
                      ->default('inactive');
                $table->timestamps();
            });
        }
        public function down(): void { Schema::dropIfExists('users'); }
    };
"""),

"backend/database/migrations/2024_01_02_000001_create_fish_categories_table.php": textwrap.dedent("""\
    <?php
    use Illuminate\\Database\\Migrations\\Migration;
    use Illuminate\\Database\\Schema\\Blueprint;
    use Illuminate\\Support\\Facades\\Schema;

    return new class extends Migration {
        public function up(): void {
            Schema::create('fish_categories', function (Blueprint $table) {
                $table->id();
                $table->string('name')->unique();   // Tilapia, Dagaa, Perch …
                $table->string('description')->nullable();
                $table->timestamps();
            });
        }
        public function down(): void { Schema::dropIfExists('fish_categories'); }
    };
"""),

"backend/database/migrations/2024_01_02_000002_create_fish_stocks_table.php": textwrap.dedent("""\
    <?php
    use Illuminate\\Database\\Migrations\\Migration;
    use Illuminate\\Database\\Schema\\Blueprint;
    use Illuminate\\Support\\Facades\\Schema;

    return new class extends Migration {
        public function up(): void {
            Schema::create('fish_stocks', function (Blueprint $table) {
                $table->id();
                $table->foreignId('seller_id')->constrained('users')->cascadeOnDelete();
                $table->foreignId('category_id')->constrained('fish_categories');
                $table->string('fish_name');
                $table->string('image')->nullable();
                $table->decimal('quantity_kg', 10, 2)->default(0);
                $table->decimal('price_per_kg', 10, 2);
                $table->enum('status', ['active', 'out_of_stock'])->default('active');
                $table->timestamps();
            });
        }
        public function down(): void { Schema::dropIfExists('fish_stocks'); }
    };
"""),

"backend/database/migrations/2024_01_02_000003_create_delivery_agencies_table.php": textwrap.dedent("""\
    <?php
    use Illuminate\\Database\\Migrations\\Migration;
    use Illuminate\\Database\\Schema\\Blueprint;
    use Illuminate\\Support\\Facades\\Schema;

    return new class extends Migration {
        public function up(): void {
            Schema::create('delivery_agencies', function (Blueprint $table) {
                $table->id();
                $table->foreignId('seller_id')->constrained('users')->cascadeOnDelete();
                $table->string('agency_name');
                $table->string('contact')->nullable();
                $table->string('area_covered')->nullable();
                $table->boolean('is_active')->default(true);
                $table->timestamps();
            });
        }
        public function down(): void { Schema::dropIfExists('delivery_agencies'); }
    };
"""),

"backend/database/migrations/2024_01_03_000001_create_orders_table.php": textwrap.dedent("""\
    <?php
    use Illuminate\\Database\\Migrations\\Migration;
    use Illuminate\\Database\\Schema\\Blueprint;
    use Illuminate\\Support\\Facades\\Schema;

    return new class extends Migration {
        public function up(): void {
            Schema::create('orders', function (Blueprint $table) {
                $table->id();
                $table->foreignId('buyer_id')->constrained('users')->cascadeOnDelete();
                $table->foreignId('seller_id')->constrained('users')->cascadeOnDelete();
                $table->enum('status', ['pending','received','confirmed','processed','cancelled'])
                      ->default('pending');
                $table->enum('payment_method', ['mobile','bank'])->nullable();
                $table->enum('payment_status', ['unpaid','paid'])->default('unpaid');
                $table->decimal('total_amount', 12, 2)->default(0);
                $table->timestamps();
            });

            Schema::create('order_items', function (Blueprint $table) {
                $table->id();
                $table->foreignId('order_id')->constrained()->cascadeOnDelete();
                $table->foreignId('stock_id')->constrained('fish_stocks');
                $table->string('fish_name');
                $table->decimal('quantity_kg', 10, 2);
                $table->decimal('price_per_kg', 10, 2);
                $table->decimal('subtotal', 12, 2);
            });

            Schema::create('order_deliveries', function (Blueprint $table) {
                $table->id();
                $table->foreignId('order_id')->constrained()->cascadeOnDelete();
                $table->foreignId('agency_id')->constrained('delivery_agencies');
                $table->string('delivery_method')->nullable();
                $table->enum('delivery_status', ['pending','dispatched','delivered'])
                      ->default('pending');
                $table->timestamps();
            });
        }
        public function down(): void {
            Schema::dropIfExists('order_deliveries');
            Schema::dropIfExists('order_items');
            Schema::dropIfExists('orders');
        }
    };
"""),

"backend/database/migrations/2024_01_03_000002_create_bills_and_subscriptions_table.php": textwrap.dedent("""\
    <?php
    use Illuminate\\Database\\Migrations\\Migration;
    use Illuminate\\Database\\Schema\\Blueprint;
    use Illuminate\\Support\\Facades\\Schema;

    return new class extends Migration {
        public function up(): void {
            Schema::create('bills', function (Blueprint $table) {
                $table->id();
                $table->foreignId('order_id')->constrained()->cascadeOnDelete();
                $table->foreignId('buyer_id')->constrained('users');
                $table->string('bill_number')->unique();
                $table->timestamp('issued_at')->useCurrent();
                $table->timestamps();
            });

            Schema::create('subscriptions', function (Blueprint $table) {
                $table->id();
                $table->foreignId('seller_id')->constrained('users')->cascadeOnDelete();
                $table->enum('plan', ['monthly', 'annual']);
                $table->decimal('amount', 10, 2);
                $table->enum('status', ['pending', 'active', 'expired'])->default('pending');
                $table->timestamp('paid_at')->nullable();
                $table->timestamps();
            });
        }
        public function down(): void {
            Schema::dropIfExists('subscriptions');
            Schema::dropIfExists('bills');
        }
    };
"""),

# ── New models ────────────────────────────────────────────────────────────
"backend/app/Models/FishStock.php": textwrap.dedent("""\
    <?php
    namespace App\\Models;

    use Illuminate\\Database\\Eloquent\\Model;

    class FishStock extends Model
    {
        protected $fillable = [
            'seller_id', 'category_id', 'fish_name',
            'image', 'quantity_kg', 'price_per_kg', 'status',
        ];

        public function seller()   { return $this->belongsTo(User::class, 'seller_id'); }
        public function category() { return $this->belongsTo(FishCategory::class); }
        public function orderItems(){ return $this->hasMany(OrderItem::class, 'stock_id'); }

        public function decreaseStock(float $qty): void
        {
            $this->decrement('quantity_kg', $qty);
            if ($this->quantity_kg <= 0) {
                $this->update(['status' => 'out_of_stock']);
            }
        }
    }
"""),

"backend/app/Models/FishCategory.php": textwrap.dedent("""\
    <?php
    namespace App\\Models;

    use Illuminate\\Database\\Eloquent\\Model;

    class FishCategory extends Model
    {
        protected $fillable = ['name', 'description'];
        public function stocks() { return $this->hasMany(FishStock::class, 'category_id'); }
    }
"""),

"backend/app/Models/DeliveryAgency.php": textwrap.dedent("""\
    <?php
    namespace App\\Models;

    use Illuminate\\Database\\Eloquent\\Model;

    class DeliveryAgency extends Model
    {
        protected $fillable = ['seller_id', 'agency_name', 'contact', 'area_covered', 'is_active'];
        public function seller() { return $this->belongsTo(User::class, 'seller_id'); }
    }
"""),

"backend/app/Models/Order.php": textwrap.dedent("""\
    <?php
    namespace App\\Models;

    use Illuminate\\Database\\Eloquent\\Model;

    class Order extends Model
    {
        protected $fillable = [
            'buyer_id', 'seller_id', 'status',
            'payment_method', 'payment_status', 'total_amount',
        ];

        public function buyer()    { return $this->belongsTo(User::class, 'buyer_id'); }
        public function seller()   { return $this->belongsTo(User::class, 'seller_id'); }
        public function items()    { return $this->hasMany(OrderItem::class); }
        public function delivery() { return $this->hasOne(OrderDelivery::class); }
        public function bill()     { return $this->hasOne(Bill::class); }
    }
"""),

"backend/app/Models/OrderItem.php": textwrap.dedent("""\
    <?php
    namespace App\\Models;

    use Illuminate\\Database\\Eloquent\\Model;

    class OrderItem extends Model
    {
        public $timestamps = false;
        protected $fillable = [
            'order_id', 'stock_id', 'fish_name', 'quantity_kg', 'price_per_kg', 'subtotal',
        ];
        public function stock() { return $this->belongsTo(FishStock::class); }
    }
"""),

"backend/app/Models/Bill.php": textwrap.dedent("""\
    <?php
    namespace App\\Models;

    use Illuminate\\Database\\Eloquent\\Model;

    class Bill extends Model
    {
        protected $fillable = ['order_id', 'buyer_id', 'bill_number', 'issued_at'];

        public function order() { return $this->belongsTo(Order::class); }
        public function buyer() { return $this->belongsTo(User::class, 'buyer_id'); }
    }
"""),

"backend/app/Models/Subscription.php": textwrap.dedent("""\
    <?php
    namespace App\\Models;

    use Illuminate\\Database\\Eloquent\\Model;

    class Subscription extends Model
    {
        protected $fillable = ['seller_id', 'plan', 'amount', 'status', 'paid_at'];
        public function seller() { return $this->belongsTo(User::class, 'seller_id'); }
    }
"""),

# ── Updated User model ────────────────────────────────────────────────────
"backend/app/Models/User.php": textwrap.dedent("""\
    <?php
    namespace App\\Models;

    use Illuminate\\Foundation\\Auth\\User as Authenticatable;
    use Laravel\\Sanctum\\HasApiTokens;

    class User extends Authenticatable
    {
        use HasApiTokens;

        protected $fillable = [
            'name', 'email', 'password', 'role', 'phone', 'location',
            'brand_logo', 'office_address', 'location_address', 'bio',
            'is_active', 'subscription_status',
        ];

        protected $hidden = ['password', 'remember_token'];

        public function fishStocks()       { return $this->hasMany(FishStock::class, 'seller_id'); }
        public function deliveryAgencies() { return $this->hasMany(DeliveryAgency::class, 'seller_id'); }
        public function ordersAsBuyer()    { return $this->hasMany(Order::class, 'buyer_id'); }
        public function ordersAsSeller()   { return $this->hasMany(Order::class, 'seller_id'); }
        public function subscriptions()    { return $this->hasMany(Subscription::class, 'seller_id'); }
    }
"""),

# ── Controllers ───────────────────────────────────────────────────────────
"backend/app/Http/Controllers/API/FishStockController.php": textwrap.dedent("""\
    <?php
    namespace App\\Http\\Controllers\\API;

    use App\\Http\\Controllers\\Controller;
    use App\\Models\\FishStock;
    use Illuminate\\Http\\Request;

    class FishStockController extends Controller
    {
        // Public: list stocks for a seller
        public function index(Request $request)
        {
            $sellerId = $request->seller_id;
            $query = FishStock::with('category')
                ->where('status', 'active')
                ->when($sellerId, fn($q) => $q->where('seller_id', $sellerId))
                ->when($request->category_id, fn($q) => $q->where('category_id', $request->category_id));

            return response()->json($query->latest()->paginate(20));
        }

        // Seller: create stock
        public function store(Request $request)
        {
            $this->ensureSeller($request);

            $data = $request->validate([
                'category_id'  => 'required|exists:fish_categories,id',
                'fish_name'    => 'required|string',
                'quantity_kg'  => 'required|numeric|min:0.1',
                'price_per_kg' => 'required|numeric|min:0',
                'image'        => 'nullable|image|max:3072',
            ]);

            if ($request->hasFile('image')) {
                $data['image'] = $request->file('image')->store('stocks', 'public');
            }

            $stock = $request->user()->fishStocks()->create($data);
            return response()->json($stock->load('category'), 201);
        }

        // Seller: update stock
        public function update(Request $request, FishStock $fishStock)
        {
            abort_unless($fishStock->seller_id === $request->user()->id, 403);

            $fishStock->update($request->validate([
                'fish_name'    => 'sometimes|string',
                'quantity_kg'  => 'sometimes|numeric|min:0',
                'price_per_kg' => 'sometimes|numeric|min:0',
                'status'       => 'sometimes|in:active,out_of_stock',
            ]));

            return response()->json($fishStock);
        }

        public function destroy(Request $request, FishStock $fishStock)
        {
            abort_unless($fishStock->seller_id === $request->user()->id, 403);
            $fishStock->delete();
            return response()->json(null, 204);
        }

        private function ensureSeller(Request $request): void
        {
            abort_unless($request->user()->role === 'seller', 403, 'Sellers only');
        }
    }
"""),

"backend/app/Http/Controllers/API/OrderController.php": textwrap.dedent("""\
    <?php
    namespace App\\Http\\Controllers\\API;

    use App\\Http\\Controllers\\Controller;
    use App\\Models\\{Order, OrderItem, OrderDelivery, FishStock, Bill};
    use Illuminate\\Http\\Request;
    use Illuminate\\Support\\Str;

    class OrderController extends Controller
    {
        // Buyer places an order
        public function store(Request $request)
        {
            $data = $request->validate([
                'seller_id'       => 'required|exists:users,id',
                'items'           => 'required|array|min:1',
                'items.*.stock_id'     => 'required|exists:fish_stocks,id',
                'items.*.quantity_kg'  => 'required|numeric|min:0.1',
                'payment_method'  => 'required|in:mobile,bank',
                'agency_id'       => 'required|exists:delivery_agencies,id',
                'delivery_method' => 'nullable|string',
            ]);

            $total = 0;
            $orderItems = [];

            foreach ($data['items'] as $item) {
                $stock = FishStock::findOrFail($item['stock_id']);
                abort_if($stock->quantity_kg < $item['quantity_kg'], 422, 'Insufficient stock');
                $subtotal = $stock->price_per_kg * $item['quantity_kg'];
                $total += $subtotal;
                $orderItems[] = [
                    'stock_id'    => $stock->id,
                    'fish_name'   => $stock->fish_name,
                    'quantity_kg' => $item['quantity_kg'],
                    'price_per_kg'=> $stock->price_per_kg,
                    'subtotal'    => $subtotal,
                ];
            }

            $order = Order::create([
                'buyer_id'       => $request->user()->id,
                'seller_id'      => $data['seller_id'],
                'total_amount'   => $total,
                'payment_method' => $data['payment_method'],
                'payment_status' => 'unpaid',
                'status'         => 'pending',
            ]);

            foreach ($orderItems as $item) {
                $order->items()->create($item);
            }

            OrderDelivery::create([
                'order_id'        => $order->id,
                'agency_id'       => $data['agency_id'],
                'delivery_method' => $data['delivery_method'] ?? null,
            ]);

            return response()->json($order->load('items', 'delivery'), 201);
        }

        // Mark payment done → seller can now confirm
        public function pay(Request $request, Order $order)
        {
            abort_unless($order->buyer_id === $request->user()->id, 403);
            $order->update(['payment_status' => 'paid', 'status' => 'received']);
            return response()->json($order);
        }

        // Seller confirms order → stock decreases, bill generated
        public function confirm(Request $request, Order $order)
        {
            abort_unless($order->seller_id === $request->user()->id, 403);
            abort_unless($order->payment_status === 'paid', 422, 'Payment not received yet');

            $order->update(['status' => 'confirmed']);

            // Decrease stock
            foreach ($order->items as $item) {
                $item->stock->decreaseStock($item->quantity_kg);
            }

            // Generate bill
            Bill::create([
                'order_id'    => $order->id,
                'buyer_id'    => $order->buyer_id,
                'bill_number' => 'BILL-' . strtoupper(Str::random(8)),
                'issued_at'   => now(),
            ]);

            return response()->json($order->load('items', 'bill'));
        }

        public function index(Request $request)
        {
            $user = $request->user();
            $orders = $user->role === 'seller'
                ? $user->ordersAsSeller()->with('buyer', 'items', 'delivery', 'bill')
                : $user->ordersAsBuyer()->with('seller', 'items', 'delivery', 'bill');

            return response()->json($orders->latest()->paginate(20));
        }
    }
"""),

"backend/app/Http/Controllers/API/DeliveryAgencyController.php": textwrap.dedent("""\
    <?php
    namespace App\\Http\\Controllers\\API;

    use App\\Http\\Controllers\\Controller;
    use App\\Models\\DeliveryAgency;
    use Illuminate\\Http\\Request;

    class DeliveryAgencyController extends Controller
    {
        // Public: agencies for a seller
        public function index(Request $request)
        {
            $sellerId = $request->seller_id ?? $request->user()?->id;
            return response()->json(
                DeliveryAgency::where('seller_id', $sellerId)
                    ->where('is_active', true)->get()
            );
        }

        public function store(Request $request)
        {
            abort_unless($request->user()->role === 'seller', 403);
            $agency = $request->user()->deliveryAgencies()->create(
                $request->validate([
                    'agency_name'  => 'required|string',
                    'contact'      => 'nullable|string',
                    'area_covered' => 'nullable|string',
                ])
            );
            return response()->json($agency, 201);
        }

        public function destroy(Request $request, DeliveryAgency $deliveryAgency)
        {
            abort_unless($deliveryAgency->seller_id === $request->user()->id, 403);
            $deliveryAgency->update(['is_active' => false]);
            return response()->json(null, 204);
        }
    }
"""),

"backend/app/Http/Controllers/API/SellerController.php": textwrap.dedent("""\
    <?php
    namespace App\\Http\\Controllers\\API;

    use App\\Http\\Controllers\\Controller;
    use App\\Models\\User;
    use Illuminate\\Http\\Request;

    class SellerController extends Controller
    {
        // Public: marketplace list of active sellers
        public function index(Request $request)
        {
            $sellers = User::where('role', 'seller')
                ->where('is_active', true)
                ->where('subscription_status', 'active')
                ->when($request->location, fn($q) => $q->where('location', 'like', "%{$request->location}%"))
                ->withCount('fishStocks')
                ->paginate(20);

            return response()->json($sellers);
        }

        // Public: single seller profile + stocks + agencies
        public function show(User $user)
        {
            abort_unless($user->role === 'seller', 404);
            return response()->json([
                'seller'   => $user,
                'stocks'   => $user->fishStocks()->with('category')->where('status','active')->get(),
                'agencies' => $user->deliveryAgencies()->where('is_active', true)->get(),
            ]);
        }

        // Seller: update own profile
        public function updateProfile(Request $request)
        {
            $user = $request->user();
            $data = $request->validate([
                'brand_logo'       => 'nullable|image|max:2048',
                'office_address'   => 'nullable|string',
                'location_address' => 'nullable|string',
                'bio'              => 'nullable|string',
            ]);

            if ($request->hasFile('brand_logo')) {
                $data['brand_logo'] = $request->file('brand_logo')->store('logos', 'public');
            }

            $user->update($data);
            return response()->json($user);
        }
    }
"""),

"backend/app/Http/Controllers/API/AdminController.php": textwrap.dedent("""\
    <?php
    namespace App\\Http\\Controllers\\API;

    use App\\Http\\Controllers\\Controller;
    use App\\Models\\{User, Subscription};
    use Illuminate\\Http\\Request;

    class AdminController extends Controller
    {
        public function users(Request $request)
        {
            return response()->json(
                User::when($request->role, fn($q) => $q->where('role', $request->role))
                    ->latest()->paginate(30)
            );
        }

        public function toggleUser(User $user)
        {
            $user->update(['is_active' => !$user->is_active]);
            return response()->json($user);
        }

        public function subscriptions()
        {
            return response()->json(
                Subscription::with('seller')->latest()->paginate(30)
            );
        }

        public function confirmSubscription(Subscription $subscription)
        {
            $subscription->update([
                'status'  => 'active',
                'paid_at' => now(),
            ]);
            $subscription->seller->update(['subscription_status' => 'active']);
            return response()->json($subscription);
        }

        public function stats()
        {
            return response()->json([
                'total_users'    => User::count(),
                'active_sellers' => User::where('role','seller')->where('subscription_status','active')->count(),
                'total_buyers'   => User::where('role','buyer')->count(),
                'pending_subs'   => Subscription::where('status','pending')->count(),
            ]);
        }
    }
"""),

# ── Updated API routes ────────────────────────────────────────────────────
"backend/routes/api.php": textwrap.dedent("""\
    <?php
    use Illuminate\\Support\\Facades\\Route;
    use App\\Http\\Controllers\\API\\{
        AuthController,
        SellerController,
        FishStockController,
        DeliveryAgencyController,
        OrderController,
        AdminController
    };

    // ── Public ──────────────────────────────────────────────────────────────
    Route::post('/register', [AuthController::class, 'register']);
    Route::post('/login',    [AuthController::class, 'login']);

    // Marketplace
    Route::get('/sellers',         [SellerController::class, 'index']);
    Route::get('/sellers/{user}',  [SellerController::class, 'show']);
    Route::get('/stocks',          [FishStockController::class, 'index']);
    Route::get('/agencies',        [DeliveryAgencyController::class, 'index']);

    // ── Protected ────────────────────────────────────────────────────────────
    Route::middleware('auth:sanctum')->group(function () {
        Route::post('/logout', [AuthController::class, 'logout']);
        Route::get('/me',      [AuthController::class, 'me']);

        // Seller profile
        Route::put('/seller/profile', [SellerController::class, 'updateProfile']);

        // Fish stocks (seller)
        Route::post('/stocks',           [FishStockController::class, 'store']);
        Route::put('/stocks/{fishStock}', [FishStockController::class, 'update']);
        Route::delete('/stocks/{fishStock}', [FishStockController::class, 'destroy']);

        // Delivery agencies (seller)
        Route::post('/agencies',                     [DeliveryAgencyController::class, 'store']);
        Route::delete('/agencies/{deliveryAgency}',  [DeliveryAgencyController::class, 'destroy']);

        // Orders
        Route::get('/orders',                [OrderController::class, 'index']);
        Route::post('/orders',               [OrderController::class, 'store']);
        Route::post('/orders/{order}/pay',   [OrderController::class, 'pay']);
        Route::post('/orders/{order}/confirm', [OrderController::class, 'confirm']);

        // Admin
        Route::prefix('admin')->middleware('can:admin')->group(function () {
            Route::get('/stats',                              [AdminController::class, 'stats']);
            Route::get('/users',                             [AdminController::class, 'users']);
            Route::put('/users/{user}/toggle',               [AdminController::class, 'toggleUser']);
            Route::get('/subscriptions',                     [AdminController::class, 'subscriptions']);
            Route::put('/subscriptions/{subscription}/confirm', [AdminController::class, 'confirmSubscription']);
        });
    });
"""),

# ── Database seeder for fish categories ──────────────────────────────────
"backend/database/seeders/FishCategorySeeder.php": textwrap.dedent("""\
    <?php
    namespace Database\\Seeders;

    use Illuminate\\Database\\Seeder;
    use Illuminate\\Support\\Facades\\DB;

    class FishCategorySeeder extends Seeder
    {
        public function run(): void
        {
            $categories = [
                'Tilapia', 'Dagaa (Sardine)', 'Nile Perch', 'Catfish',
                'Mackerel', 'Tuna', 'Kingfish', 'Octopus', 'Prawns', 'Crab',
            ];

            foreach ($categories as $name) {
                DB::table('fish_categories')->insertOrIgnore(['name' => $name, 'created_at' => now(), 'updated_at' => now()]);
            }
        }
    }
"""),

# ── Frontend updated pages ────────────────────────────────────────────────
"frontend/src/api/sellers.js": textwrap.dedent("""\
    import client from './client'

    export const getSellers         = (params) => client.get('/sellers', { params })
    export const getSeller          = (id)     => client.get(`/sellers/${id}`)
    export const updateProfile      = (data)   => client.put('/seller/profile', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
"""),

"frontend/src/api/stocks.js": textwrap.dedent("""\
    import client from './client'

    export const getStocks    = (params) => client.get('/stocks', { params })
    export const createStock  = (data)   => client.post('/stocks', data, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    export const updateStock  = (id, data) => client.put(`/stocks/${id}`, data)
    export const deleteStock  = (id)       => client.delete(`/stocks/${id}`)
"""),

"frontend/src/api/orders.js": textwrap.dedent("""\
    import client from './client'

    export const getOrders   = ()       => client.get('/orders')
    export const placeOrder  = (data)   => client.post('/orders', data)
    export const payOrder    = (id)     => client.post(`/orders/${id}/pay`)
    export const confirmOrder= (id)     => client.post(`/orders/${id}/confirm`)
"""),

"frontend/src/pages/market/MarketPage.jsx": textwrap.dedent("""\
    import { useState } from 'react'
    import { useQuery } from '@tanstack/react-query'
    import { getSellers } from '../../api/sellers'
    import SellerCard from '../../components/sellers/SellerCard'

    export default function MarketPage() {
      const [search, setSearch] = useState('')
      const { data, isLoading } = useQuery({
        queryKey: ['sellers', search],
        queryFn: () => getSellers({ location: search }).then(r => r.data),
      })

      return (
        <div className=\"container mx-auto px-4 py-8\">
          <h1 className=\"text-3xl font-bold text-blue-900 mb-2\">SmartFish Marketplace</h1>
          <p className=\"text-gray-500 mb-6\">Browse verified fish sellers and their available stock</p>

          <input
            className=\"input max-w-sm mb-8\"
            placeholder=\"Search by location…\"
            value={search}
            onChange={e => setSearch(e.target.value)}
          />

          {isLoading ? (
            <div className=\"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6\">
              {[...Array(6)].map((_, i) => (
                <div key={i} className=\"h-48 bg-gray-200 animate-pulse rounded-2xl\" />
              ))}
            </div>
          ) : (
            <div className=\"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6\">
              {data?.data?.map(seller => <SellerCard key={seller.id} seller={seller} />)}
            </div>
          )}
        </div>
      )
    }
"""),

"frontend/src/components/sellers/SellerCard.jsx": textwrap.dedent("""\
    import { Link } from 'react-router-dom'

    export default function SellerCard({ seller }) {
      return (
        <div className=\"bg-white rounded-2xl shadow p-5 hover:shadow-md transition flex flex-col gap-3\">
          <div className=\"flex items-center gap-3\">
            {seller.brand_logo
              ? <img src={`/storage/${seller.brand_logo}`} alt={seller.name}
                     className=\"w-14 h-14 rounded-full object-cover border\" />
              : <div className=\"w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-2xl\">🐟</div>
            }
            <div>
              <h3 className=\"font-bold text-blue-900 text-lg\">{seller.name}</h3>
              <p className=\"text-gray-500 text-sm\">📍 {seller.location_address || seller.location}</p>
            </div>
          </div>
          <p className=\"text-gray-600 text-sm\">{seller.office_address}</p>
          <div className=\"flex items-center justify-between mt-auto\">
            <span className=\"text-sm text-blue-600\">{seller.fish_stocks_count} items</span>
            <Link to={`/sellers/${seller.id}`}
              className=\"bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm hover:bg-blue-700\">
              View Shop
            </Link>
          </div>
        </div>
      )
    }
"""),

"frontend/src/pages/market/SellerPage.jsx": textwrap.dedent("""\
    import { useParams } from 'react-router-dom'
    import { useQuery } from '@tanstack/react-query'
    import { getSeller } from '../../api/sellers'
    import { useAuthStore } from '../../store/authStore'
    import OrderModal from '../../components/orders/OrderModal'
    import { useState } from 'react'

    export default function SellerPage() {
      const { id } = useParams()
      const { user } = useAuthStore()
      const [orderItem, setOrderItem] = useState(null)

      const { data, isLoading } = useQuery({
        queryKey: ['seller', id],
        queryFn: () => getSeller(id).then(r => r.data),
      })

      if (isLoading) return <div className=\"p-8\">Loading seller…</div>

      const { seller, stocks, agencies } = data

      return (
        <div className=\"container mx-auto px-4 py-8\">
          {/* Seller Hero */}
          <div className=\"bg-white rounded-2xl shadow p-6 mb-8 flex gap-6 items-center\">
            {seller.brand_logo
              ? <img src={`/storage/${seller.brand_logo}`} className=\"w-24 h-24 rounded-full object-cover border-4 border-blue-200\" />
              : <div className=\"w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center text-4xl\">🐟</div>
            }
            <div>
              <h1 className=\"text-2xl font-bold text-blue-900\">{seller.name}</h1>
              <p className=\"text-gray-500\">🏢 {seller.office_address}</p>
              <p className=\"text-gray-500\">📍 {seller.location_address}</p>
              {seller.bio && <p className=\"text-gray-600 mt-2\">{seller.bio}</p>}
            </div>
          </div>

          {/* Fish Stock Grid */}
          <h2 className=\"text-xl font-bold text-blue-800 mb-4\">Available Fish</h2>
          <div className=\"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-8\">
            {stocks.map(stock => (
              <div key={stock.id} className=\"bg-white rounded-xl shadow p-4\">
                {stock.image && <img src={`/storage/${stock.image}`} className=\"w-full h-36 object-cover rounded-lg mb-3\" />}
                <span className=\"text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full\">{stock.category?.name}</span>
                <h3 className=\"font-semibold text-blue-900 mt-1\">{stock.fish_name}</h3>
                <p className=\"text-gray-600 text-sm\">{stock.quantity_kg} kg available</p>
                <p className=\"text-blue-700 font-bold\">TZS {Number(stock.price_per_kg).toLocaleString()} / kg</p>
                {user && (
                  <button onClick={() => setOrderItem({ stock, seller, agencies })}
                    className=\"mt-3 w-full bg-blue-600 text-white py-1.5 rounded-lg hover:bg-blue-700 text-sm\">
                    Order Now
                  </button>
                )}
              </div>
            ))}
          </div>

          {orderItem && (
            <OrderModal data={orderItem} onClose={() => setOrderItem(null)} />
          )}
        </div>
      )
    }
"""),

"frontend/src/components/orders/OrderModal.jsx": textwrap.dedent("""\
    import { useState } from 'react'
    import { placeOrder, payOrder } from '../../api/orders'
    import toast from 'react-hot-toast'

    export default function OrderModal({ data: { stock, seller, agencies }, onClose }) {
      const [qty, setQty]       = useState(1)
      const [agency, setAgency] = useState('')
      const [method, setMethod] = useState('mobile')
      const [loading, setLoading] = useState(false)

      const total = (qty * stock.price_per_kg).toFixed(2)

      const handleOrder = async () => {
        if (!agency) return toast.error('Choose a delivery agency')
        setLoading(true)
        try {
          const { data: order } = await placeOrder({
            seller_id: seller.id,
            items: [{ stock_id: stock.id, quantity_kg: qty }],
            payment_method: method,
            agency_id: agency,
          })
          await payOrder(order.id)   // mark as paid immediately (demo flow)
          toast.success('Order placed & payment recorded!')
          onClose()
        } catch (e) {
          toast.error(e.response?.data?.message || 'Order failed')
        } finally {
          setLoading(false)
        }
      }

      return (
        <div className=\"fixed inset-0 bg-black/50 flex items-center justify-center z-50\">
          <div className=\"bg-white rounded-2xl p-6 w-full max-w-md shadow-xl\">
            <h2 className=\"text-xl font-bold mb-4\">Place Order – {stock.fish_name}</h2>

            <label className=\"block text-sm mb-1\">Quantity (kg)</label>
            <input type=\"number\" min=\"0.1\" max={stock.quantity_kg} step=\"0.1\"
              value={qty} onChange={e => setQty(Number(e.target.value))}
              className=\"input mb-4\" />

            <label className=\"block text-sm mb-1\">Delivery Agency</label>
            <select value={agency} onChange={e => setAgency(e.target.value)} className=\"input mb-4\">
              <option value=\"\">Select agency…</option>
              {agencies.map(a => <option key={a.id} value={a.id}>{a.agency_name} – {a.area_covered}</option>)}
            </select>

            <label className=\"block text-sm mb-1\">Payment Method</label>
            <div className=\"flex gap-4 mb-6\">
              {['mobile', 'bank'].map(m => (
                <label key={m} className=\"flex items-center gap-2 cursor-pointer\">
                  <input type=\"radio\" value={m} checked={method===m} onChange={() => setMethod(m)} />
                  {m === 'mobile' ? '📱 Mobile Money' : '🏦 Bank Transfer'}
                </label>
              ))}
            </div>

            <div className=\"bg-blue-50 rounded-lg p-3 mb-4\">
              <p className=\"font-semibold text-blue-900\">Total: TZS {Number(total).toLocaleString()}</p>
            </div>

            <div className=\"flex gap-3\">
              <button onClick={onClose} className=\"flex-1 border border-gray-300 rounded-lg py-2\">Cancel</button>
              <button onClick={handleOrder} disabled={loading}
                className=\"flex-1 bg-blue-600 text-white rounded-lg py-2 hover:bg-blue-700 disabled:opacity-50\">
                {loading ? 'Placing…' : 'Confirm Order'}
              </button>
            </div>
          </div>
        </div>
      )
    }
"""),

"frontend/src/pages/dashboard/BuyerDashboard.jsx": textwrap.dedent("""\
    import { useQuery } from '@tanstack/react-query'
    import { getOrders } from '../../api/orders'
    import { Link } from 'react-router-dom'

    const STATUS_STYLE = {
      pending:   'bg-yellow-100 text-yellow-700',
      received:  'bg-blue-100 text-blue-700',
      confirmed: 'bg-green-100 text-green-700',
      processed: 'bg-gray-100 text-gray-700',
      cancelled: 'bg-red-100 text-red-600',
    }

    export default function BuyerDashboard() {
      const { data, isLoading } = useQuery({
        queryKey: ['my-orders'],
        queryFn: () => getOrders().then(r => r.data),
      })

      return (
        <div className=\"container mx-auto px-4 py-8\">
          <h1 className=\"text-2xl font-bold text-blue-900 mb-6\">My Orders</h1>
          <Link to=\"/\" className=\"btn-primary mb-6 inline-block\">Browse Marketplace</Link>

          {isLoading ? <p>Loading orders…</p> : (
            <div className=\"space-y-4\">
              {data?.data?.map(order => (
                <div key={order.id} className=\"bg-white rounded-xl shadow p-5\">
                  <div className=\"flex justify-between items-start\">
                    <div>
                      <p className=\"font-semibold\">Order #{order.id} – {order.seller?.name}</p>
                      <p className=\"text-gray-500 text-sm\">{order.items?.length} item(s) · TZS {Number(order.total_amount).toLocaleString()}</p>
                    </div>
                    <span className={`text-xs px-3 py-1 rounded-full font-medium ${STATUS_STYLE[order.status]}`}>
                      {order.status.toUpperCase()}
                    </span>
                  </div>
                  {order.bill && (
                    <p className=\"text-sm text-blue-600 mt-2\">🧾 Bill #{order.bill.bill_number}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )
    }
"""),

"frontend/src/pages/dashboard/SellerDashboard.jsx": textwrap.dedent("""\
    import { useState } from 'react'
    import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
    import { getOrders, confirmOrder } from '../../api/orders'
    import { getStocks, deleteStock } from '../../api/stocks'
    import toast from 'react-hot-toast'
    import AddStockForm from '../../components/stocks/AddStockForm'

    export default function SellerDashboard() {
      const [tab, setTab] = useState('orders')
      const qc = useQueryClient()

      const { data: orders } = useQuery({ queryKey: ['seller-orders'], queryFn: () => getOrders().then(r=>r.data) })
      const { data: stocks } = useQuery({ queryKey: ['seller-stocks'], queryFn: () => getStocks({}).then(r=>r.data) })

      const confirm = useMutation({
        mutationFn: (id) => confirmOrder(id),
        onSuccess: () => { toast.success('Order confirmed!'); qc.invalidateQueries(['seller-orders']) },
      })

      return (
        <div className=\"container mx-auto px-4 py-8\">
          <h1 className=\"text-2xl font-bold text-blue-900 mb-4\">Seller Dashboard</h1>

          <div className=\"flex gap-3 mb-6\">
            {['orders','stocks'].map(t => (
              <button key={t} onClick={() => setTab(t)}
                className={`px-4 py-2 rounded-lg capitalize font-medium ${tab===t ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}>
                {t}
              </button>
            ))}
          </div>

          {tab === 'orders' && (
            <div className=\"space-y-4\">
              {orders?.data?.map(order => (
                <div key={order.id} className=\"bg-white rounded-xl shadow p-4 flex justify-between items-center\">
                  <div>
                    <p className=\"font-semibold\">Order #{order.id} – {order.buyer?.name}</p>
                    <p className=\"text-gray-500 text-sm\">TZS {Number(order.total_amount).toLocaleString()} · {order.payment_status}</p>
                    <p className=\"text-sm capitalize\">Status: {order.status}</p>
                  </div>
                  {order.payment_status === 'paid' && order.status === 'received' && (
                    <button onClick={() => confirm.mutate(order.id)}
                      className=\"bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm\">
                      Confirm
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {tab === 'stocks' && (
            <div>
              <AddStockForm />
              <div className=\"mt-6 space-y-3\">
                {stocks?.data?.map(s => (
                  <div key={s.id} className=\"bg-white rounded-xl shadow p-4 flex justify-between items-center\">
                    <div>
                      <p className=\"font-semibold\">{s.fish_name} ({s.category?.name})</p>
                      <p className=\"text-gray-500 text-sm\">{s.quantity_kg} kg · TZS {Number(s.price_per_kg).toLocaleString()}/kg</p>
                    </div>
                    <button onClick={() => deleteStock(s.id).then(() => qc.invalidateQueries(['seller-stocks']))}
                      className=\"text-red-500 text-sm hover:underline\">Remove</button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )
    }
"""),

"frontend/src/components/stocks/AddStockForm.jsx": textwrap.dedent("""\
    import { useState } from 'react'
    import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query'
    import { createStock } from '../../api/stocks'
    import client from '../../api/client'
    import toast from 'react-hot-toast'

    export default function AddStockForm() {
      const qc = useQueryClient()
      const [form, setForm] = useState({ fish_name:'', category_id:'', quantity_kg:'', price_per_kg:'' })
      const [image, setImage] = useState(null)

      const { data: cats } = useQuery({
        queryKey: ['categories'],
        queryFn: () => client.get('/categories').then(r => r.data),
      })

      const add = useMutation({
        mutationFn: () => {
          const fd = new FormData()
          Object.entries(form).forEach(([k,v]) => fd.append(k, v))
          if (image) fd.append('image', image)
          return createStock(fd)
        },
        onSuccess: () => { toast.success('Stock added!'); qc.invalidateQueries(['seller-stocks']); setForm({fish_name:'',category_id:'',quantity_kg:'',price_per_kg:''}) },
        onError: () => toast.error('Failed to add stock'),
      })

      return (
        <div className=\"bg-white rounded-xl shadow p-5\">
          <h2 className=\"font-bold text-blue-900 mb-4\">Add Fish Stock</h2>
          <div className=\"grid grid-cols-2 gap-3\">
            <select className=\"input col-span-2\" value={form.category_id} onChange={e=>setForm({...form,category_id:e.target.value})}>
              <option value=\"\">Select category…</option>
              {cats?.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
            <input className=\"input\" placeholder=\"Fish name\" value={form.fish_name} onChange={e=>setForm({...form,fish_name:e.target.value})} />
            <input className=\"input\" type=\"number\" placeholder=\"Qty (kg)\" value={form.quantity_kg} onChange={e=>setForm({...form,quantity_kg:e.target.value})} />
            <input className=\"input\" type=\"number\" placeholder=\"Price/kg\" value={form.price_per_kg} onChange={e=>setForm({...form,price_per_kg:e.target.value})} />
            <input className=\"input\" type=\"file\" accept=\"image/*\" onChange={e=>setImage(e.target.files[0])} />
          </div>
          <button onClick={()=>add.mutate()} disabled={add.isPending}
            className=\"mt-4 btn-primary\">
            {add.isPending ? 'Adding…' : 'Add Stock'}
          </button>
        </div>
      )
    }
"""),

"frontend/src/App.jsx": textwrap.dedent("""\
    import { Routes, Route, Navigate } from 'react-router-dom'
    import { Toaster } from 'react-hot-toast'
    import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
    import { useAuthStore } from './store/authStore'
    import Layout from './components/layout/Layout'
    import LoginPage from './pages/auth/LoginPage'
    import RegisterPage from './pages/auth/RegisterPage'
    import MarketPage from './pages/market/MarketPage'
    import SellerPage from './pages/market/SellerPage'
    import SellerDashboard from './pages/dashboard/SellerDashboard'
    import BuyerDashboard from './pages/dashboard/BuyerDashboard'
    import AdminPanel from './pages/admin/AdminPanel'

    const qc = new QueryClient()

    function PrivateRoute({ children, roles }) {
      const { user } = useAuthStore()
      if (!user) return <Navigate to=\"/login\" replace />
      if (roles && !roles.includes(user.role)) return <Navigate to=\"/\" replace />
      return children
    }

    export default function App() {
      const { user } = useAuthStore()
      return (
        <QueryClientProvider client={qc}>
          <Toaster position=\"top-right\" />
          <Routes>
            <Route path=\"/login\"    element={<LoginPage />} />
            <Route path=\"/register\" element={<RegisterPage />} />
            <Route element={<Layout />}>
              <Route path=\"/\"              element={<MarketPage />} />
              <Route path=\"/sellers/:id\"   element={<SellerPage />} />
              <Route path=\"/dashboard\" element={
                <PrivateRoute>
                  {user?.role === 'seller' ? <SellerDashboard /> : <BuyerDashboard />}
                </PrivateRoute>
              } />
              <Route path=\"/admin\" element={
                <PrivateRoute roles={['admin']}><AdminPanel /></PrivateRoute>
              } />
            </Route>
          </Routes>
        </QueryClientProvider>
      )
    }
"""),

# ── Updated schema ─────────────────────────────────────────────────────────
"database/schema.sql": textwrap.dedent("""\
    -- SmartFish – Fish Market Access & Distribution System
    -- Reference schema v2 (run via Laravel migrations on PlanetScale)

    CREATE TABLE users (
      id                  BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      name                VARCHAR(255) NOT NULL,
      email               VARCHAR(255) NOT NULL UNIQUE,
      password            VARCHAR(255) NOT NULL,
      role                ENUM('admin','seller','buyer') DEFAULT 'buyer',
      phone               VARCHAR(50),
      location            VARCHAR(255),
      brand_logo          VARCHAR(255),
      office_address      VARCHAR(255),
      location_address    VARCHAR(255),
      bio                 TEXT,
      is_active           TINYINT(1) DEFAULT 1,
      subscription_status ENUM('active','pending','inactive') DEFAULT 'inactive',
      created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL
    );

    CREATE TABLE fish_categories (
      id   BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      name VARCHAR(255) NOT NULL UNIQUE,
      description VARCHAR(255),
      created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL
    );

    CREATE TABLE fish_stocks (
      id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      seller_id    BIGINT UNSIGNED NOT NULL,
      category_id  BIGINT UNSIGNED NOT NULL,
      fish_name    VARCHAR(255) NOT NULL,
      image        VARCHAR(255),
      quantity_kg  DECIMAL(10,2) DEFAULT 0,
      price_per_kg DECIMAL(10,2) NOT NULL,
      status       ENUM('active','out_of_stock') DEFAULT 'active',
      created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
      FOREIGN KEY (seller_id)   REFERENCES users(id) ON DELETE CASCADE,
      FOREIGN KEY (category_id) REFERENCES fish_categories(id)
    );

    CREATE TABLE delivery_agencies (
      id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      seller_id    BIGINT UNSIGNED NOT NULL,
      agency_name  VARCHAR(255) NOT NULL,
      contact      VARCHAR(100),
      area_covered VARCHAR(255),
      is_active    TINYINT(1) DEFAULT 1,
      created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
      FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE orders (
      id             BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      buyer_id       BIGINT UNSIGNED NOT NULL,
      seller_id      BIGINT UNSIGNED NOT NULL,
      status         ENUM('pending','received','confirmed','processed','cancelled') DEFAULT 'pending',
      payment_method ENUM('mobile','bank'),
      payment_status ENUM('unpaid','paid') DEFAULT 'unpaid',
      total_amount   DECIMAL(12,2) DEFAULT 0,
      created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
      FOREIGN KEY (buyer_id)  REFERENCES users(id),
      FOREIGN KEY (seller_id) REFERENCES users(id)
    );

    CREATE TABLE order_items (
      id           BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      order_id     BIGINT UNSIGNED NOT NULL,
      stock_id     BIGINT UNSIGNED NOT NULL,
      fish_name    VARCHAR(255) NOT NULL,
      quantity_kg  DECIMAL(10,2),
      price_per_kg DECIMAL(10,2),
      subtotal     DECIMAL(12,2),
      FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
      FOREIGN KEY (stock_id) REFERENCES fish_stocks(id)
    );

    CREATE TABLE order_deliveries (
      id              BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      order_id        BIGINT UNSIGNED NOT NULL,
      agency_id       BIGINT UNSIGNED NOT NULL,
      delivery_method VARCHAR(100),
      delivery_status ENUM('pending','dispatched','delivered') DEFAULT 'pending',
      created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
      FOREIGN KEY (order_id)  REFERENCES orders(id) ON DELETE CASCADE,
      FOREIGN KEY (agency_id) REFERENCES delivery_agencies(id)
    );

    CREATE TABLE bills (
      id          BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      order_id    BIGINT UNSIGNED NOT NULL UNIQUE,
      buyer_id    BIGINT UNSIGNED NOT NULL,
      bill_number VARCHAR(50) UNIQUE,
      issued_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
      FOREIGN KEY (order_id) REFERENCES orders(id),
      FOREIGN KEY (buyer_id) REFERENCES users(id)
    );

    CREATE TABLE subscriptions (
      id        BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
      seller_id BIGINT UNSIGNED NOT NULL,
      plan      ENUM('monthly','annual'),
      amount    DECIMAL(10,2),
      status    ENUM('pending','active','expired') DEFAULT 'pending',
      paid_at   TIMESTAMP NULL,
      created_at TIMESTAMP NULL, updated_at TIMESTAMP NULL,
      FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE CASCADE
    );
"""),

}

# ─────────────────────────────────────────────────────────────────────────────
#  WRITE FILES
# ─────────────────────────────────────────────────────────────────────────────

def run():
    # Write sprint file
    sprint_path = os.path.join(BASE, "project_sprints.txt")
    with open(sprint_path, "w", encoding="utf-8") as f:
        f.write(SPRINTS)
    print(f"✅  project_sprints.txt updated")

    # Write patch files
    for rel, content in PATCH_FILES.items():
        full = os.path.join(BASE, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄  {rel}")

    print(f"\n✅  Patch v2 applied → {BASE}")
    print("""
KEY CHANGES FROM IMAGES
────────────────────────
  ✓ System renamed SmartFish
  ✓ Roles: admin / seller / buyer  (not fisher/trader/customer)
  ✓ Seller has public shop page: brand logo, office address, location
  ✓ Fish stocks categorized (Tilapia, Dagaa, Perch, etc.)
  ✓ Stock quantity auto-decreases on order confirmation (Model method)
  ✓ Delivery agencies managed by seller, chosen by buyer at checkout
  ✓ Order status flow: pending → received → confirmed → processed
  ✓ Bill auto-generated when seller confirms
  ✓ Subscription billing: seller pays monthly/annual; admin confirms
  ✓ Payment: mobile money or bank transfer

DEV ENV CHANGES  (Kali rootless)
──────────────────────────────────
  ✓ Backend has .env.testing for GitHub Actions only
  ✓ GitHub Actions: backend-test + frontend-build + docker-build-check
  ✓ Frontend .env always points to Render (no local backend needed)
  ✓ No local MySQL, Docker, or PHP required
  ✓ Write code → push → CI tests → Render/Vercel auto-deploy
""")

if __name__ == "__main__":
    run()

