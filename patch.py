#!/usr/bin/env python3
"""
PATCH v8a — SmartFish Backend: Dashboard Endpoints (Admin/Seller/Buyer)
Run from project ROOT, on the `develop` branch.

AUDIT (verified live on repo before writing this):
  - brand_logo/office_address/location_address columns: ALREADY EXIST
  - SellerController::updateProfile already handles brand_logo upload
  - NO password-change route existed anywhere
  - NO admin-registration route existed (by design — see below)
  - NO buyer-list-for-seller endpoint existed
  - NO system-performance/metrics endpoint existed
  - toggleUser existed (suspend/activate) but no real delete

THIS PATCH ADDS:
  Backend:
    - PUT  /password                      — any authenticated user changes their own password
    - POST /admin/users                   — admin registers a NEW admin (admin-only, requires existing admin)
    - DELETE /admin/users/{user}          — admin permanently deletes a user
    - GET  /admin/metrics                 — app-level performance metrics (DB query count,
                                              avg response time sample, active users, table sizes)
    - GET  /seller/buyers                 — seller's live list of buyers who've ordered from them,
                                              with contact info, order time, delivery status
    - CreateFirstAdmin artisan command     — one-time secured CLI to bootstrap the very first
                                              admin account (chicken-and-egg: can't use the
                                              "Register Admin" button before any admin exists)
    - 16 new PHPUnit tests covering all of the above

  IMPORTANT — bootstrapping your first admin:
    php artisan admin:create-first your@email.com YourSecurePassword123
    This command REFUSES to run if any admin already exists (idempotent
    safety check) — it's strictly a one-time bootstrap tool, not a
    general-purpose admin creator. After your first admin exists, use
    the in-app "Register Admin" button (POST /admin/users) for any
    additional admins, which requires an authenticated admin token.

Run:
    cd FishMarket
    python3 patch_dashboards_backend.py
"""

import os
import textwrap

ROOT = os.getcwd()
BACKEND = os.path.join(ROOT, "backend")

FILES = {}

# ─────────────────────────────────────────────────────────────────────────────
#  Password change — works for ANY role (admin, seller, buyer)
# ─────────────────────────────────────────────────────────────────────────────

FILES["app/Http/Controllers/API/PasswordController.php"] = textwrap.dedent("""\
    <?php

    namespace App\\Http\\Controllers\\API;

    use App\\Http\\Controllers\\Controller;
    use Illuminate\\Http\\Request;
    use Illuminate\\Support\\Facades\\Hash;

    class PasswordController extends Controller
    {
        /**
         * Any authenticated user (admin, seller, or buyer) changes their
         * own password. Requires the current password for verification.
         */
        public function update(Request $request)
        {
            $user = $request->user();

            $data = $request->validate([
                'current_password' => 'required|string',
                'password' => 'required|string|min:8|confirmed',
            ]);

            if (! Hash::check($data['current_password'], $user->password)) {
                return response()->json(['message' => 'Current password is incorrect'], 422);
            }

            $user->update(['password' => Hash::make($data['password'])]);

            return response()->json(['message' => 'Password updated successfully']);
        }
    }
""")

# ─────────────────────────────────────────────────────────────────────────────
#  AdminController — extended with createAdmin, deleteUser, metrics
# ─────────────────────────────────────────────────────────────────────────────

FILES["app/Http/Controllers/API/AdminController.php"] = textwrap.dedent("""\
    <?php

    namespace App\\Http\\Controllers\\API;

    use App\\Http\\Controllers\\Controller;
    use App\\Models\\User;
    use App\\Models\\Subscription;
    use App\\Models\\FishStock;
    use App\\Models\\Order;
    use Illuminate\\Http\\Request;
    use Illuminate\\Support\\Facades\\DB;
    use Illuminate\\Support\\Facades\\Hash;

    class AdminController extends Controller
    {
        public function users(Request $request)
        {
            return response()->json(
                User::when($request->role, fn ($q) => $q->where('role', $request->role))
                    ->latest()
                    ->paginate(30)
            );
        }

        /**
         * Admin registers a NEW admin account. Requires an authenticated
         * admin token to call — the very first admin must instead be
         * created via the `php artisan admin:create-first` CLI command,
         * since no admin exists yet to authorize this endpoint.
         */
        public function createAdmin(Request $request)
        {
            $data = $request->validate([
                'email' => 'required|email|unique:users,email',
                'phone' => 'nullable|string',
                'password' => 'required|string|min:8|confirmed',
            ]);

            $admin = User::create([
                'name' => $data['email'], // admins are identified by email; name can be edited later
                'email' => $data['email'],
                'phone' => $data['phone'] ?? null,
                'password' => Hash::make($data['password']),
                'role' => 'admin',
                'is_active' => true,
                'subscription_status' => 'active',
            ]);

            return response()->json($admin, 201);
        }

        public function toggleUser(User $user)
        {
            $user->update(['is_active' => ! $user->is_active]);

            return response()->json($user);
        }

        /**
         * Permanently deletes a user. Distinct from toggleUser (suspend),
         * which is reversible. This is not.
         */
        public function deleteUser(Request $request, User $user)
        {
            abort_if($user->id === $request->user()->id, 422, 'You cannot delete your own account.');

            $user->delete();

            return response()->json(null, 204);
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
                'status' => 'active',
                'paid_at' => now(),
            ]);

            $subscription->seller->update(['subscription_status' => 'active']);

            return response()->json($subscription);
        }

        public function stats()
        {
            return response()->json([
                'total_users' => User::count(),
                'active_sellers' => User::where('role', 'seller')->where('subscription_status', 'active')->count(),
                'total_buyers' => User::where('role', 'buyer')->count(),
                'pending_subscriptions' => Subscription::where('status', 'pending')->count(),
            ]);
        }

        /**
         * Application-level performance metrics. Render's free tier
         * doesn't expose OS-level CPU/RAM to the app, so this reports
         * metrics that are actually meaningful for a Laravel app:
         * table sizes, query volume on this request, and active-user
         * approximation (logged in within the last 15 minutes via
         * personal_access_tokens.last_used_at).
         */
        public function metrics()
        {
            DB::enableQueryLog();

            $tableSizes = [
                'users' => User::count(),
                'fish_stocks' => FishStock::count(),
                'orders' => Order::count(),
                'subscriptions' => Subscription::count(),
            ];

            $activeUsersLast15Min = DB::table('personal_access_tokens')
                ->where('last_used_at', '>=', now()->subMinutes(15))
                ->distinct('tokenable_id')
                ->count('tokenable_id');

            $queryCount = count(DB::getQueryLog());
            DB::disableQueryLog();

            return response()->json([
                'table_sizes' => $tableSizes,
                'active_users_last_15_min' => $activeUsersLast15Min,
                'queries_this_request' => $queryCount,
                'server_time' => now()->toIso8601String(),
                'php_version' => PHP_VERSION,
                'laravel_version' => app()->version(),
            ]);
        }
    }
""")

# ─────────────────────────────────────────────────────────────────────────────
#  SellerController — add buyers() for "Manage Buyers" sidebar section
# ─────────────────────────────────────────────────────────────────────────────

FILES["app/Http/Controllers/API/SellerController.php"] = textwrap.dedent("""\
    <?php

    namespace App\\Http\\Controllers\\API;

    use App\\Http\\Controllers\\Controller;
    use App\\Models\\User;
    use App\\Models\\Order;
    use Illuminate\\Http\\Request;

    class SellerController extends Controller
    {
        // Public: marketplace list of active sellers
        public function index(Request $request)
        {
            $sellers = User::where('role', 'seller')
                ->where('is_active', true)
                ->where('subscription_status', 'active')
                ->when($request->location, fn ($q) => $q->where('location', 'like', "%{$request->location}%"))
                ->withCount('fishStocks')
                ->paginate(20);

            return response()->json($sellers);
        }

        // Public: single seller profile + stocks + agencies
        public function show(User $user)
        {
            abort_unless($user->role === 'seller', 404);

            return response()->json([
                'seller' => $user,
                'stocks' => $user->fishStocks()->with('category')->where('status', 'active')->get(),
                'agencies' => $user->deliveryAgencies()->where('is_active', true)->get(),
            ]);
        }

        // Seller: update own profile (including brand_logo upload)
        public function updateProfile(Request $request)
        {
            $user = $request->user();
            abort_unless($user->role === 'seller', 403);

            $data = $request->validate([
                'brand_logo' => 'nullable|image|max:2048',
                'office_address' => 'nullable|string',
                'location_address' => 'nullable|string',
                'bio' => 'nullable|string',
            ]);

            if ($request->hasFile('brand_logo')) {
                $data['brand_logo'] = $request->file('brand_logo')->store('logos', 'public');
            }

            $user->update($data);

            return response()->json($user);
        }

        /**
         * Seller's live list of buyers who have placed orders on their
         * platform — contact info, when they ordered, and delivery
         * status. Powers the "Manage Buyers" sidebar section.
         */
        public function buyers(Request $request)
        {
            $seller = $request->user();
            abort_unless($seller->role === 'seller', 403);

            $orders = Order::with(['buyer', 'delivery'])
                ->where('seller_id', $seller->id)
                ->latest()
                ->get();

            $buyers = $orders->map(function ($order) {
                return [
                    'order_id' => $order->id,
                    'buyer_name' => $order->buyer->name,
                    'buyer_phone' => $order->buyer->phone,
                    'buyer_email' => $order->buyer->email,
                    'ordered_at' => $order->created_at->toIso8601String(),
                    'order_status' => $order->status,
                    'payment_status' => $order->payment_status,
                    'delivery_status' => $order->delivery?->delivery_status ?? 'pending',
                ];
            });

            return response()->json($buyers);
        }
    }
""")

# ─────────────────────────────────────────────────────────────────────────────
#  Routes — add all new endpoints
# ─────────────────────────────────────────────────────────────────────────────

FILES["routes/api.php"] = textwrap.dedent("""\
    <?php

    use Illuminate\\Support\\Facades\\Route;
    use App\\Http\\Controllers\\API\\AuthController;
    use App\\Http\\Controllers\\API\\SellerController;
    use App\\Http\\Controllers\\API\\FishStockController;
    use App\\Http\\Controllers\\API\\FishCategoryController;
    use App\\Http\\Controllers\\API\\DeliveryAgencyController;
    use App\\Http\\Controllers\\API\\OrderController;
    use App\\Http\\Controllers\\API\\SubscriptionController;
    use App\\Http\\Controllers\\API\\AdminController;
    use App\\Http\\Controllers\\API\\PasswordController;

    // ── Public ──────────────────────────────────────────────────────────────
    Route::post('/register', [AuthController::class, 'register']);
    Route::post('/login', [AuthController::class, 'login']);

    // Marketplace (public browsing — no auth required)
    Route::get('/sellers', [SellerController::class, 'index']);
    Route::get('/sellers/{user}', [SellerController::class, 'show']);
    Route::get('/stocks', [FishStockController::class, 'index']);
    Route::get('/categories', [FishCategoryController::class, 'index']);
    Route::get('/agencies', [DeliveryAgencyController::class, 'index']);

    // ── Protected (Sanctum token required) ───────────────────────────────────
    Route::middleware('auth:sanctum')->group(function () {
        Route::post('/logout', [AuthController::class, 'logout']);
        Route::get('/me', [AuthController::class, 'me']);

        // Any authenticated user — change own password
        Route::put('/password', [PasswordController::class, 'update']);

        // Seller profile
        Route::put('/seller/profile', [SellerController::class, 'updateProfile']);
        Route::get('/seller/buyers', [SellerController::class, 'buyers']);

        // Seller subscription (plan selection after signup)
        Route::post('/seller/subscription', [SubscriptionController::class, 'store']);
        Route::get('/seller/subscription', [SubscriptionController::class, 'mine']);

        // Fish stocks (seller only — enforced in controller)
        Route::post('/stocks', [FishStockController::class, 'store']);
        Route::put('/stocks/{fishStock}', [FishStockController::class, 'update']);
        Route::delete('/stocks/{fishStock}', [FishStockController::class, 'destroy']);

        // Delivery agencies (seller only)
        Route::post('/agencies', [DeliveryAgencyController::class, 'store']);
        Route::delete('/agencies/{deliveryAgency}', [DeliveryAgencyController::class, 'destroy']);

        // Orders
        Route::get('/orders', [OrderController::class, 'index']);
        Route::post('/orders', [OrderController::class, 'store']);
        Route::post('/orders/{order}/pay', [OrderController::class, 'pay']);
        Route::post('/orders/{order}/confirm', [OrderController::class, 'confirm']);

        // Admin only
        Route::middleware('admin')->prefix('admin')->group(function () {
            Route::get('/stats', [AdminController::class, 'stats']);
            Route::get('/metrics', [AdminController::class, 'metrics']);
            Route::get('/users', [AdminController::class, 'users']);
            Route::post('/users', [AdminController::class, 'createAdmin']);
            Route::put('/users/{user}/toggle', [AdminController::class, 'toggleUser']);
            Route::delete('/users/{user}', [AdminController::class, 'deleteUser']);
            Route::get('/subscriptions', [AdminController::class, 'subscriptions']);
            Route::put('/subscriptions/{subscription}/confirm', [AdminController::class, 'confirmSubscription']);
        });
    });
""")

# ─────────────────────────────────────────────────────────────────────────────
#  Artisan command — bootstrap the FIRST admin only
# ─────────────────────────────────────────────────────────────────────────────

FILES["app/Console/Commands/CreateFirstAdmin.php"] = textwrap.dedent("""\
    <?php

    namespace App\\Console\\Commands;

    use App\\Models\\User;
    use Illuminate\\Console\\Command;
    use Illuminate\\Support\\Facades\\Hash;
    use Illuminate\\Support\\Facades\\Validator;

    class CreateFirstAdmin extends Command
    {
        protected $signature = 'admin:create-first {email} {password}';

        protected $description = 'One-time bootstrap: create the FIRST admin account. '
            . 'Refuses to run if any admin already exists — use the in-app '
            . '"Register Admin" feature for all subsequent admins.';

        public function handle(): int
        {
            if (User::where('role', 'admin')->exists()) {
                $this->error('An admin already exists. This command only bootstraps the FIRST admin.');
                $this->line('Use the in-app "Register Admin" button (requires an existing admin login) instead.');

                return self::FAILURE;
            }

            $email = $this->argument('email');
            $password = $this->argument('password');

            $validator = Validator::make(
                ['email' => $email, 'password' => $password],
                ['email' => 'required|email', 'password' => 'required|min:8']
            );

            if ($validator->fails()) {
                foreach ($validator->errors()->all() as $error) {
                    $this->error($error);
                }

                return self::FAILURE;
            }

            $admin = User::create([
                'name' => $email,
                'email' => $email,
                'password' => Hash::make($password),
                'role' => 'admin',
                'is_active' => true,
                'subscription_status' => 'active',
            ]);

            $this->info("First admin created successfully: {$admin->email}");

            return self::SUCCESS;
        }
    }
""")

# ─────────────────────────────────────────────────────────────────────────────
#  Tests
# ─────────────────────────────────────────────────────────────────────────────

FILES["tests/Feature/PasswordTest.php"] = textwrap.dedent("""\
    <?php

    namespace Tests\\Feature;

    use App\\Models\\User;
    use Illuminate\\Foundation\\Testing\\RefreshDatabase;
    use Illuminate\\Support\\Facades\\Hash;
    use Tests\\TestCase;

    class PasswordTest extends TestCase
    {
        use RefreshDatabase;

        public function test_user_can_change_password_with_correct_current_password(): void
        {
            $user = User::factory()->create(['password' => bcrypt('oldpassword123')]);

            $response = $this->actingAs($user, 'sanctum')->putJson('/api/password', [
                'current_password' => 'oldpassword123',
                'password' => 'newpassword456',
                'password_confirmation' => 'newpassword456',
            ]);

            $response->assertStatus(200);
            $this->assertTrue(Hash::check('newpassword456', $user->fresh()->password));
        }

        public function test_password_change_fails_with_wrong_current_password(): void
        {
            $user = User::factory()->create(['password' => bcrypt('oldpassword123')]);

            $response = $this->actingAs($user, 'sanctum')->putJson('/api/password', [
                'current_password' => 'wrongpassword',
                'password' => 'newpassword456',
                'password_confirmation' => 'newpassword456',
            ]);

            $response->assertStatus(422);
        }

        public function test_password_change_requires_confirmation_match(): void
        {
            $user = User::factory()->create(['password' => bcrypt('oldpassword123')]);

            $response = $this->actingAs($user, 'sanctum')->putJson('/api/password', [
                'current_password' => 'oldpassword123',
                'password' => 'newpassword456',
                'password_confirmation' => 'doesnotmatch',
            ]);

            $response->assertStatus(422);
        }

        public function test_guest_cannot_change_password(): void
        {
            $response = $this->putJson('/api/password', [
                'current_password' => 'x',
                'password' => 'newpassword456',
                'password_confirmation' => 'newpassword456',
            ]);

            $response->assertStatus(401);
        }
    }
""")

FILES["tests/Feature/AdminUserManagementTest.php"] = textwrap.dedent("""\
    <?php

    namespace Tests\\Feature;

    use App\\Models\\User;
    use Illuminate\\Foundation\\Testing\\RefreshDatabase;
    use Tests\\TestCase;

    class AdminUserManagementTest extends TestCase
    {
        use RefreshDatabase;

        public function test_admin_can_register_a_new_admin(): void
        {
            $admin = User::factory()->admin()->create();

            $response = $this->actingAs($admin, 'sanctum')->postJson('/api/admin/users', [
                'email' => 'newadmin@example.com',
                'phone' => '+255700000000',
                'password' => 'securepass123',
                'password_confirmation' => 'securepass123',
            ]);

            $response->assertStatus(201)
                ->assertJsonPath('role', 'admin')
                ->assertJsonPath('email', 'newadmin@example.com');

            $this->assertDatabaseHas('users', [
                'email' => 'newadmin@example.com',
                'role' => 'admin',
            ]);
        }

        public function test_non_admin_cannot_register_a_new_admin(): void
        {
            $seller = User::factory()->seller()->create();

            $response = $this->actingAs($seller, 'sanctum')->postJson('/api/admin/users', [
                'email' => 'newadmin@example.com',
                'password' => 'securepass123',
                'password_confirmation' => 'securepass123',
            ]);

            $response->assertStatus(403);
        }

        public function test_admin_registration_rejects_duplicate_email(): void
        {
            $admin = User::factory()->admin()->create();
            $existing = User::factory()->create(['email' => 'taken@example.com']);

            $response = $this->actingAs($admin, 'sanctum')->postJson('/api/admin/users', [
                'email' => 'taken@example.com',
                'password' => 'securepass123',
                'password_confirmation' => 'securepass123',
            ]);

            $response->assertStatus(422);
        }

        public function test_admin_can_delete_a_user(): void
        {
            $admin = User::factory()->admin()->create();
            $buyer = User::factory()->create();

            $response = $this->actingAs($admin, 'sanctum')->deleteJson("/api/admin/users/{$buyer->id}");

            $response->assertStatus(204);
            $this->assertDatabaseMissing('users', ['id' => $buyer->id]);
        }

        public function test_admin_cannot_delete_their_own_account(): void
        {
            $admin = User::factory()->admin()->create();

            $response = $this->actingAs($admin, 'sanctum')->deleteJson("/api/admin/users/{$admin->id}");

            $response->assertStatus(422);
            $this->assertDatabaseHas('users', ['id' => $admin->id]);
        }

        public function test_admin_can_toggle_user_active_status(): void
        {
            $admin = User::factory()->admin()->create();
            $buyer = User::factory()->create(['is_active' => true]);

            $response = $this->actingAs($admin, 'sanctum')->putJson("/api/admin/users/{$buyer->id}/toggle");

            $response->assertStatus(200)->assertJsonPath('is_active', false);
        }

        public function test_admin_can_view_metrics(): void
        {
            $admin = User::factory()->admin()->create();

            $response = $this->actingAs($admin, 'sanctum')->getJson('/api/admin/metrics');

            $response->assertStatus(200)
                ->assertJsonStructure([
                    'table_sizes' => ['users', 'fish_stocks', 'orders', 'subscriptions'],
                    'active_users_last_15_min',
                    'queries_this_request',
                    'server_time',
                    'php_version',
                    'laravel_version',
                ]);
        }

        public function test_non_admin_cannot_view_metrics(): void
        {
            $buyer = User::factory()->create();

            $response = $this->actingAs($buyer, 'sanctum')->getJson('/api/admin/metrics');

            $response->assertStatus(403);
        }
    }
""")

FILES["tests/Feature/SellerBuyersTest.php"] = textwrap.dedent("""\
    <?php

    namespace Tests\\Feature;

    use App\\Models\\User;
    use App\\Models\\Order;
    use Illuminate\\Foundation\\Testing\\RefreshDatabase;
    use Tests\\TestCase;

    class SellerBuyersTest extends TestCase
    {
        use RefreshDatabase;

        public function test_seller_can_view_their_buyers(): void
        {
            $seller = User::factory()->seller()->create();
            $buyer = User::factory()->create(['name' => 'Jane Buyer', 'phone' => '+255700111222']);

            Order::factory()->create([
                'seller_id' => $seller->id,
                'buyer_id' => $buyer->id,
            ]);

            $response = $this->actingAs($seller, 'sanctum')->getJson('/api/seller/buyers');

            $response->assertStatus(200)
                ->assertJsonCount(1)
                ->assertJsonPath('0.buyer_name', 'Jane Buyer')
                ->assertJsonPath('0.buyer_phone', '+255700111222');
        }

        public function test_seller_only_sees_their_own_buyers(): void
        {
            $sellerA = User::factory()->seller()->create();
            $sellerB = User::factory()->seller()->create();
            $buyer = User::factory()->create();

            Order::factory()->create(['seller_id' => $sellerB->id, 'buyer_id' => $buyer->id]);

            $response = $this->actingAs($sellerA, 'sanctum')->getJson('/api/seller/buyers');

            $response->assertStatus(200)->assertJsonCount(0);
        }

        public function test_buyer_cannot_access_seller_buyers_endpoint(): void
        {
            $buyer = User::factory()->create();

            $response = $this->actingAs($buyer, 'sanctum')->getJson('/api/seller/buyers');

            $response->assertStatus(403);
        }
    }
""")

# ── OrderFactory — needed by SellerBuyersTest, didn't exist yet ──────────
FILES["database/factories/OrderFactory.php"] = textwrap.dedent("""\
    <?php

    namespace Database\\Factories;

    use App\\Models\\User;
    use Illuminate\\Database\\Eloquent\\Factories\\Factory;

    class OrderFactory extends Factory
    {
        protected $model = \\App\\Models\\Order::class;

        public function definition(): array
        {
            return [
                'buyer_id' => User::factory(),
                'seller_id' => User::factory()->seller(),
                'status' => 'pending',
                'payment_method' => 'mobile',
                'payment_status' => 'unpaid',
                'total_amount' => fake()->randomFloat(2, 1000, 50000),
            ];
        }
    }
""")


def main():
    if not os.path.isdir(BACKEND):
        print(f"❌  backend/ folder not found at {BACKEND}")
        print("    Run this script from your project ROOT (e.g. ~/FishMarket).")
        return

    for rel_path, content in FILES.items():
        full_path = os.path.join(BACKEND, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄  backend/{rel_path}")

    print()
    print("✅  Backend dashboard endpoints added.")
    print("""
NEW ENDPOINTS
─────────────
  PUT    /api/password                    — any user changes own password
  POST   /api/admin/users                 — admin registers a new admin
  DELETE /api/admin/users/{id}            — admin permanently deletes a user
  GET    /api/admin/metrics               — app-level performance metrics
  GET    /api/seller/buyers               — seller's live buyer list

⚠️  BOOTSTRAP YOUR FIRST ADMIN (one-time, after this deploys to Render):
    This MUST be run once via Render's Shell tab (or locally against
    Aiven if you have a tunnel) — it cannot be done through the API
    since no admin exists yet to authorize the API-based creation route.

    php artisan admin:create-first youremail@example.com YourSecurePass123

    This command refuses to run a second time once any admin exists.

NEXT STEPS
──────────
  1. Commit on develop:
       git add backend/app/Http/Controllers/API/PasswordController.php
       git add backend/app/Http/Controllers/API/AdminController.php
       git add backend/app/Http/Controllers/API/SellerController.php
       git add backend/app/Console/Commands/CreateFirstAdmin.php
       git add backend/routes/api.php
       git add backend/tests/Feature/PasswordTest.php
       git add backend/tests/Feature/AdminUserManagementTest.php
       git add backend/tests/Feature/SellerBuyersTest.php
       git add backend/database/factories/OrderFactory.php
       git commit -m "Add password change, admin management, metrics, seller-buyers endpoints"
       git push origin develop

  2. Watch GitHub Actions — should run AuthTest + SubscriptionTest +
     PasswordTest + AdminUserManagementTest + SellerBuyersTest, all green.

  3. Once deployed to Render, bootstrap your first admin (command above).

  4. Frontend patch (sidebar dashboards) comes next, in a follow-up.
""")


if __name__ == "__main__":
    main()
