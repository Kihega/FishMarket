#!/usr/bin/env python3
"""
FishMarket Patch Script
Run from the FishMarket root directory:
    python3 patch_fishmarket.py

Fixes:
  1. Frontend always reads VITE_API_BASE_URL from .env (no hardcoded Render URLs).
     Backend reads DB credentials from .env only. Both .env files are reset to
     local-dev defaults with clear instructions.
  2. DatabaseSeeder seeds ONLY the test admin (no factory data).
     Admin credentials are printed clearly after migration+seed.
  3. Real-time polling added to all dashboard panels that show live data:
     - BuyerDashboard: sellers list (15 s), orders (15 s)
     - SellerDashboard: orders (10 s), stocks (15 s), buyers (10 s), agencies (15 s)
     - SellerPage: seller profile + stocks (20 s)
     - MarketPage: sellers list (30 s)
     Image URLs routed through the backend's APP_URL (not relative /storage/…)
     so local and remote environments both resolve images correctly.
"""

import os
import sys
import shutil
import textwrap

ROOT = os.path.abspath(os.getcwd())
FRONTEND = os.path.join(ROOT, "frontend")
BACKEND  = os.path.join(ROOT, "backend")

def p(path):
    """Absolute path relative to ROOT."""
    return os.path.join(ROOT, path)

def write(rel, content):
    """Write content to a file, creating parent dirs as needed."""
    target = p(rel)
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(content).lstrip("\n"))
    print(f"  ✔  {rel}")

def backup(rel):
    """Copy original file to .bak before overwriting."""
    src = p(rel)
    if os.path.exists(src):
        shutil.copy2(src, src + ".bak")

# ─────────────────────────────────────────────────────────────────────────────
# 1. ENVIRONMENT FILES
# ─────────────────────────────────────────────────────────────────────────────

def patch_env_files():
    print("\n[1/5] Patching environment files…")

    # frontend/.env  — local dev always hits local backend
    backup("frontend/.env")
    write("frontend/.env", """
        # ── Local development ─────────────────────────────────────────────
        # This file is read by Vite at build/dev time.
        # Change this to your local backend address if you use a different port.
        VITE_API_BASE_URL=http://localhost:8000/api
    """)

    # frontend/.env.example — guide for anyone cloning the repo
    write("frontend/.env.example", """
        # Copy this file to .env and fill in the values for your environment.
        #
        # LOCAL development (Laravel backend on your machine):
        VITE_API_BASE_URL=http://localhost:8000/api
        #
        # PRODUCTION (e.g. Render backend):
        # VITE_API_BASE_URL=https://your-backend.onrender.com/api
    """)

    # backend/.env.example — local MySQL / Oracle MySQL guide
    write("backend/.env.example", """
        APP_NAME=SmartFish
        APP_ENV=local
        APP_KEY=
        APP_DEBUG=true
        APP_URL=http://localhost:8000

        # ── Local MySQL / Oracle MySQL ────────────────────────────────────
        # Leave DATABASE_URL empty for local; use individual DB_* vars instead.
        DATABASE_URL=

        DB_CONNECTION=mysql
        DB_HOST=127.0.0.1
        DB_PORT=3306
        DB_DATABASE=fishmarket
        DB_USERNAME=root
        DB_PASSWORD=

        # ── Production Aiven MySQL (fill in when deploying) ───────────────
        # DATABASE_URL=mysql://user:pass@host:port/dbname
        # MYSQL_ATTR_SSL_CA=/var/www/docker/aiven-ca.pem

        QUEUE_CONNECTION=sync
        SESSION_DRIVER=cookie
        CACHE_STORE=database

        # CORS: set to your frontend origin
        FRONTEND_URL=http://localhost:5173
        SANCTUM_STATEFUL_DOMAINS=localhost:5173,127.0.0.1:5173

        # Cloudinary — only needed for production image uploads
        # CLOUDINARY_URL=cloudinary://key:secret@cloud_name

        LOG_CHANNEL=stack
        LOG_LEVEL=debug
    """)

    print("    → frontend/.env now points to http://localhost:8000/api")
    print("    → backend/.env.example updated with local MySQL guide")
    print("    → Reminder: copy backend/.env.example → backend/.env and fill DB creds")


# ─────────────────────────────────────────────────────────────────────────────
# 2. DATABASE SEEDER — test admin only
# ─────────────────────────────────────────────────────────────────────────────

def patch_seeder():
    print("\n[2/5] Patching DatabaseSeeder (test admin only)…")
    backup("backend/database/seeders/DatabaseSeeder.php")
    write("backend/database/seeders/DatabaseSeeder.php", r"""
        <?php

        namespace Database\Seeders;

        use App\Models\User;
        use Illuminate\Database\Seeder;
        use Illuminate\Support\Facades\Hash;

        /**
         * Seeds ONLY the test admin account.
         *
         * Fish categories are intentionally excluded from fresh clones —
         * they are created through the Admin Panel UI (or via FishCategorySeeder
         * independently).  This seeder exists solely to bootstrap the very first
         * login after `php artisan migrate --seed` on a fresh database.
         *
         * Credentials printed to console after seeding.
         */
        class DatabaseSeeder extends Seeder
        {
            public function run(): void
            {
                $email    = env('ADMIN_EMAIL',    'admin@smartfish.test');
                $password = env('ADMIN_PASSWORD', 'Admin@1234');

                $created = false;

                $admin = User::firstOrCreate(
                    ['email' => $email],
                    [
                        'name'                => 'SmartFish Admin',
                        'password'            => Hash::make($password),
                        'role'                => 'admin',
                        'is_active'           => true,
                        'subscription_status' => 'active',
                    ]
                );

                if ($admin->wasRecentlyCreated) {
                    $created = true;
                }

                $this->command->newLine();
                $this->command->info('╔══════════════════════════════════════════════╗');
                $this->command->info('║         SmartFish — Admin Account            ║');
                $this->command->info('╠══════════════════════════════════════════════╣');
                $this->command->info("║  Email   : {$email}");
                $this->command->info("║  Password: {$password}");
                $this->command->info('║                                              ║');
                $this->command->info($created
                    ? '║  ✔ Admin account CREATED successfully.       ║'
                    : '║  ℹ Admin account already existed — skipped.  ║'
                );
                $this->command->info('╚══════════════════════════════════════════════╝');
                $this->command->newLine();
                $this->command->warn('Change the password after your first login!');
            }
        }
    """)


# ─────────────────────────────────────────────────────────────────────────────
# 3. BACKEND: ensure CORS allows local frontend, image URL helper
# ─────────────────────────────────────────────────────────────────────────────

def patch_backend():
    print("\n[3/5] Patching backend CORS config and image storage…")

    # CORS — keep existing Vercel pattern, add localhost explicitly
    backup("backend/config/cors.php")
    write("backend/config/cors.php", r"""
        <?php

        return [

            'paths' => ['api/*', 'sanctum/csrf-cookie'],

            'allowed_methods' => ['*'],

            'allowed_origins' => array_filter([
                env('FRONTEND_URL', 'http://localhost:5173'),
                'http://localhost:5173',
                'http://127.0.0.1:5173',
                'http://localhost:3000',
            ]),

            'allowed_origins_patterns' => [
                // Vercel preview deployments
                '#^https://.*\.vercel\.app$#',
            ],

            'allowed_headers' => ['*'],

            'exposed_headers' => [],

            'max_age' => 0,

            'supports_credentials' => false,

        ];
    """)

    # StoresImages — return full URL for local mode so frontend doesn't need
    # to know the backend base URL when constructing image src attributes.
    backup("backend/app/Http/Controllers/API/Concerns/StoresImages.php")
    write("backend/app/Http/Controllers/API/Concerns/StoresImages.php", r"""
        <?php

        namespace App\Http\Controllers\API\Concerns;

        use Illuminate\Http\UploadedFile;
        use Illuminate\Support\Facades\Storage;

        /**
         * Decides HOW to store an uploaded image:
         *
         * - Local DB (127.0.0.1 / localhost):
         *     Base64-encode and store inline in the DB column.
         *     No disk or symlink setup required — works immediately on
         *     any fresh clone.
         *
         * - Remote DB (Aiven / production):
         *     Store on Laravel's public disk; return a full URL
         *     (APP_URL/storage/path) so the frontend never has to
         *     guess the backend origin.
         *
         * The DB column always holds either:
         *   "data:image/jpeg;base64,…"   ← local
         *   "https://host/storage/…"     ← remote
         *
         * The frontend checks `startsWith('data:')` or `startsWith('http')`
         * and uses the value as-is in both cases.
         */
        trait StoresImages
        {
            protected function isLocalDatabase(): bool
            {
                // When DATABASE_URL is set (production), the host env var
                // is the Aiven hostname — never 127.0.0.1/localhost.
                $host = config('database.connections.mysql.host', '');
                return in_array($host, ['127.0.0.1', 'localhost'], true);
            }

            protected function storeImage(UploadedFile $file, string $folder): string
            {
                if ($this->isLocalDatabase()) {
                    $mime     = $file->getMimeType();
                    $contents = base64_encode(file_get_contents($file->getRealPath()));
                    return "data:{$mime};base64,{$contents}";
                }

                // Production: store on disk, return full URL
                $path = $file->store($folder, 'public');
                return Storage::disk('public')->url($path);
            }
        }
    """)


# ─────────────────────────────────────────────────────────────────────────────
# 4. FRONTEND: fix all hardcoded image paths, add real-time polling
# ─────────────────────────────────────────────────────────────────────────────

def patch_frontend():
    print("\n[4/5] Patching frontend files…")

    # ── api/client.js — already correct (uses VITE_API_BASE_URL), but add
    #    a small helper so image URLs work for both local base64 and remote http
    backup("frontend/src/api/client.js")
    write("frontend/src/api/client.js", r"""
        import axios from 'axios'
        import { useAuthStore } from '../store/authStore'

        const client = axios.create({
          baseURL: import.meta.env.VITE_API_BASE_URL,
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          // Generous timeout for Render cold-starts on production
          timeout: 45000,
        })

        client.interceptors.request.use((config) => {
          const token = useAuthStore.getState().token
          if (token) config.headers.Authorization = `Bearer ${token}`
          return config
        })

        client.interceptors.response.use(
          (res) => res,
          (err) => {
            if (err.response?.status === 401) {
              useAuthStore.getState().clearAuth()
            }
            return Promise.reject(err)
          }
        )

        export default client

        /**
         * Resolve an image value from the backend.
         *
         * The backend stores either:
         *   - "data:image/...;base64,..."  (local mode)
         *   - "https://..."                (production full URL)
         *
         * Returns null for falsy input so callers can safely do:
         *   {resolveImage(src) && <img src={resolveImage(src)} />}
         */
        export function resolveImage(src) {
          if (!src) return null
          if (src.startsWith('data:') || src.startsWith('http')) return src
          // Fallback for old disk-path values (e.g. "stocks/abc.jpg")
          const base = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/api\/?$/, '')
          return `${base}/storage/${src}`
        }
    """)

    # ── BuyerDashboard — real-time polling + correct image resolution
    backup("frontend/src/pages/dashboard/BuyerDashboard.jsx")
    write("frontend/src/pages/dashboard/BuyerDashboard.jsx", r"""
        import { useState } from 'react'
        import { useQuery } from '@tanstack/react-query'
        import { Link } from 'react-router-dom'
        import { Fish, MapPin, Receipt } from 'lucide-react'
        import { getOrders } from '../../api/orders'
        import { getSellers } from '../../api/sellers'
        import { resolveImage } from '../../api/client'
        import { useAuthStore } from '../../store/authStore'
        import { formatTsh } from '../../utils/currency'
        import DashboardLayout from '../../components/dashboard/DashboardLayout'
        import ChangePasswordModal from '../../components/dashboard/ChangePasswordModal'
        import { HomeIcon, ClipboardListIcon, LockIcon, LogoutIcon } from '../../components/dashboard/Icons'

        const SECTIONS = [
          { key: 'home',     label: 'Home',            icon: HomeIcon },
          { key: 'orders',   label: 'My Orders',       icon: ClipboardListIcon },
          { key: 'password', label: 'Change Password', icon: LockIcon },
          { key: 'logout',   label: 'Logout',          icon: LogoutIcon },
        ]

        const STATUS_STYLE = {
          pending:   'bg-yellow-100 text-yellow-700',
          received:  'bg-blue-100 text-blue-700',
          confirmed: 'bg-green-100 text-green-700',
          processed: 'bg-gray-100 text-gray-700',
          cancelled: 'bg-red-100 text-red-600',
        }

        export default function BuyerDashboard() {
          const [active, setActive] = useState('home')
          const [showPasswordModal, setShowPasswordModal] = useState(false)
          const { clearAuth } = useAuthStore()

          const handleSelect = (key) => {
            if (key === 'logout') { clearAuth(); window.location.href = '/'; return }
            if (key === 'password') { setShowPasswordModal(true); return }
            setActive(key)
          }

          return (
            <>
              <DashboardLayout items={SECTIONS} activeKey={active} onSelect={handleSelect}>
                {active === 'home'   && <HomePanel />}
                {active === 'orders' && <OrdersPanel />}
              </DashboardLayout>
              {showPasswordModal && <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />}
            </>
          )
        }

        // ── HOME — browse seller platforms, refreshes every 15 s ─────────────
        function HomePanel() {
          const { data, isLoading } = useQuery({
            queryKey: ['buyer-home-sellers'],
            queryFn: () => getSellers({}).then((r) => r.data),
            refetchInterval: 15000,          // live: new sellers appear within 15 s
            staleTime: 0,
          })

          return (
            <div>
              <h1 className="text-2xl font-bold text-blue-900 mb-2">Browse Markets</h1>
              <p className="text-gray-500 text-sm mb-6">
                Registered seller businesses on SmartFish · updates every 15 s
              </p>

              {isLoading ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-40 bg-gray-100 animate-pulse rounded-2xl" />
                  ))}
                </div>
              ) : data?.data?.length ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                  {data.data.map((seller) => (
                    <Link
                      key={seller.id}
                      to={`/sellers/${seller.id}`}
                      className="bg-white rounded-2xl shadow p-5 hover:shadow-md transition flex flex-col gap-3"
                    >
                      <div className="flex items-center gap-3">
                        {resolveImage(seller.brand_logo) ? (
                          <img
                            src={resolveImage(seller.brand_logo)}
                            alt={seller.name}
                            className="w-14 h-14 rounded-full object-cover border"
                          />
                        ) : (
                          <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center">
                            <Fish className="w-6 h-6 text-blue-600" />
                          </div>
                        )}
                        <div>
                          <h3 className="font-bold text-blue-900">{seller.name}</h3>
                          <p className="text-gray-500 text-sm flex items-center gap-1">
                            <MapPin className="w-3.5 h-3.5" /> {seller.location_address || seller.location}
                          </p>
                        </div>
                      </div>
                      <p className="text-sm text-blue-600">{seller.fish_stocks_count} items available</p>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-10">No sellers registered yet.</p>
              )}
            </div>
          )
        }

        // ── MY ORDERS — polls every 15 s ─────────────────────────────────────
        function OrdersPanel() {
          const { data, isLoading } = useQuery({
            queryKey: ['my-orders'],
            queryFn: () => getOrders().then((r) => r.data),
            refetchInterval: 15000,
            staleTime: 0,
          })

          return (
            <div>
              <h1 className="text-2xl font-bold text-blue-900 mb-2">My Orders</h1>
              <p className="text-gray-500 text-sm mb-6">Live order updates · refreshes every 15 s</p>

              {isLoading ? (
                <p className="text-gray-400">Loading orders…</p>
              ) : data?.data?.length ? (
                <div className="space-y-4">
                  {data.data.map((order) => (
                    <div key={order.id} className="bg-white rounded-xl shadow p-5">
                      <div className="flex justify-between items-start flex-wrap gap-2">
                        <div>
                          <p className="font-semibold">Order #{order.id} — {order.seller?.name}</p>
                          <p className="text-gray-500 text-sm">
                            {order.items?.length} item(s) · {formatTsh(order.total_amount)}
                          </p>
                        </div>
                        <span className={`text-xs px-3 py-1 rounded-full font-medium ${STATUS_STYLE[order.status] ?? ''}`}>
                          {order.status?.toUpperCase()}
                        </span>
                      </div>
                      {order.bill && (
                        <p className="text-sm text-blue-600 mt-2 flex items-center gap-1">
                          <Receipt className="w-4 h-4" /> Bill #{order.bill.bill_number}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-10">
                  No orders yet — browse the marketplace to get started.
                </p>
              )}
            </div>
          )
        }
    """)

    # ── SellerDashboard — real-time polling + correct image resolution
    backup("frontend/src/pages/dashboard/SellerDashboard.jsx")
    write("frontend/src/pages/dashboard/SellerDashboard.jsx", r"""
        import { useState } from 'react'
        import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
        import toast from 'react-hot-toast'
        import client, { resolveImage } from '../../api/client'
        import { getOrders, confirmOrder } from '../../api/orders'
        import { getStocks, deleteStock } from '../../api/stocks'
        import { useAuthStore } from '../../store/authStore'
        import { formatTsh } from '../../utils/currency'
        import DashboardLayout from '../../components/dashboard/DashboardLayout'
        import ChangePasswordModal from '../../components/dashboard/ChangePasswordModal'
        import ModalShell from '../../components/auth/ModalShell'
        import AddStockForm from '../../components/stocks/AddStockForm'
        import {
          HomeIcon, ClipboardListIcon, PackageIcon, ContactIcon,
          TruckIcon, LockIcon, LogoutIcon,
        } from '../../components/dashboard/Icons'

        const SECTIONS = [
          { key: 'home',     label: 'Home',              icon: HomeIcon },
          { key: 'orders',   label: 'Manage Orders',     icon: ClipboardListIcon },
          { key: 'stocks',   label: 'Manage Stocks',     icon: PackageIcon },
          { key: 'buyers',   label: 'Manage Buyers',     icon: ContactIcon },
          { key: 'agencies', label: 'Delivery Partners', icon: TruckIcon },
          { key: 'password', label: 'Change Password',   icon: LockIcon },
          { key: 'logout',   label: 'Logout',            icon: LogoutIcon },
        ]

        export default function SellerDashboard() {
          const [active, setActive] = useState('home')
          const [showPasswordModal, setShowPasswordModal] = useState(false)
          const { clearAuth } = useAuthStore()

          const handleSelect = (key) => {
            if (key === 'logout') { clearAuth(); window.location.href = '/'; return }
            if (key === 'password') { setShowPasswordModal(true); return }
            setActive(key)
          }

          return (
            <>
              <DashboardLayout items={SECTIONS} activeKey={active} onSelect={handleSelect}>
                {active === 'home'     && <HomePanel />}
                {active === 'orders'   && <OrdersPanel />}
                {active === 'stocks'   && <StocksPanel />}
                {active === 'buyers'   && <BuyersPanel />}
                {active === 'agencies' && <AgenciesPanel />}
              </DashboardLayout>
              {showPasswordModal && <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />}
            </>
          )
        }

        // ── HOME — quick stats overview (polls every 30 s) ────────────────────
        function HomePanel() {
          const { data: orders } = useQuery({
            queryKey: ['seller-orders'],
            queryFn: () => getOrders().then((r) => r.data),
            refetchInterval: 30000,
            staleTime: 0,
          })
          const { data: stocks } = useQuery({
            queryKey: ['seller-stocks'],
            queryFn: () => getStocks({}).then((r) => r.data),
            refetchInterval: 30000,
            staleTime: 0,
          })

          const pendingCount = orders?.data?.filter(
            (o) => o.status === 'pending' || o.status === 'received'
          ).length ?? 0

          return (
            <div>
              <h1 className="text-2xl font-bold text-blue-900 mb-6">Welcome back</h1>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <StatCard label="Pending Orders"    value={pendingCount} />
                <StatCard label="Active Stock Items" value={stocks?.data?.length ?? 0} />
                <StatCard label="Total Orders"       value={orders?.data?.length ?? 0} />
              </div>
            </div>
          )
        }

        function StatCard({ label, value }) {
          return (
            <div className="bg-white rounded-2xl shadow p-6 text-center">
              <p className="text-3xl font-bold text-blue-700">{value ?? '—'}</p>
              <p className="text-sm text-gray-500 mt-1">{label}</p>
            </div>
          )
        }

        // ── MANAGE ORDERS — polls every 10 s ─────────────────────────────────
        function OrdersPanel() {
          const qc = useQueryClient()

          const { data: orders } = useQuery({
            queryKey: ['seller-orders'],
            queryFn: () => getOrders().then((r) => r.data),
            refetchInterval: 10000,      // new orders appear within 10 s
            staleTime: 0,
          })

          const confirm = useMutation({
            mutationFn: (id) => confirmOrder(id),
            onSuccess: () => {
              toast.success('Order confirmed!')
              qc.invalidateQueries({ queryKey: ['seller-orders'] })
            },
          })

          return (
            <div>
              <h1 className="text-2xl font-bold text-blue-900 mb-2">Manage Orders</h1>
              <p className="text-gray-500 text-sm mb-6">Live order updates · refreshes every 10 s</p>

              <div className="space-y-4">
                {orders?.data?.length ? (
                  orders.data.map((order) => (
                    <div
                      key={order.id}
                      className="bg-white rounded-xl shadow p-4 flex justify-between items-center flex-wrap gap-3"
                    >
                      <div>
                        <p className="font-semibold">Order #{order.id} — {order.buyer?.name}</p>
                        <p className="text-gray-500 text-sm">
                          {formatTsh(order.total_amount)} · {order.payment_status}
                        </p>
                        <p className="text-sm capitalize">Status: {order.status}</p>
                      </div>
                      {order.payment_status === 'paid' && order.status === 'received' && (
                        <button
                          onClick={() => confirm.mutate(order.id)}
                          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
                        >
                          Confirm
                        </button>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-center py-10">No orders yet.</p>
                )}
              </div>
            </div>
          )
        }

        // ── MANAGE STOCKS — polls every 15 s ─────────────────────────────────
        function StocksPanel() {
          const qc = useQueryClient()
          const [showAddForm, setShowAddForm] = useState(false)

          const { data: stocks } = useQuery({
            queryKey: ['seller-stocks'],
            queryFn: () => getStocks({}).then((r) => r.data),
            refetchInterval: 15000,
            staleTime: 0,
          })

          const remove = useMutation({
            mutationFn: (id) => deleteStock(id),
            onSuccess: () => {
              toast.success('Stock removed')
              qc.invalidateQueries({ queryKey: ['seller-stocks'] })
            },
          })

          return (
            <div>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h1 className="text-2xl font-bold text-blue-900">Manage Stocks</h1>
                  <p className="text-gray-500 text-sm">Live updates · refreshes every 15 s</p>
                </div>
                <button onClick={() => setShowAddForm(true)} className="btn-primary">
                  + Add New Stock
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
                {stocks?.data?.length ? (
                  stocks.data.map((s) => (
                    <div key={s.id} className="bg-white rounded-xl shadow p-4 flex flex-col">
                      {resolveImage(s.image) && (
                        <img
                          src={resolveImage(s.image)}
                          alt={s.fish_name}
                          className="w-full h-32 object-cover rounded-lg mb-3"
                        />
                      )}
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full self-start mb-1">
                        {s.category?.name}
                      </span>
                      <p className="font-semibold">{s.fish_name}</p>
                      <p className="text-gray-500 text-sm">
                        {s.quantity_kg} kg · {formatTsh(s.price_per_kg)}/kg
                      </p>
                      <span className={`text-xs mt-1 ${s.status === 'active' ? 'text-green-600' : 'text-red-500'}`}>
                        {s.status === 'active' ? '● In Stock' : '● Out of Stock'}
                      </span>
                      <button
                        onClick={() => remove.mutate(s.id)}
                        className="mt-3 text-red-500 text-sm hover:underline self-start"
                      >
                        Remove Stock
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 col-span-full text-center py-10">
                    No stock items yet — add your first one above.
                  </p>
                )}
              </div>

              {showAddForm && (
                <ModalShell onClose={() => setShowAddForm(false)} maxWidth="max-w-lg">
                  <AddStockForm onDone={() => { setShowAddForm(false); qc.invalidateQueries({ queryKey: ['seller-stocks'] }) }} />
                </ModalShell>
              )}
            </div>
          )
        }

        // ── MANAGE BUYERS — polls every 10 s ─────────────────────────────────
        function BuyersPanel() {
          const { data: buyers } = useQuery({
            queryKey: ['seller-buyers'],
            queryFn: () => client.get('/seller/buyers').then((r) => r.data),
            refetchInterval: 10000,
            staleTime: 0,
          })

          return (
            <div>
              <h1 className="text-2xl font-bold text-blue-900 mb-2">Manage Buyers</h1>
              <p className="text-gray-500 text-sm mb-6">
                Buyers who have placed orders on your platform · live updates every 10 s
              </p>

              <div className="bg-white rounded-xl shadow divide-y">
                {buyers?.length ? (
                  buyers.map((b) => (
                    <div key={b.order_id} className="flex flex-wrap justify-between items-center gap-3 p-4">
                      <div>
                        <p className="font-semibold">{b.buyer_name}</p>
                        <p className="text-sm text-gray-500">{b.buyer_phone} · {b.buyer_email}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          Ordered {new Date(b.ordered_at).toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs capitalize bg-blue-50 text-blue-700 px-2 py-1 rounded-full">
                          {b.order_status}
                        </span>
                        <p className="text-xs text-gray-400 mt-1 capitalize">
                          Delivery: {b.delivery_status}
                        </p>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 p-6 text-center">No buyers yet.</p>
                )}
              </div>
            </div>
          )
        }

        // ── DELIVERY PARTNERS — polls every 15 s ─────────────────────────────
        function AgenciesPanel() {
          const qc = useQueryClient()
          const [form, setForm] = useState({ agency_name: '', contact: '', area_covered: '' })

          const { data: agencies } = useQuery({
            queryKey: ['seller-agencies'],
            queryFn: () => client.get('/agencies').then((r) => r.data),
            refetchInterval: 15000,
            staleTime: 0,
          })

          const addAgency = useMutation({
            mutationFn: (data) => client.post('/agencies', data),
            onSuccess: () => {
              toast.success('Delivery partner added')
              qc.invalidateQueries({ queryKey: ['seller-agencies'] })
              setForm({ agency_name: '', contact: '', area_covered: '' })
            },
          })

          const removeAgency = useMutation({
            mutationFn: (id) => client.delete(`/agencies/${id}`),
            onSuccess: () => {
              toast.success('Delivery partner removed')
              qc.invalidateQueries({ queryKey: ['seller-agencies'] })
            },
          })

          return (
            <div>
              <h1 className="text-2xl font-bold text-blue-900 mb-6">Delivery Partners</h1>

              <div className="bg-white rounded-xl shadow p-5 mb-6">
                <h2 className="font-bold text-blue-900 mb-3">Add Delivery Partner</h2>
                <div className="grid sm:grid-cols-3 gap-3">
                  <input
                    placeholder="Agency Name" className="input"
                    value={form.agency_name}
                    onChange={(e) => setForm({ ...form, agency_name: e.target.value })}
                  />
                  <input
                    placeholder="Contact" className="input"
                    value={form.contact}
                    onChange={(e) => setForm({ ...form, contact: e.target.value })}
                  />
                  <input
                    placeholder="Area Covered" className="input"
                    value={form.area_covered}
                    onChange={(e) => setForm({ ...form, area_covered: e.target.value })}
                  />
                </div>
                <button
                  onClick={() => addAgency.mutate(form)}
                  disabled={!form.agency_name || addAgency.isPending}
                  className="btn-primary mt-3"
                >
                  {addAgency.isPending ? 'Adding…' : 'Add Partner'}
                </button>
              </div>

              <div className="bg-white rounded-xl shadow divide-y">
                {agencies?.length ? (
                  agencies.map((a) => (
                    <div key={a.id} className="flex justify-between items-center p-4">
                      <div>
                        <p className="font-semibold">{a.agency_name}</p>
                        <p className="text-sm text-gray-500">{a.contact} · {a.area_covered}</p>
                      </div>
                      <button
                        onClick={() => removeAgency.mutate(a.id)}
                        className="text-red-500 text-sm hover:underline"
                      >
                        Remove
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 p-6 text-center">No delivery partners yet.</p>
                )}
              </div>
            </div>
          )
        }
    """)

    # ── MarketPage — polls every 30 s, no hardcoded fallback message about Render
    backup("frontend/src/pages/market/MarketPage.jsx")
    write("frontend/src/pages/market/MarketPage.jsx", r"""
        import { useQuery } from '@tanstack/react-query'
        import { getSellers } from '../../api/sellers'
        import SellerCard from '../../components/sellers/SellerCard'
        import { useUIStore } from '../../store/uiStore'

        export default function MarketPage() {
          const { openSignupChoice } = useUIStore()

          const { data, isLoading, isError, refetch, isFetching } = useQuery({
            queryKey: ['sellers-home'],
            queryFn: () => getSellers({}).then((r) => r.data),
            refetchInterval: 30000,   // new sellers appear on the homepage within 30 s
            staleTime: 0,
            retry: 2,
            retryDelay: 3000,
          })

          return (
            <div>
              {/* HERO */}
              <section
                className="relative h-[90vh] flex items-center justify-center text-center text-white"
                style={{
                  backgroundImage:
                    'linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url(/hero-fish.jpg)',
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                }}
              >
                <div>
                  <h1 className="text-4xl md:text-5xl font-bold mb-4">Fresh Fish from Water</h1>
                  <p className="text-lg md:text-xl mb-6">
                    Connecting Fishermen and Buyers Across Tanzania
                  </p>
                  <button
                    onClick={openSignupChoice}
                    className="bg-black hover:bg-gray-800 text-white px-8 py-3 rounded-lg font-semibold transition"
                  >
                    Get Started
                  </button>
                </div>
              </section>

              {/* FEATURES */}
              <section className="flex flex-wrap justify-center gap-6 -mt-12 relative z-10 px-4">
                <FeatureCard icon="fa-fish"  title="Fresh Catch"        text="Daily fish supply from local fishermen" />
                <FeatureCard icon="fa-store" title="Market Access"      text="Buyers connect directly with fishermen" />
                <FeatureCard icon="fa-truck" title="Fast Distribution"  text="Efficient delivery and coordination" />
              </section>

              {/* MARKETPLACE — live sellers */}
              <section className="text-center py-16 px-4">
                <h2 className="text-3xl font-bold text-blue-900 mb-2">Verified Sellers Near You</h2>
                <p className="text-gray-500 mb-10">
                  Browse active fish sellers on the platform · updates every 30 s
                </p>

                {isLoading || isFetching ? (
                  <div className="flex flex-wrap justify-center gap-6">
                    {[...Array(3)].map((_, i) => (
                      <div key={i} className="w-64 h-48 bg-gray-100 animate-pulse rounded-2xl" />
                    ))}
                  </div>
                ) : isError ? (
                  <div className="max-w-md mx-auto bg-yellow-50 border border-yellow-200 rounded-xl p-6">
                    <p className="text-yellow-800 font-medium mb-3">
                      Could not reach the backend. Make sure the backend is running and
                      VITE_API_BASE_URL in frontend/.env is correct.
                    </p>
                    <button
                      onClick={() => refetch()}
                      className="bg-blue-700 hover:bg-blue-800 text-white px-5 py-2 rounded-lg font-semibold"
                    >
                      Try Again
                    </button>
                  </div>
                ) : data?.data?.length ? (
                  <div className="flex flex-wrap justify-center gap-6">
                    {data.data.map((seller) => (
                      <SellerCard key={seller.id} seller={seller} />
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-400">No active sellers yet — be the first to join!</p>
                )}
              </section>

              {/* ABOUT */}
              <section className="bg-blue-700 text-white text-center py-16 px-6">
                <h2 className="text-3xl font-bold mb-4">About the System</h2>
                <p className="max-w-2xl mx-auto leading-relaxed">
                  This system is designed to improve fish market access and supply coordination
                  in Tanzania. It connects fishermen directly with buyers, reduces middlemen, and
                  ensures efficient distribution.
                </p>
              </section>

              {/* WHY CHOOSE US */}
              <section className="bg-gray-50 text-center py-16 px-4">
                <h2 className="text-3xl font-bold text-blue-900 mb-10">Why Choose Our System?</h2>
                <div className="flex flex-wrap justify-center gap-6">
                  <FeatureCard icon="fa-bolt"         title="Fast Access"     text="Quick connection between fishermen and buyers" />
                  <FeatureCard icon="fa-fish"         title="Fresh Fish"      text="Direct supply from local fishermen" />
                  <FeatureCard icon="fa-check-circle" title="Reliable System" text="Efficient coordination and delivery" />
                </div>
              </section>

              {/* CONTACT */}
              <footer className="bg-gray-900 text-white text-center py-10 px-4">
                <h2 className="text-2xl font-bold mb-3">Contact Us</h2>
                <p>Email: fishmarket@gmail.com</p>
                <p>Phone: +255 710 491 613 / +255 616 421 613</p>
              </footer>
            </div>
          )
        }

        function FeatureCard({ icon, title, text }) {
          return (
            <div className="bg-white rounded-2xl shadow-lg p-6 w-56 text-center hover:-translate-y-1 transition">
              <i className={`fas ${icon} text-3xl text-blue-600 mb-3`} />
              <h3 className="font-bold text-blue-900 mb-1">{title}</h3>
              <p className="text-sm text-gray-500">{text}</p>
            </div>
          )
        }
    """)

    # ── SellerPage — polls every 20 s + correct image resolution
    backup("frontend/src/pages/market/SellerPage.jsx")
    write("frontend/src/pages/market/SellerPage.jsx", r"""
        import { useState } from 'react'
        import { useParams } from 'react-router-dom'
        import { useQuery } from '@tanstack/react-query'
        import { Fish, Building2, MapPin } from 'lucide-react'
        import { getSeller } from '../../api/sellers'
        import { resolveImage } from '../../api/client'
        import { useAuthStore } from '../../store/authStore'
        import { formatTsh } from '../../utils/currency'
        import OrderModal from '../../components/orders/OrderModal'

        export default function SellerPage() {
          const { id } = useParams()
          const { user } = useAuthStore()
          const [orderItem, setOrderItem] = useState(null)

          const { data, isLoading } = useQuery({
            queryKey: ['seller', id],
            queryFn: () => getSeller(id).then((r) => r.data),
            refetchInterval: 20000,     // stocks + agencies refresh every 20 s
            staleTime: 0,
          })

          if (isLoading) return <div className="p-8">Loading seller…</div>

          const { seller, stocks, agencies } = data

          return (
            <div className="container mx-auto px-4 py-8">
              {/* Seller Hero */}
              <div className="bg-white rounded-2xl shadow p-6 mb-8 flex gap-6 items-center">
                {resolveImage(seller.brand_logo) ? (
                  <img
                    src={resolveImage(seller.brand_logo)}
                    className="w-24 h-24 rounded-full object-cover border-4 border-blue-200"
                    alt={seller.name}
                  />
                ) : (
                  <div className="w-24 h-24 rounded-full bg-blue-100 flex items-center justify-center">
                    <Fish className="w-10 h-10 text-blue-600" />
                  </div>
                )}
                <div>
                  <h1 className="text-2xl font-bold text-blue-900">{seller.name}</h1>
                  <p className="text-gray-500 flex items-center gap-1.5">
                    <Building2 className="w-4 h-4" /> {seller.office_address}
                  </p>
                  <p className="text-gray-500 flex items-center gap-1.5">
                    <MapPin className="w-4 h-4" /> {seller.location_address}
                  </p>
                  {seller.bio && <p className="text-gray-600 mt-2">{seller.bio}</p>}
                </div>
              </div>

              {/* Delivery Agencies */}
              {agencies?.length > 0 && (
                <div className="mb-8">
                  <h2 className="text-lg font-bold text-blue-800 mb-3">Delivery Partners</h2>
                  <div className="flex flex-wrap gap-3">
                    {agencies.map((a) => (
                      <span key={a.id} className="bg-blue-50 text-blue-700 px-3 py-1 rounded-full text-sm">
                        {a.agency_name} · {a.area_covered}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Fish Stock Grid */}
              <h2 className="text-xl font-bold text-blue-800 mb-4">
                Available Fish
                <span className="text-sm font-normal text-gray-400 ml-2">· live, refreshes every 20 s</span>
              </h2>

              {stocks?.length ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
                  {stocks.map((stock) => (
                    <div key={stock.id} className="bg-white rounded-xl shadow p-4">
                      {resolveImage(stock.image) && (
                        <img
                          src={resolveImage(stock.image)}
                          className="w-full h-36 object-cover rounded-lg mb-3"
                          alt={stock.fish_name}
                        />
                      )}
                      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                        {stock.category?.name}
                      </span>
                      <h3 className="font-semibold text-blue-900 mt-1">{stock.fish_name}</h3>
                      <p className="text-gray-600 text-sm">{stock.quantity_kg} kg available</p>
                      <p className="text-blue-700 font-bold">{formatTsh(stock.price_per_kg)} / kg</p>
                      {user && (
                        <button
                          onClick={() => setOrderItem({ stock, seller, agencies })}
                          className="mt-3 w-full bg-blue-600 text-white py-1.5 rounded-lg hover:bg-blue-700 text-sm"
                        >
                          Order Now
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-center py-10">No active stock available from this seller.</p>
              )}

              {orderItem && (
                <OrderModal data={orderItem} onClose={() => setOrderItem(null)} />
              )}
            </div>
          )
        }
    """)

    # ── SellerCard component — fix image resolution
    backup("frontend/src/components/sellers/SellerCard.jsx")
    seller_card_path = p("frontend/src/components/sellers/SellerCard.jsx")
    with open(seller_card_path, "r", encoding="utf-8") as f:
        sc = f.read()
    # Replace any /storage/ or data: image pattern with resolveImage
    if "resolveImage" not in sc:
        sc_new = "import { resolveImage } from '../../api/client'\n" + sc
        # Replace the img src patterns
        import re
        sc_new = re.sub(
            r"src=\{seller\.brand_logo\.startsWith\('data:'\)\s*\?\s*seller\.brand_logo\s*:\s*`/storage/\$\{seller\.brand_logo\}`\}",
            "src={resolveImage(seller.brand_logo)}",
            sc_new,
        )
        with open(seller_card_path, "w", encoding="utf-8") as f:
            f.write(sc_new)
        print("  ✔  frontend/src/components/sellers/SellerCard.jsx (image fix)")
    else:
        print("  –  SellerCard already uses resolveImage, skipped")


# ─────────────────────────────────────────────────────────────────────────────
# 5. VITE CONFIG — proxy to local backend by default
# ─────────────────────────────────────────────────────────────────────────────

def patch_vite_config():
    print("\n[5/5] Patching vite.config.js…")
    backup("frontend/vite.config.js")
    write("frontend/vite.config.js", r"""
        import { defineConfig } from 'vite'
        import react from '@vitejs/plugin-react'
        import tailwindcss from '@tailwindcss/vite'

        // https://vite.dev/config/
        export default defineConfig({
          plugins: [react(), tailwindcss()],
          server: {
            port: 5173,
            // Dev proxy: only used when VITE_API_BASE_URL is set to /api
            // (relative URL). When it is a full http:// URL the proxy is
            // bypassed — requests go directly to that origin.
            proxy: {
              '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
              },
              '/storage': {
                target: 'http://localhost:8000',
                changeOrigin: true,
              },
            },
          },
        })
    """)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # Sanity check — must be run from FishMarket root
    if not os.path.isdir(p("frontend")) or not os.path.isdir(p("backend")):
        print("ERROR: Run this script from the FishMarket root directory.")
        print(f"  Current directory: {ROOT}")
        sys.exit(1)

    print("=" * 60)
    print("  FishMarket Patch — local-first, real-time, clean seed")
    print("=" * 60)

    patch_env_files()
    patch_seeder()
    patch_backend()
    patch_frontend()
    patch_vite_config()

    print("\n" + "=" * 60)
    print("  PATCH COMPLETE")
    print("=" * 60)
    print("""
NEXT STEPS
──────────
Backend (first-time setup):
  1. cd backend
  2. cp .env.example .env          # then fill in DB_HOST, DB_DATABASE,
                                   # DB_USERNAME, DB_PASSWORD for your
                                   # local Oracle MySQL instance
  3. php artisan key:generate
  4. php artisan migrate
  5. php artisan db:seed           # creates test admin + prints credentials
  6. php artisan storage:link      # only needed for production disk storage
  7. php artisan serve             # runs on http://localhost:8000

Frontend:
  1. cd frontend
  2. npm install                   # if not already done
  3. (frontend/.env already set to http://localhost:8000/api)
  4. npm run dev                   # runs on http://localhost:5173

Admin login:
  Email   : admin@smartfish.test
  Password: Admin@1234
  (Change immediately after first login)

Optional — customise the admin seed credentials without editing PHP:
  Add to backend/.env:
    ADMIN_EMAIL=youremail@example.com
    ADMIN_PASSWORD=YourStr0ng!Pass

Original files are backed up as *.bak next to each changed file.
""")


if __name__ == "__main__":
    main()
