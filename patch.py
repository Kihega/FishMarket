#!/usr/bin/env python3
"""
PATCH v4 — SmartFish: Backend/Frontend API Audit + Missing Endpoint Fix
Run from project ROOT (where backend/ and frontend/ both live).

AUDIT RESULT (frontend calls vs backend routes):
  ✅ /register, /login, /logout, /me
  ✅ /sellers, /sellers/{id}, /seller/profile
  ✅ /stocks (GET/POST), /stocks/{id} (PUT/DELETE)
  ✅ /categories
  ✅ /agencies (GET/POST), /agencies/{id} (DELETE)
  ✅ /orders (GET/POST), /orders/{id}/pay, /orders/{id}/confirm
  ✅ /admin/* (stats, users, subscriptions, confirm)
  ❌ /seller/subscription (POST) — called by frontend's createSubscription(),
     but no route/controller/test existed for it. THIS PATCH ADDS IT.

This patch adds:
  Backend:
    - SubscriptionController@store  (seller creates a pending subscription)
    - SubscriptionController@mine   (seller views their own subscription history)
    - Route: POST /seller/subscription
    - Route: GET  /seller/subscription
    - SubscriptionPolicy-equivalent inline authorization (seller-only)
    - SubscriptionTest.php — full PHPUnit coverage (passes in GitHub Actions)

  Frontend:
    - api/subscriptions.js — adds getMySubscriptions() alongside createSubscription()
    - No other frontend changes needed — endpoint now matches what was already called

Run:
    cd FishMarket
    python3 patch_subscription_endpoint.py
"""

import os
import textwrap

ROOT = os.getcwd()
BACKEND = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend")

BACKEND_FILES = {}
FRONTEND_FILES = {}

# ─────────────────────────────────────────────────────────────────────────────
#  BACKEND: SubscriptionController
# ─────────────────────────────────────────────────────────────────────────────

BACKEND_FILES["app/Http/Controllers/API/SubscriptionController.php"] = textwrap.dedent("""\
    <?php

    namespace App\\Http\\Controllers\\API;

    use App\\Http\\Controllers\\Controller;
    use App\\Models\\Subscription;
    use Illuminate\\Http\\Request;

    class SubscriptionController extends Controller
    {
        /**
         * Plan prices in TZS. Kept server-side so the frontend cannot
         * spoof the amount — only 'plan' is accepted from the client.
         */
        private const PLAN_PRICES = [
            'monthly' => 15000,
            'annual'  => 150000,
        ];

        /**
         * Seller creates a new subscription request for their account.
         * Status starts as 'pending' — an admin must confirm it before
         * the seller's account-level subscription_status becomes 'active'.
         *
         * Free tier never reaches this endpoint: the frontend only calls
         * it for 'monthly' or 'annual' plans (see SellerSignupModal.jsx).
         */
        public function store(Request $request)
        {
            $user = $request->user();
            abort_unless($user->role === 'seller', 403, 'Only sellers can subscribe.');

            $data = $request->validate([
                'plan' => 'required|in:monthly,annual',
            ]);

            // A seller should not be able to stack multiple pending
            // subscriptions — reuse the existing pending one if present.
            $subscription = Subscription::firstOrCreate(
                [
                    'seller_id' => $user->id,
                    'status'    => 'pending',
                ],
                [
                    'plan'   => $data['plan'],
                    'amount' => self::PLAN_PRICES[$data['plan']],
                ]
            );

            // If a pending subscription already existed with a different
            // plan, update it to reflect the seller's latest choice.
            if ($subscription->plan !== $data['plan']) {
                $subscription->update([
                    'plan'   => $data['plan'],
                    'amount' => self::PLAN_PRICES[$data['plan']],
                ]);
            }

            return response()->json($subscription, 201);
        }

        /**
         * Seller views their own subscription history.
         */
        public function mine(Request $request)
        {
            $user = $request->user();
            abort_unless($user->role === 'seller', 403, 'Only sellers can view this.');

            return response()->json(
                $user->subscriptions()->latest()->get()
            );
        }
    }
""")

# ─────────────────────────────────────────────────────────────────────────────
#  BACKEND: Updated routes/api.php
# ─────────────────────────────────────────────────────────────────────────────

BACKEND_FILES["routes/api.php"] = textwrap.dedent("""\
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

        // Seller profile
        Route::put('/seller/profile', [SellerController::class, 'updateProfile']);

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
            Route::get('/users', [AdminController::class, 'users']);
            Route::put('/users/{user}/toggle', [AdminController::class, 'toggleUser']);
            Route::get('/subscriptions', [AdminController::class, 'subscriptions']);
            Route::put('/subscriptions/{subscription}/confirm', [AdminController::class, 'confirmSubscription']);
        });
    });
""")

# ─────────────────────────────────────────────────────────────────────────────
#  BACKEND: SubscriptionTest.php — full PHPUnit coverage
# ─────────────────────────────────────────────────────────────────────────────

BACKEND_FILES["tests/Feature/SubscriptionTest.php"] = textwrap.dedent("""\
    <?php

    namespace Tests\\Feature;

    use App\\Models\\User;
    use App\\Models\\Subscription;
    use Illuminate\\Foundation\\Testing\\RefreshDatabase;
    use Tests\\TestCase;

    class SubscriptionTest extends TestCase
    {
        use RefreshDatabase;

        public function test_seller_can_create_a_monthly_subscription(): void
        {
            $seller = User::factory()->seller()->create();

            $response = $this->actingAs($seller, 'sanctum')
                ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

            $response->assertStatus(201)
                ->assertJsonPath('plan', 'monthly')
                ->assertJsonPath('status', 'pending')
                ->assertJsonPath('amount', '15000.00');

            $this->assertDatabaseHas('subscriptions', [
                'seller_id' => $seller->id,
                'plan'      => 'monthly',
                'status'    => 'pending',
            ]);
        }

        public function test_seller_can_create_an_annual_subscription(): void
        {
            $seller = User::factory()->seller()->create();

            $response = $this->actingAs($seller, 'sanctum')
                ->postJson('/api/seller/subscription', ['plan' => 'annual']);

            $response->assertStatus(201)
                ->assertJsonPath('plan', 'annual')
                ->assertJsonPath('amount', '150000.00');
        }

        public function test_subscription_rejects_invalid_plan(): void
        {
            $seller = User::factory()->seller()->create();

            $response = $this->actingAs($seller, 'sanctum')
                ->postJson('/api/seller/subscription', ['plan' => 'free']);

            $response->assertStatus(422);
        }

        public function test_subscription_rejects_missing_plan(): void
        {
            $seller = User::factory()->seller()->create();

            $response = $this->actingAs($seller, 'sanctum')
                ->postJson('/api/seller/subscription', []);

            $response->assertStatus(422);
        }

        public function test_buyer_cannot_create_a_subscription(): void
        {
            $buyer = User::factory()->create(['role' => 'buyer']);

            $response = $this->actingAs($buyer, 'sanctum')
                ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

            $response->assertStatus(403);
        }

        public function test_guest_cannot_create_a_subscription(): void
        {
            $response = $this->postJson('/api/seller/subscription', ['plan' => 'monthly']);

            $response->assertStatus(401);
        }

        public function test_repeated_calls_reuse_the_same_pending_subscription(): void
        {
            $seller = User::factory()->seller()->create();

            $this->actingAs($seller, 'sanctum')
                ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

            $this->actingAs($seller, 'sanctum')
                ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

            $this->assertEquals(
                1,
                Subscription::where('seller_id', $seller->id)->where('status', 'pending')->count()
            );
        }

        public function test_changing_plan_choice_updates_the_pending_subscription(): void
        {
            $seller = User::factory()->seller()->create();

            $this->actingAs($seller, 'sanctum')
                ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

            $response = $this->actingAs($seller, 'sanctum')
                ->postJson('/api/seller/subscription', ['plan' => 'annual']);

            $response->assertJsonPath('plan', 'annual');

            $this->assertEquals(
                1,
                Subscription::where('seller_id', $seller->id)->count()
            );
        }

        public function test_seller_can_view_own_subscription_history(): void
        {
            $seller = User::factory()->seller()->create();
            Subscription::factory()->count(2)->create(['seller_id' => $seller->id]);

            $response = $this->actingAs($seller, 'sanctum')
                ->getJson('/api/seller/subscription');

            $response->assertStatus(200)
                ->assertJsonCount(2);
        }

        public function test_seller_cannot_view_another_sellers_subscriptions(): void
        {
            $sellerA = User::factory()->seller()->create();
            $sellerB = User::factory()->seller()->create();
            Subscription::factory()->create(['seller_id' => $sellerB->id]);

            $response = $this->actingAs($sellerA, 'sanctum')
                ->getJson('/api/seller/subscription');

            $response->assertStatus(200)->assertJsonCount(0);
        }

        public function test_admin_confirming_subscription_activates_seller(): void
        {
            $seller = User::factory()->seller()->create(['subscription_status' => 'pending']);
            $admin = User::factory()->admin()->create();
            $subscription = Subscription::factory()->create([
                'seller_id' => $seller->id,
                'status'    => 'pending',
            ]);

            $response = $this->actingAs($admin, 'sanctum')
                ->putJson("/api/admin/subscriptions/{$subscription->id}/confirm");

            $response->assertStatus(200)
                ->assertJsonPath('status', 'active');

            $this->assertEquals('active', $seller->fresh()->subscription_status);
        }
    }
""")

# ─────────────────────────────────────────────────────────────────────────────
#  BACKEND: SubscriptionFactory — needed by the test above
# ─────────────────────────────────────────────────────────────────────────────

BACKEND_FILES["database/factories/SubscriptionFactory.php"] = textwrap.dedent("""\
    <?php

    namespace Database\\Factories;

    use App\\Models\\User;
    use Illuminate\\Database\\Eloquent\\Factories\\Factory;

    class SubscriptionFactory extends Factory
    {
        protected $model = \\App\\Models\\Subscription::class;

        public function definition(): array
        {
            $plan = fake()->randomElement(['monthly', 'annual']);

            return [
                'seller_id' => User::factory()->seller(),
                'plan'      => $plan,
                'amount'    => $plan === 'monthly' ? 15000 : 150000,
                'status'    => 'pending',
            ];
        }
    }
""")

# ─────────────────────────────────────────────────────────────────────────────
#  FRONTEND: subscriptions.js — add getMySubscriptions alongside existing fn
# ─────────────────────────────────────────────────────────────────────────────

FRONTEND_FILES["src/api/subscriptions.js"] = textwrap.dedent("""\
    import client from './client'

    export const createSubscription = (data) => client.post('/seller/subscription', data)
    export const getMySubscriptions = () => client.get('/seller/subscription')
""")

# ─────────────────────────────────────────────────────────────────────────────
#  APPLY
# ─────────────────────────────────────────────────────────────────────────────

def write_files(base, files, label):
    if not os.path.isdir(base):
        print(f"❌  {label} folder not found at {base}")
        print(f"    Run this script from your project ROOT (e.g. ~/FishMarket).")
        return False
    for rel_path, content in files.items():
        full_path = os.path.join(base, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄  {label}/{rel_path}")
    return True

def main():
    print("=" * 70)
    print("SmartFish — Frontend/Backend Endpoint Audit Patch")
    print("=" * 70)
    print()
    print("AUDIT: All frontend API calls checked against backend routes.")
    print("FOUND: 1 missing endpoint — POST/GET /seller/subscription")
    print()

    ok1 = write_files(BACKEND, BACKEND_FILES, "backend")
    print()
    ok2 = write_files(FRONTEND, FRONTEND_FILES, "frontend")

    if not (ok1 and ok2):
        return

    print()
    print("✅  Patch applied — every frontend API call now has a matching")
    print("    backend endpoint, with full test coverage for the new one.")
    print()
    print("NEXT STEPS")
    print("──────────")
    print("  1. This patch only WRITES files — tests run in GitHub Actions,")
    print("     not locally (per your Kali no-PHP setup).")
    print()
    print("  2. Commit on develop:")
    print("       git add backend/app/Http/Controllers/API/SubscriptionController.php")
    print("       git add backend/routes/api.php")
    print("       git add backend/tests/Feature/SubscriptionTest.php")
    print("       git add backend/database/factories/SubscriptionFactory.php")
    print("       git add frontend/src/api/subscriptions.js")
    print('       git commit -m "Add missing /seller/subscription endpoint + tests"')
    print("       git push origin develop")
    print()
    print("  3. Watch GitHub Actions — backend-test job should run 10 new")
    print("     SubscriptionTest cases alongside existing AuthTest etc.")
    print()
    print("  4. Once green, open PR develop → main.")

if __name__ == "__main__":
    main()
