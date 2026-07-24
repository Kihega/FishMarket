#!/usr/bin/env python3
"""
patch_19.py

Run from the FishMarket project root (on top of a project that
already has patch_16, patch_17, and patch_18 applied):

    python3 patch_19.py

This patch does TWO things:

  1. REVERTS patch_18 — the delivery-agency / delivery-tracking
     feature removal was a mistake. This restores it exactly as it
     was (delivery partners, delivery address, delivery fee, delivery
     status, buyer's "Confirm Delivery" action) — including the
     database tables — using the project ZIP from that point as the
     reference. Also reverts the buyer-phone-became-mandatory change
     that came with it; phone goes back to optional at registration.

  2. Removes "Manage Sellers" from the admin panel and the seller
     subscription/plan feature behind it entirely (backend + frontend
     + database), since sellers are activated immediately with no
     billing step and this panel has no purpose anymore.

Safe to re-run: every change is guarded so an already-patched project
is left alone instead of being re-applied or corrupted.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND = ROOT / "frontend" / "src"
BACKEND = ROOT / "backend"

FAILS = []


def read(path: Path) -> str:
    if not path.exists():
        FAILS.append(f"MISSING FILE: {path}")
        return ""
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ensure_content(path: Path, done_marker: str, new_content: str, label: str):
    """
    Full-file replace, idempotent: skips if done_marker (something
    only present in the ALREADY-PATCHED / target version) is already
    in the file. Otherwise overwrites the whole file with new_content,
    regardless of what its current content is.
    """
    content = read(path)
    if not content:
        return
    if done_marker in content:
        print(f"  [skip] {label} (already applied) — {path.name}")
        return
    write(path, new_content)
    print(f"  [ok]   {label} — {path.name}")


def create_if_missing(path: Path, content: str, label: str):
    if path.exists():
        print(f"  [skip] {label} (file already exists) — {path.name}")
        return
    write(path, content)
    print(f"  [ok]   {label} — created {path.name}")


def delete_if_exists(path: Path, label: str):
    if not path.exists():
        print(f"  [skip] {label} (already removed) — {path.name}")
        return
    path.unlink()
    print(f"  [ok]   {label} — deleted {path.name}")


# ═══════════════════════════════════════════════════════════════════
# PART A — RESTORE THE DELIVERY-AGENCY FEATURE (revert patch_18)
# ═══════════════════════════════════════════════════════════════════

# ── A1. Database ──────────────────────────────────────────────────
print("\n=== A1. Database — restore delivery tables ===")

delete_if_exists(
    BACKEND / "database" / "migrations" / "2026_07_22_000001_drop_delivery_feature_tables.php",
    "Remove patch_18's drop-tables migration",
)

RESTORE_DELIVERY_TABLES_MIGRATION = """<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Database\\Schema\\Blueprint;
use Illuminate\\Support\\Facades\\Schema;

/**
 * Restores delivery_agencies and order_deliveries — the delivery
 * agency / delivery-tracking feature that a previous patch removed
 * by mistake is back. Guarded with hasTable() so this is safe
 * whether or not that removal migration ever actually ran on a given
 * database.
 *
 * Schema matches the tables' final shape from before they were
 * dropped (i.e. after all of the original create + alter
 * migrations), so no separate "add delivery_fee" / "add
 * delivery_address" follow-up migrations are needed here.
 */
return new class extends Migration
{
    public function up(): void
    {
        if (! Schema::hasTable('delivery_agencies')) {
            Schema::create('delivery_agencies', function (Blueprint $table) {
                $table->id();
                $table->foreignId('seller_id')->constrained('users')->cascadeOnDelete();
                $table->string('agency_name');
                $table->string('contact')->nullable();
                $table->string('area_covered')->nullable();
                $table->decimal('delivery_fee', 10, 2)->default(0);
                $table->boolean('is_active')->default(true);
                $table->timestamps();
            });
        }

        if (! Schema::hasTable('order_deliveries')) {
            Schema::create('order_deliveries', function (Blueprint $table) {
                $table->id();
                $table->foreignId('order_id')->constrained()->cascadeOnDelete();
                $table->foreignId('agency_id')->nullable()
                    ->constrained('delivery_agencies')->nullOnDelete();
                $table->decimal('delivery_fee', 10, 2)->default(0);
                $table->text('delivery_address')->nullable();
                $table->string('delivery_method')->nullable();
                $table->enum('delivery_status', ['pending', 'dispatched', 'delivered'])->default('pending');
                $table->timestamps();
            });
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('order_deliveries');
        Schema::dropIfExists('delivery_agencies');
    }
};
"""
create_if_missing(
    BACKEND / "database" / "migrations" / "2026_07_24_000001_restore_delivery_feature_tables.php",
    RESTORE_DELIVERY_TABLES_MIGRATION,
    "Create restore-delivery-tables migration",
)

# ── A2. Recreate deleted backend files ──────────────────────────────
print("\n=== A2. Recreate delivery-agency backend files ===")

DELIVERY_AGENCY_CONTROLLER = """<?php

namespace App\\Http\\Controllers\\API;

use App\\Http\\Controllers\\Controller;
use App\\Models\\DeliveryAgency;
use Illuminate\\Http\\Request;

class DeliveryAgencyController extends Controller
{
    // Public: agencies belonging to a given seller
    public function index(Request $request)
    {
        $sellerId = $request->seller_id ?? $request->user()?->id;

        if (! $sellerId) {
            return response()->json(['message' => 'seller_id is required'], 422);
        }

        return response()->json(
            DeliveryAgency::where('seller_id', $sellerId)->where('is_active', true)->get()
        );
    }

    // Seller: register a delivery partnership agency
    public function store(Request $request)
    {
        abort_unless($request->user()->role === 'seller', 403);

        $data = $request->validate([
            'agency_name' => 'required|string',
            'contact' => 'nullable|string',
            'area_covered' => 'nullable|string',
            // Every agency may charge a different fee depending on the
            // area it serves, so it's set once here at registration
            // rather than per order.
            'delivery_fee' => 'nullable|numeric|min:0',
        ]);

        // validate() simply omits delivery_fee from $data when it's not
        // sent at all (rather than setting it to null), so without this
        // the column's DB-level default(0) would apply to the actual
        // row, but the in-memory $agency object returned by create()
        // below is never backfilled with that server-side default —
        // Eloquent only re-reads the auto-increment id after an insert,
        // not other columns — so the JSON response would show null
        // even though the database itself correctly stored 0.
        $data['delivery_fee'] = $data['delivery_fee'] ?? 0;

        $agency = $request->user()->deliveryAgencies()->create($data);

        return response()->json($agency, 201);
    }

    // Seller: remove (soft-deactivate) a delivery agency
    public function destroy(Request $request, DeliveryAgency $deliveryAgency)
    {
        abort_unless($deliveryAgency->seller_id === $request->user()->id, 403);
        $deliveryAgency->update(['is_active' => false]);

        return response()->json(null, 204);
    }
}
"""
create_if_missing(
    BACKEND / "app" / "Http" / "Controllers" / "API" / "DeliveryAgencyController.php",
    DELIVERY_AGENCY_CONTROLLER,
    "Recreate DeliveryAgencyController",
)

DELIVERY_AGENCY_MODEL = """<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Database\\Eloquent\\Model;

class DeliveryAgency extends Model
{
    use HasFactory;

    protected $fillable = ['seller_id', 'agency_name', 'contact', 'area_covered', 'delivery_fee', 'is_active'];

    protected function casts(): array
    {
        return [
            'is_active' => 'boolean',
            'delivery_fee' => 'decimal:2',
        ];
    }

    public function seller()
    {
        return $this->belongsTo(User::class, 'seller_id');
    }
}
"""
create_if_missing(
    BACKEND / "app" / "Models" / "DeliveryAgency.php", DELIVERY_AGENCY_MODEL, "Recreate DeliveryAgency model"
)

ORDER_DELIVERY_MODEL = """<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Database\\Eloquent\\Model;

class OrderDelivery extends Model
{
    use HasFactory;

    protected $fillable = [
        'order_id', 'agency_id', 'delivery_fee', 'delivery_address', 'delivery_method', 'delivery_status',
    ];

    protected function casts(): array
    {
        return [
            'delivery_fee' => 'decimal:2',
        ];
    }

    public function order()
    {
        return $this->belongsTo(Order::class);
    }

    public function agency()
    {
        return $this->belongsTo(DeliveryAgency::class, 'agency_id');
    }
}
"""
create_if_missing(
    BACKEND / "app" / "Models" / "OrderDelivery.php", ORDER_DELIVERY_MODEL, "Recreate OrderDelivery model"
)

DELIVERY_AGENCY_FACTORY = """<?php

namespace Database\\Factories;

use App\\Models\\User;
use Illuminate\\Database\\Eloquent\\Factories\\Factory;

class DeliveryAgencyFactory extends Factory
{
    protected $model = \\App\\Models\\DeliveryAgency::class;

    public function definition(): array
    {
        return [
            'seller_id' => User::factory()->seller(),
            'agency_name' => fake()->company().' Delivery',
            'contact' => fake()->phoneNumber(),
            'area_covered' => fake()->city(),
            'is_active' => true,
        ];
    }
}
"""
create_if_missing(
    BACKEND / "database" / "factories" / "DeliveryAgencyFactory.php",
    DELIVERY_AGENCY_FACTORY,
    "Recreate DeliveryAgencyFactory",
)

DELIVERY_AGENCY_TEST = """<?php

namespace Tests\\Feature;

use App\\Models\\DeliveryAgency;
use App\\Models\\User;
use Illuminate\\Foundation\\Testing\\RefreshDatabase;
use Tests\\TestCase;

class DeliveryAgencyTest extends TestCase
{
    use RefreshDatabase;

    public function test_seller_sees_newly_added_agency_in_their_own_list(): void
    {
        $seller = User::factory()->seller()->create();

        $createResponse = $this->actingAs($seller, 'sanctum')->postJson('/api/agencies', [
            'agency_name' => 'Coastal Express',
            'contact' => '0712345678',
            'area_covered' => 'Dar es Salaam',
        ]);
        $createResponse->assertStatus(201);

        $listResponse = $this->actingAs($seller, 'sanctum')->getJson('/api/agencies');

        $listResponse->assertStatus(200)
            ->assertJsonCount(1)
            ->assertJsonPath('0.agency_name', 'Coastal Express');
    }

    public function test_seller_only_sees_their_own_agencies_not_other_sellers(): void
    {
        $seller = User::factory()->seller()->create();
        $otherSeller = User::factory()->seller()->create();

        DeliveryAgency::factory()->create(['seller_id' => $seller->id, 'agency_name' => 'Mine']);
        DeliveryAgency::factory()->create(['seller_id' => $otherSeller->id, 'agency_name' => 'Theirs']);

        $response = $this->actingAs($seller, 'sanctum')->getJson('/api/agencies');

        $response->assertStatus(200)
            ->assertJsonCount(1)
            ->assertJsonPath('0.agency_name', 'Mine');
    }

    public function test_guest_is_rejected_with_401_not_a_silent_empty_list(): void
    {
        $response = $this->getJson('/api/agencies');

        $response->assertStatus(401);
    }

    public function test_seller_can_set_a_delivery_fee_when_registering_an_agency(): void
    {
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')->postJson('/api/agencies', [
            'agency_name' => 'Coastal Express',
            'area_covered' => 'Dar es Salaam',
            'delivery_fee' => 3500,
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('delivery_fee', '3500.00');
    }

    public function test_agency_delivery_fee_defaults_to_zero_when_not_given(): void
    {
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')->postJson('/api/agencies', [
            'agency_name' => 'No Fee Listed',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('delivery_fee', '0.00');
    }

    public function test_newly_added_agency_is_visible_to_buyers_on_the_seller_page(): void
    {
        $seller = User::factory()->seller()->create();

        $this->actingAs($seller, 'sanctum')->postJson('/api/agencies', [
            'agency_name' => 'Lakeside Movers',
        ])->assertStatus(201);

        $publicResponse = $this->getJson("/api/sellers/{$seller->id}");

        $publicResponse->assertStatus(200)
            ->assertJsonPath('agencies.0.agency_name', 'Lakeside Movers');
    }
}
"""
create_if_missing(
    BACKEND / "tests" / "Feature" / "DeliveryAgencyTest.php", DELIVERY_AGENCY_TEST, "Recreate DeliveryAgencyTest"
)

# ── A3. Restore routes ───────────────────────────────────────────────
print("\n=== A3. Restore /agencies + confirm-delivery routes ===")
# (Subscription routes are removed here too — see Part B — so this
# file is written once, in its final combined state.)

ROUTES_API_FINAL = """<?php

use Illuminate\\Support\\Facades\\Route;
use App\\Http\\Controllers\\API\\AuthController;
use App\\Http\\Controllers\\API\\SellerController;
use App\\Http\\Controllers\\API\\FishStockController;
use App\\Http\\Controllers\\API\\FishCategoryController;
use App\\Http\\Controllers\\API\\DeliveryAgencyController;
use App\\Http\\Controllers\\API\\OrderController;
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

// ── Protected (Sanctum token required) ───────────────────────────────────
Route::middleware('auth:sanctum')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/me', [AuthController::class, 'me']);

    // Any authenticated user — change own password
    Route::put('/password', [PasswordController::class, 'update']);

    // Seller profile
    Route::put('/seller/profile', [SellerController::class, 'updateProfile']);
    Route::get('/seller/buyers', [SellerController::class, 'buyers']);

    // Fish stocks (seller only — enforced in controller)
    // /seller/stocks is the seller's OWN scoped list (used by the
    // dashboard) — distinct from the public /stocks marketplace feed.
    Route::get('/seller/stocks', [FishStockController::class, 'mine']);
    Route::post('/stocks', [FishStockController::class, 'store']);
    Route::put('/stocks/{fishStock}', [FishStockController::class, 'update']);
    Route::delete('/stocks/{fishStock}', [FishStockController::class, 'destroy']);

    // Delivery agencies (seller only)
    Route::get('/agencies', [DeliveryAgencyController::class, 'index']);
    Route::post('/agencies', [DeliveryAgencyController::class, 'store']);
    Route::delete('/agencies/{deliveryAgency}', [DeliveryAgencyController::class, 'destroy']);

    // Orders
    Route::get('/orders', [OrderController::class, 'index']);
    Route::post('/orders', [OrderController::class, 'store']);
    Route::post('/orders/{order}/pay', [OrderController::class, 'pay']);
    Route::post('/orders/{order}/confirm', [OrderController::class, 'confirm']);
    Route::post('/orders/{order}/cancel', [OrderController::class, 'cancel']);
    Route::post('/orders/{order}/confirm-delivery', [OrderController::class, 'confirmDelivery']);

    // Admin only
    Route::middleware('admin')->prefix('admin')->group(function () {
        Route::get('/stats', [AdminController::class, 'stats']);
        Route::get('/metrics', [AdminController::class, 'metrics']);
        Route::get('/users', [AdminController::class, 'users']);
        Route::post('/users', [AdminController::class, 'createAdmin']);
        Route::put('/users/{user}/toggle', [AdminController::class, 'toggleUser']);
        Route::delete('/users/{user}', [AdminController::class, 'deleteUser']);
    });
});
"""
ensure_content(
    BACKEND / "routes" / "api.php",
    "DeliveryAgencyController",
    ROUTES_API_FINAL,
    "Restore /agencies + confirm-delivery routes, remove subscription routes",
)

# ── A4. Restore model relations ─────────────────────────────────────
print("\n=== A4. Restore delivery relations on models ===")

USER_MODEL_FINAL = """<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Foundation\\Auth\\User as Authenticatable;
use Illuminate\\Notifications\\Notifiable;
use Laravel\\Sanctum\\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;

    protected $fillable = [
        'name', 'business_name', 'email', 'password', 'role', 'phone', 'location',
        'brand_logo', 'office_address', 'location_address', 'bio',
        'is_active',
    ];

    protected $hidden = ['password', 'remember_token'];

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
            'is_active' => 'boolean',
        ];
    }

    public function fishStocks()
    {
        return $this->hasMany(FishStock::class, 'seller_id');
    }

    public function deliveryAgencies()
    {
        return $this->hasMany(DeliveryAgency::class, 'seller_id');
    }

    public function ordersAsBuyer()
    {
        return $this->hasMany(Order::class, 'buyer_id');
    }

    public function ordersAsSeller()
    {
        return $this->hasMany(Order::class, 'seller_id');
    }
}
"""
ensure_content(
    BACKEND / "app" / "Models" / "User.php",
    "deliveryAgencies",
    USER_MODEL_FINAL,
    "Restore User::deliveryAgencies(), remove subscriptions()/subscription_status",
)

ORDER_MODEL_FINAL = """<?php

namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Factories\\HasFactory;
use Illuminate\\Database\\Eloquent\\Model;

class Order extends Model
{
    use HasFactory;

    protected $fillable = [
        'buyer_id', 'seller_id', 'status',
        'payment_method', 'payment_status', 'total_amount',
    ];

    protected function casts(): array
    {
        return [
            'total_amount' => 'decimal:2',
        ];
    }

    public function buyer()
    {
        return $this->belongsTo(User::class, 'buyer_id');
    }

    public function seller()
    {
        return $this->belongsTo(User::class, 'seller_id');
    }

    public function items()
    {
        return $this->hasMany(OrderItem::class);
    }

    public function delivery()
    {
        return $this->hasOne(OrderDelivery::class);
    }

    public function bill()
    {
        return $this->hasOne(Bill::class);
    }
}
"""
ensure_content(
    BACKEND / "app" / "Models" / "Order.php", "OrderDelivery", ORDER_MODEL_FINAL, "Restore Order::delivery()"
)

# ── A5. Restore OrderController ─────────────────────────────────────
print("\n=== A5. Restore OrderController ===")

ORDER_CONTROLLER_FINAL = """<?php

namespace App\\Http\\Controllers\\API;

use App\\Http\\Controllers\\Controller;
use App\\Models\\DeliveryAgency;
use App\\Models\\Order;
use App\\Models\\OrderDelivery;
use App\\Models\\FishStock;
use App\\Models\\Bill;
use Illuminate\\Http\\Request;
use Illuminate\\Support\\Str;

class OrderController extends Controller
{
    // How long a buyer has, after placing an order, to cancel it
    // themselves without seller involvement.
    private const CANCEL_WINDOW_MINUTES = 2;

    // Buyer places an order (one or more fish items from one seller)
    public function store(Request $request)
    {
        $data = $request->validate([
            'seller_id' => 'required|exists:users,id',
            'items' => 'required|array|min:1',
            'items.*.stock_id' => 'required|exists:fish_stocks,id',
            'items.*.quantity_kg' => 'required|numeric|min:0.1',
            'payment_method' => 'required|in:mobile,bank',
            // Choosing a delivery agency is optional — a buyer may
            // arrange their own delivery instead.
            'agency_id' => 'nullable|exists:delivery_agencies,id',
            'delivery_method' => 'nullable|string',
            // Required whenever an agency is chosen: the exact physical
            // location the buyer wants the order delivered to.
            'delivery_address' => 'nullable|string|max:500',
        ]);

        if (! empty($data['agency_id']) && empty(trim($data['delivery_address'] ?? ''))) {
            abort(422, 'Please enter the physical location for delivery.');
        }

        $deliveryFee = 0;
        $agency = null;

        if (! empty($data['agency_id'])) {
            $agency = DeliveryAgency::where('id', $data['agency_id'])
                ->where('seller_id', $data['seller_id'])
                ->where('is_active', true)
                ->first();

            abort_unless($agency, 422, 'Selected delivery agency is not available for this seller.');

            $deliveryFee = (float) $agency->delivery_fee;
        }

        $total = 0;
        $orderItems = [];

        foreach ($data['items'] as $item) {
            $stock = FishStock::findOrFail($item['stock_id']);
            abort_unless((int) $stock->seller_id === (int) $data['seller_id'], 422, 'One of the items no longer belongs to this seller.');
            abort_if($stock->quantity_kg < $item['quantity_kg'], 422, 'Insufficient stock for '.$stock->fish_name);

            $subtotal = $stock->price_per_kg * $item['quantity_kg'];
            $total += $subtotal;

            $orderItems[] = [
                'stock_id' => $stock->id,
                'fish_name' => $stock->fish_name,
                'quantity_kg' => $item['quantity_kg'],
                'price_per_kg' => $stock->price_per_kg,
                'subtotal' => $subtotal,
            ];
        }

        $total += $deliveryFee;

        $order = Order::create([
            'buyer_id' => $request->user()->id,
            'seller_id' => $data['seller_id'],
            'total_amount' => $total,
            'payment_method' => $data['payment_method'],
            'payment_status' => 'unpaid',
            'status' => 'pending',
        ]);

        foreach ($orderItems as $item) {
            $order->items()->create($item);
        }

        // Only record a delivery row when the buyer actually chose one
        // of the seller's agencies — otherwise they're arranging their
        // own delivery, so there's nothing to track here.
        if ($agency) {
            OrderDelivery::create([
                'order_id' => $order->id,
                'agency_id' => $agency->id,
                // Snapshotted at order time (like fish_name/price_per_kg
                // on OrderItem) so a later change to the agency's fee
                // never rewrites the cost of a past order.
                'delivery_fee' => $deliveryFee,
                'delivery_address' => trim($data['delivery_address']),
                'delivery_method' => $data['delivery_method'] ?? null,
            ]);
        }

        return response()->json($order->load('items', 'delivery'), 201);
    }

    // Buyer marks payment done → order becomes "received", seller can now confirm
    public function pay(Request $request, Order $order)
    {
        abort_unless($order->buyer_id === $request->user()->id, 403);

        $order->update([
            'payment_status' => 'paid',
            'status' => 'received',
        ]);

        return response()->json($order);
    }

    // Seller confirms order → stock decreases, bill is generated
    public function confirm(Request $request, Order $order)
    {
        abort_unless($order->seller_id === $request->user()->id, 403);
        abort_unless($order->payment_status === 'paid', 422, 'Payment not received yet');

        $order->update(['status' => 'confirmed']);

        foreach ($order->items as $item) {
            $item->stock->decreaseStock((float) $item->quantity_kg);
        }

        Bill::firstOrCreate(
            ['order_id' => $order->id],
            [
                'buyer_id' => $order->buyer_id,
                'bill_number' => 'BILL-'.strtoupper(Str::random(8)),
                'issued_at' => now(),
            ]
        );

        return response()->json($order->load('items', 'bill'));
    }

    // Buyer: cancel their own order, but only within the first
    // CANCEL_WINDOW_MINUTES minutes and only before the seller has
    // confirmed/processed it. After that, the order has to play out.
    public function cancel(Request $request, Order $order)
    {
        abort_unless($order->buyer_id === $request->user()->id, 403);

        abort_if(
            in_array($order->status, ['confirmed', 'processed', 'cancelled']),
            422,
            'This order can no longer be cancelled.'
        );

        abort_if(
            $order->created_at->diffInMinutes(now()) > self::CANCEL_WINDOW_MINUTES,
            422,
            'The '.self::CANCEL_WINDOW_MINUTES.'-minute cancellation window has expired.'
        );

        $order->update(['status' => 'cancelled']);

        return response()->json($order);
    }

    // Buyer: confirm physical delivery was received. Sets the
    // delivery status to 'delivered', which is what the seller sees
    // in their "Manage Buyers" panel. If the buyer arranged their own
    // delivery (no agency chosen at checkout, so no OrderDelivery row
    // exists yet), one is created here on the fly.
    public function confirmDelivery(Request $request, Order $order)
    {
        abort_unless($order->buyer_id === $request->user()->id, 403);

        abort_unless(
            in_array($order->status, ['confirmed', 'processed']),
            422,
            'Order has not been confirmed by the seller yet.'
        );

        $delivery = $order->delivery ?? $order->delivery()->create([
            'agency_id' => null,
            'delivery_fee' => 0,
            'delivery_status' => 'pending',
        ]);

        $delivery->update(['delivery_status' => 'delivered']);

        return response()->json($order->load('items', 'delivery', 'bill'));
    }

    // List orders for the current user (buyer sees own orders, seller sees incoming orders)
    public function index(Request $request)
    {
        $user = $request->user();

        $orders = $user->role === 'seller'
            ? $user->ordersAsSeller()->with('buyer', 'items', 'delivery', 'bill')
            : $user->ordersAsBuyer()->with('seller', 'items', 'delivery', 'bill');

        return response()->json($orders->latest()->paginate(20));
    }
}
"""
ensure_content(
    BACKEND / "app" / "Http" / "Controllers" / "API" / "OrderController.php",
    "use App\\Models\\DeliveryAgency;",
    ORDER_CONTROLLER_FINAL,
    "Restore OrderController agency/delivery logic + confirmDelivery",
)

# ── A6. Restore SellerController (+ drop subscription filter) ──────
print("\n=== A6. Restore SellerController ===")

SELLER_CONTROLLER_FINAL = """<?php

namespace App\\Http\\Controllers\\API;

use App\\Http\\Controllers\\API\\Concerns\\StoresImages;
use App\\Http\\Controllers\\Controller;
use App\\Models\\User;
use Illuminate\\Http\\Request;

class SellerController extends Controller
{
    use StoresImages;

    // Public: marketplace list of active sellers
    public function index(Request $request)
    {
        $sellers = User::where('role', 'seller')
            ->where('is_active', true)
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
            $data['brand_logo'] = $this->storeImage($request->file('brand_logo'), 'logos');
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

        $orders = \\App\\Models\\Order::with(['buyer', 'delivery'])
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
                'delivery_address' => $order->delivery?->delivery_address,
            ];
        });

        return response()->json($buyers);
    }
}
"""
ensure_content(
    BACKEND / "app" / "Http" / "Controllers" / "API" / "SellerController.php",
    "'agencies' => $user->deliveryAgencies()",
    SELLER_CONTROLLER_FINAL,
    "Restore agencies + delivery fields, drop subscription_status filter",
)

# ── A7. Restore AuthController (phone optional, no subscription) ───
print("\n=== A7. Restore optional phone on AuthController ===")

AUTH_CONTROLLER_FINAL = """<?php

namespace App\\Http\\Controllers\\API;

use App\\Http\\Controllers\\API\\Concerns\\StoresImages;
use App\\Http\\Controllers\\Controller;
use App\\Models\\User;
use Illuminate\\Http\\Request;
use Illuminate\\Support\\Facades\\Hash;

class AuthController extends Controller
{
    use StoresImages;

    public function register(Request $request)
    {
        $data = $request->validate([
            'name' => 'required|string|max:255',
            'business_name' => 'nullable|string|max:255',
            'email' => 'required|email|unique:users',
            'password' => [
                'required', 'min:8', 'confirmed',
                'regex:/^(?=.*[a-zA-Z])(?=.*\\d)(?=.*[^a-zA-Z\\d]).+$/',
            ],
            'role' => 'required|in:seller,buyer',
            // +255 followed by exactly 9 digits (e.g. +255712345678).
            // Stays optional — 'nullable' skips this rule entirely when
            // the field isn't sent at all, but enforces the exact
            // format whenever a value is present.
            'phone' => ['nullable', 'regex:/^\\+255\\d{9}$/'],
            'location' => 'nullable|string',
            'office_address' => 'nullable|string',
            // Collected here now, as part of seller account creation,
            // instead of as a separate step inside the seller dashboard.
            'brand_logo' => 'nullable|image|max:2048',
        ], [
            'password.regex' => 'Password must contain letters, numbers, and at least one special character.',
            'phone.regex' => 'Phone number must be +255 followed by exactly 9 digits.',
        ]);

        // Auto-capitalize each word (e.g. "john doe" -> "John Doe") rather
        // than rejecting lowercase input — friendlier than a validation error.
        $data['name'] = ucwords(strtolower($data['name']));
        if (! empty($data['business_name'])) {
            $data['business_name'] = ucwords(strtolower($data['business_name']));
        }

        $brandLogo = null;
        if ($request->hasFile('brand_logo')) {
            $brandLogo = $this->storeImage($request->file('brand_logo'), 'logos');
        }

        $user = User::create([
            'name' => $data['name'],
            'business_name' => $data['business_name'] ?? null,
            'email' => $data['email'],
            'password' => Hash::make($data['password']),
            'role' => $data['role'],
            'phone' => $data['phone'] ?? null,
            'location' => $data['location'] ?? null,
            'office_address' => $data['office_address'] ?? null,
            'brand_logo' => $brandLogo,
        ]);

        $token = $user->createToken('auth_token')->plainTextToken;

        return response()->json([
            'user' => $user,
            'token' => $token,
        ], 201);
    }

    public function login(Request $request)
    {
        $data = $request->validate([
            'email' => 'required|email',
            'password' => 'required',
        ]);

        $user = User::where('email', $data['email'])->first();

        if (! $user || ! Hash::check($data['password'], $user->password)) {
            return response()->json(['message' => 'Invalid credentials'], 401);
        }

        $token = $user->createToken('auth_token')->plainTextToken;

        return response()->json(['user' => $user, 'token' => $token]);
    }

    public function logout(Request $request)
    {
        $request->user()->currentAccessToken()->delete();

        return response()->json(['message' => 'Logged out']);
    }

    public function me(Request $request)
    {
        return response()->json($request->user());
    }
}
"""
ensure_content(
    BACKEND / "app" / "Http" / "Controllers" / "API" / "AuthController.php",
    "Stays optional",
    AUTH_CONTROLLER_FINAL,
    "Restore optional phone, drop subscription_status from registration",
)

# ── A8. Restore frontend delivery UI ────────────────────────────────
print("\n=== A8. Restore frontend delivery UI ===")

ORDER_MODAL_FINAL = """import { useState } from 'react'
import { Smartphone, Landmark, Phone } from 'lucide-react'
import { placeOrder, payOrder } from '../../api/orders'
import { formatTsh } from '../../utils/currency'
import toast from 'react-hot-toast'

export default function OrderModal({ data: { stock, seller, agencies }, onClose }) {
  const [qty, setQty]       = useState(1)
  // '' = no agency chosen yet, 'self' = buyer will arrange their own
  // delivery, otherwise an agency id.
  const [agency, setAgency] = useState('')
  const [deliveryAddress, setDeliveryAddress] = useState('')
  const [method, setMethod] = useState('mobile')
  const [loading, setLoading] = useState(false)

  const hasAgencies = agencies?.length > 0
  const selectedAgency = agencies?.find((a) => String(a.id) === String(agency))
  const deliveryFee = selectedAgency ? Number(selectedAgency.delivery_fee) : 0
  const subtotal = qty * stock.price_per_kg
  const total = (subtotal + deliveryFee).toFixed(2)

  const handleOrder = async () => {
    // Agency selection is optional — the buyer may arrange their own
    // delivery. But once an agency IS chosen, the exact physical
    // delivery location is required so the agency knows where to go.
    if (selectedAgency && !deliveryAddress.trim()) {
      toast.error('Please enter the physical location for delivery')
      return
    }
    setLoading(true)
    try {
      const { data: order } = await placeOrder({
        seller_id: seller.id,
        items: [{ stock_id: stock.id, quantity_kg: qty }],
        payment_method: method,
        agency_id: selectedAgency ? selectedAgency.id : null,
        delivery_address: selectedAgency ? deliveryAddress.trim() : null,
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
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-xl font-bold mb-4">Place Order – {stock.fish_name}</h2>

        <label className="block text-sm mb-1">Quantity (kg)</label>
        <input type="number" min="0.1" max={stock.quantity_kg} step="0.1"
          value={qty} onChange={e => setQty(Number(e.target.value))}
          className="input mb-4" />

        <label className="block text-sm mb-1">Delivery</label>
        {hasAgencies ? (
          <select value={agency} onChange={e => setAgency(e.target.value)} className="input mb-1">
            <option value="">I'll arrange my own delivery</option>
            {agencies.map(a => (
              <option key={a.id} value={a.id}>
                {a.agency_name} – {a.area_covered} ({formatTsh(a.delivery_fee)})
              </option>
            ))}
          </select>
        ) : (
          <p className="text-sm text-gray-500 mb-1">
            This seller has no delivery partner listed — you'll need to arrange your own delivery.
          </p>
        )}
        <p className="text-xs text-gray-400 mb-4">
          Choosing a delivery partner is optional — skip it if you have your own delivery arrangement.
        </p>

        {selectedAgency && (
          <>
            <label className="block text-sm mb-1">Delivery Location</label>
            <textarea
              value={deliveryAddress}
              onChange={e => setDeliveryAddress(e.target.value)}
              placeholder="Enter the exact physical location you want this order delivered to (street, landmark, area, etc.)"
              rows={2}
              className="input mb-4"
            />
          </>
        )}

        <label className="block text-sm mb-1">Payment Method</label>
        <div className="flex gap-4 mb-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" value="mobile" checked={method === 'mobile'} onChange={() => setMethod('mobile')} />
            <Smartphone className="w-4 h-4" /> Mobile Money
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input type="radio" value="bank" checked={method === 'bank'} onChange={() => setMethod('bank')} />
            <Landmark className="w-4 h-4" /> Bank Transfer
          </label>
        </div>

        {method === 'mobile' && seller.phone && (
          <div className="bg-green-50 text-green-800 rounded-lg p-3 mb-4 flex items-center gap-2 text-sm">
            <Phone className="w-4 h-4 flex-shrink-0" />
            Send mobile money to the seller at <span className="font-semibold">{seller.phone}</span>
          </div>
        )}

        <div className="bg-blue-50 rounded-lg p-3 mb-4 space-y-1">
          <p className="text-sm text-blue-800 flex justify-between">
            <span>Fish subtotal</span><span>{formatTsh(subtotal)}</span>
          </p>
          <p className="text-sm text-blue-800 flex justify-between">
            <span>Delivery fee</span><span>{deliveryFee ? formatTsh(deliveryFee) : '—'}</span>
          </p>
          <p className="font-semibold text-blue-900 flex justify-between border-t border-blue-200 pt-1 mt-1">
            <span>Total</span><span>{formatTsh(total)}</span>
          </p>
        </div>

        <div className="flex gap-3">
          <button onClick={onClose} className="flex-1 border border-gray-300 rounded-lg py-2">Cancel</button>
          <button onClick={handleOrder} disabled={loading}
            className="flex-1 bg-blue-600 text-white rounded-lg py-2 hover:bg-blue-700 disabled:opacity-50">
            {loading ? 'Placing…' : 'Confirm Order'}
          </button>
        </div>
      </div>
    </div>
  )
}
"""
ensure_content(
    FRONTEND / "components" / "orders" / "OrderModal.jsx",
    "hasAgencies",
    ORDER_MODAL_FINAL,
    "Restore OrderModal agency select + delivery address + delivery fee",
)

SELLER_PAGE_FINAL = """import { useState } from 'react'
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
                {a.agency_name} · {a.area_covered} · {formatTsh(a.delivery_fee)}
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
"""
ensure_content(
    FRONTEND / "pages" / "market" / "SellerPage.jsx",
    "Delivery Partners",
    SELLER_PAGE_FINAL,
    "Restore Delivery Agencies block on SellerPage",
)

BUYER_DASHBOARD_FINAL = """import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Fish, MapPin, Receipt } from 'lucide-react'
import { getOrders, cancelOrder, confirmDelivery } from '../../api/orders'
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

// Buyers can self-cancel only within this many minutes of placing the
// order, and only before the seller has confirmed it — mirrors the
// backend's OrderController::CANCEL_WINDOW_MINUTES.
const CANCEL_WINDOW_MINUTES = 2

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

// Whether an order is still inside the self-cancel window and not yet
// acted on by the seller.
function canCancel(order) {
  if (order.status !== 'pending' && order.status !== 'received') return false
  const ageMinutes = (Date.now() - new Date(order.created_at).getTime()) / 60000
  return ageMinutes <= CANCEL_WINDOW_MINUTES
}

// Whether the buyer can confirm delivery — seller has confirmed (or
// processed) the order and it hasn't already been marked delivered.
function canConfirmDelivery(order) {
  return (order.status === 'confirmed' || order.status === 'processed')
    && order.delivery?.delivery_status !== 'delivered'
}

// ── MY ORDERS — polls every 15 s ─────────────────────────────────────
function OrdersPanel() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['my-orders'],
    queryFn: () => getOrders().then((r) => r.data),
    refetchInterval: 15000,
    staleTime: 0,
  })

  const cancel = useMutation({
    mutationFn: (id) => cancelOrder(id),
    onSuccess: () => {
      toast.success('Order cancelled')
      qc.invalidateQueries({ queryKey: ['my-orders'] })
    },
    onError: (err) => {
      toast.error(err?.response?.data?.message || 'Could not cancel order')
    },
  })

  const confirmDeliveryMutation = useMutation({
    mutationFn: (id) => confirmDelivery(id),
    onSuccess: () => {
      toast.success('Delivery confirmed — thanks!')
      qc.invalidateQueries({ queryKey: ['my-orders'] })
    },
    onError: (err) => {
      toast.error(err?.response?.data?.message || 'Could not confirm delivery')
    },
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
                  {order.delivery && (
                    <p className="text-xs text-gray-400 mt-1 capitalize">
                      Delivery: {order.delivery.delivery_status}
                    </p>
                  )}
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

              <div className="flex gap-3 mt-3">
                {canCancel(order) && (
                  <button
                    onClick={() => cancel.mutate(order.id)}
                    disabled={cancel.isPending}
                    className="text-red-500 text-sm hover:underline"
                  >
                    Cancel Order
                  </button>
                )}
                {canConfirmDelivery(order) && (
                  <button
                    onClick={() => confirmDeliveryMutation.mutate(order.id)}
                    disabled={confirmDeliveryMutation.isPending}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 text-sm"
                  >
                    Confirm Delivery
                  </button>
                )}
              </div>
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
"""
ensure_content(
    FRONTEND / "pages" / "dashboard" / "BuyerDashboard.jsx",
    "canConfirmDelivery",
    BUYER_DASHBOARD_FINAL,
    "Restore delivery status + Confirm Delivery button",
)

SELLER_DASHBOARD_FINAL = """import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import client, { resolveImage } from '../../api/client'
import { getOrders, confirmOrder } from '../../api/orders'
import { getMyStocks } from '../../api/stocks'
import { useAuthStore } from '../../store/authStore'
import { formatTsh } from '../../utils/currency'
import DashboardLayout from '../../components/dashboard/DashboardLayout'
import ChangePasswordModal from '../../components/dashboard/ChangePasswordModal'
import ModalShell from '../../components/auth/ModalShell'
import AddStockForm from '../../components/stocks/AddStockForm'
import EditStockForm from '../../components/stocks/EditStockForm'
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
    queryFn: () => getMyStocks().then((r) => r.data),
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
  const [editingStock, setEditingStock] = useState(null)

  const { data: stocks } = useQuery({
    queryKey: ['seller-stocks'],
    queryFn: () => getMyStocks().then((r) => r.data),
    refetchInterval: 15000,
    staleTime: 0,
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
                onClick={() => setEditingStock(s)}
                className="mt-3 text-blue-600 text-sm hover:underline self-start"
              >
                Edit Stock
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

      {editingStock && (
        <ModalShell onClose={() => setEditingStock(null)} maxWidth="max-w-lg">
          <EditStockForm
            stock={editingStock}
            onDone={() => { setEditingStock(null); qc.invalidateQueries({ queryKey: ['seller-stocks'] }) }}
          />
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
                {b.delivery_address && (
                  <p className="text-xs text-gray-400 mt-1 max-w-xs text-right">
                    Deliver to: {b.delivery_address}
                  </p>
                )}
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
  const [form, setForm] = useState({ agency_name: '', contact: '', area_covered: '', delivery_fee: '' })

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
      setForm({ agency_name: '', contact: '', area_covered: '', delivery_fee: '' })
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
        <div className="grid sm:grid-cols-4 gap-3">
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
          <input
            placeholder="Delivery Fee (Tsh)" className="input" type="number" min="0" step="1"
            value={form.delivery_fee}
            onChange={(e) => setForm({ ...form, delivery_fee: e.target.value })}
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
                <p className="text-sm text-gray-500">
                  {a.contact} · {a.area_covered} · {formatTsh(a.delivery_fee)} delivery fee
                </p>
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
"""
ensure_content(
    FRONTEND / "pages" / "dashboard" / "SellerDashboard.jsx",
    "AgenciesPanel",
    SELLER_DASHBOARD_FINAL,
    "Restore Delivery Partners tab + delivery fields in Manage Buyers",
)

ORDERS_API_FINAL = """import client from './client'

export const getOrders        = ()   => client.get('/orders')
export const placeOrder       = (data) => client.post('/orders', data)
export const payOrder         = (id) => client.post(`/orders/${id}/pay`)
export const confirmOrder     = (id) => client.post(`/orders/${id}/confirm`)
// Buyer-only actions
export const cancelOrder      = (id) => client.post(`/orders/${id}/cancel`)
export const confirmDelivery  = (id) => client.post(`/orders/${id}/confirm-delivery`)
"""
ensure_content(
    FRONTEND / "api" / "orders.js", "confirmDelivery", ORDERS_API_FINAL, "Restore confirmDelivery API call"
)

BUYER_SIGNUP_MODAL_FINAL = """import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { User, Phone, Mail, Lock } from 'lucide-react'
import ModalShell from './ModalShell'
import { useUIStore } from '../../store/uiStore'
import { useAuthStore } from '../../store/authStore'
import { register } from '../../api/auth'
import PasswordStrengthIndicator, { isPasswordStrong } from './PasswordStrengthIndicator'
import { toTitleCase, formatTzPhone, isCompleteTzPhone } from '../../utils/formInput'

export default function BuyerSignupModal() {
  const { closeModal, openLogin } = useUIStore()
  const { setAuth } = useAuthStore()
  const navigate = useNavigate()

  const [form, setForm] = useState({
    name: '',
    phone: '+255',
    email: '',
    password: '',
    password_confirmation: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  // The full name is usually two or three words (first/middle/last) —
  // capitalize each one live as the buyer types.
  const updateName = (field) => (e) => setForm({ ...form, [field]: toTitleCase(e.target.value) })

  const handlePhoneChange = (e) => {
    setForm({ ...form, phone: formatTzPhone(e.target.value) })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!form.name || !form.email || !form.password) {
      setError('Please fill in all fields')
      return
    }
    if (form.phone !== '+255' && !isCompleteTzPhone(form.phone)) {
      setError('Phone number must be +255 followed by exactly 9 digits')
      return
    }
    if (form.password !== form.password_confirmation) {
      setError('Passwords do not match')
      return
    }
    if (!isPasswordStrong(form.password)) {
      setError('Password must contain letters, numbers, and a special character')
      return
    }

    setLoading(true)
    try {
      const { data } = await register({
        name: form.name,
        email: form.email,
        password: form.password,
        password_confirmation: form.password_confirmation,
        role: 'buyer',
        phone: form.phone === '+255' ? null : form.phone,
      })
      setAuth(data.user, data.token)
      closeModal()
      toast.success(`Welcome to SmartFish, ${data.user.name}!`)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.message || 'Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <ModalShell onClose={closeModal}>
      <div className="text-center mb-6">
        <h2 className="text-2xl font-bold text-blue-900">Create Buyer Account</h2>
        <p className="text-gray-500 mt-1">Browse sellers and order fresh fish</p>
      </div>

      {error && (
        <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2 mb-4">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <Field icon={User} placeholder="Full Name" value={form.name} onChange={updateName('name')} />
        <Field
          icon={Phone}
          placeholder="+255 7XX XXX XXX"
          value={form.phone}
          onChange={handlePhoneChange}
        />
        <Field
          icon={Mail}
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={update('email')}
        />
        <Field
          icon={Lock}
          type="password"
          placeholder="Password"
          value={form.password}
          onChange={update('password')}
        />
        <PasswordStrengthIndicator password={form.password} />
        <Field
          icon={Lock}
          type="password"
          placeholder="Confirm Password"
          value={form.password_confirmation}
          onChange={update('password_confirmation')}
        />

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-700 hover:bg-blue-800 text-white font-semibold py-3 rounded-lg transition mt-2 disabled:opacity-50"
        >
          {loading ? 'Creating account…' : 'Create Account'}
        </button>
      </form>

      <p className="text-center text-sm text-gray-500 mt-5">
        Already have an account?{' '}
        <button onClick={openLogin} className="text-blue-700 font-semibold hover:underline">
          Log in
        </button>
      </p>
    </ModalShell>
  )
}

function Field({ icon: Icon, type = 'text', placeholder, value, onChange }) {
  return (
    <div className="flex items-center border border-gray-300 rounded-lg px-3 py-2.5 focus-within:ring-2 focus-within:ring-blue-400">
      <Icon className="w-4 h-4 text-blue-600 mr-3 flex-shrink-0" />
      <input
        type={type}
        required
        placeholder={placeholder}
        className="w-full outline-none text-sm"
        value={value}
        onChange={onChange}
      />
    </div>
  )
}
"""
ensure_content(
    FRONTEND / "components" / "auth" / "BuyerSignupModal.jsx",
    "form.phone !== '+255' && !isCompleteTzPhone",
    BUYER_SIGNUP_MODAL_FINAL,
    "Revert buyer phone back to optional",
)


# ═══════════════════════════════════════════════════════════════════
# PART B — REMOVE "MANAGE SELLERS" / SUBSCRIPTIONS FEATURE
# ═══════════════════════════════════════════════════════════════════

# ── B1. Database ──────────────────────────────────────────────────
print("\n=== B1. Database — drop subscriptions ===")

DROP_SUBSCRIPTIONS_MIGRATION = """<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Support\\Facades\\Schema;

/**
 * "Manage Sellers" (the admin panel's subscription/billing approval
 * screen) is removed — sellers are activated immediately at
 * registration with no billing step, so there was nothing left for
 * this screen to actually manage. Drops the subscriptions table and
 * the now-unused subscription_status column on users.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::dropIfExists('subscriptions');

        if (Schema::hasColumn('users', 'subscription_status')) {
            Schema::table('users', function ($table) {
                $table->dropColumn('subscription_status');
            });
        }
    }

    public function down(): void
    {
        // Intentionally not reversible — see class docblock above.
    }
};
"""
create_if_missing(
    BACKEND / "database" / "migrations" / "2026_07_24_000002_drop_subscriptions_feature.php",
    DROP_SUBSCRIPTIONS_MIGRATION,
    "Create drop-subscriptions migration",
)

# ── B2. Delete subscription backend files ───────────────────────────
print("\n=== B2. Delete subscription backend files ===")

delete_if_exists(
    BACKEND / "app" / "Http" / "Controllers" / "API" / "SubscriptionController.php",
    "Delete SubscriptionController",
)
delete_if_exists(BACKEND / "app" / "Models" / "Subscription.php", "Delete Subscription model")
delete_if_exists(BACKEND / "database" / "factories" / "SubscriptionFactory.php", "Delete SubscriptionFactory")
delete_if_exists(BACKEND / "tests" / "Feature" / "SubscriptionTest.php", "Delete SubscriptionTest")

# Note: routes/api.php, User.php, and SellerController.php were already
# rewritten to their final (subscription-free) state in Part A above.

# ── B3. AdminController — drop subscription endpoints/stats ────────
print("\n=== B3. AdminController ===")

ADMIN_CONTROLLER_FINAL = """<?php

namespace App\\Http\\Controllers\\API;

use App\\Http\\Controllers\\Controller;
use App\\Models\\User;
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

    public function stats()
    {
        return response()->json([
            'total_users' => User::count(),
            // No subscription gate — "active" here just means not
            // suspended by an admin.
            'active_sellers' => User::where('role', 'seller')->where('is_active', true)->count(),
            'total_buyers' => User::where('role', 'buyer')->count(),
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
"""
ensure_content(
    BACKEND / "app" / "Http" / "Controllers" / "API" / "AdminController.php",
    "'is_active', true)->count(),\n            'total_buyers'",
    ADMIN_CONTROLLER_FINAL,
    "Remove subscription endpoints + stats from AdminController",
)

# ── B4. Factories / seeder / CLI command ────────────────────────────
print("\n=== B4. Drop subscription_status from factories/seeder/CLI ===")

USER_FACTORY_FINAL = """<?php

namespace Database\\Factories;

use Illuminate\\Database\\Eloquent\\Factories\\Factory;
use Illuminate\\Support\\Facades\\Hash;

class UserFactory extends Factory
{
    protected $model = \\App\\Models\\User::class;

    public function definition(): array
    {
        return [
            'name' => fake()->name(),
            'email' => fake()->unique()->safeEmail(),
            'email_verified_at' => now(),
            'password' => Hash::make('password'),
            'role' => 'buyer',
            'phone' => fake()->phoneNumber(),
            'location' => fake()->city(),
            'is_active' => true,
            'remember_token' => \\Illuminate\\Support\\Str::random(10),
        ];
    }

    public function seller(): static
    {
        return $this->state(fn () => [
            'role' => 'seller',
            'office_address' => fake()->address(),
            'location_address' => fake()->city(),
            'bio' => fake()->sentence(),
        ]);
    }

    public function admin(): static
    {
        return $this->state(fn () => [
            'role' => 'admin',
        ]);
    }

    public function unverified(): static
    {
        return $this->state(fn () => ['email_verified_at' => null]);
    }
}
"""
ensure_content(
    BACKEND / "database" / "factories" / "UserFactory.php",
    "'admin',\n        ]);",
    USER_FACTORY_FINAL,
    "Drop subscription_status from UserFactory",
)

DATABASE_SEEDER_FINAL = """<?php

namespace Database\\Seeders;

use App\\Models\\User;
use Illuminate\\Database\\Seeder;
use Illuminate\\Support\\Facades\\Hash;

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
"""
ensure_content(
    BACKEND / "database" / "seeders" / "DatabaseSeeder.php",
    "'is_active'           => true,\n            ]\n        );",
    DATABASE_SEEDER_FINAL,
    "Drop subscription_status from DatabaseSeeder",
)

CREATE_FIRST_ADMIN_FINAL = """<?php

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
        ]);

        $this->info("First admin created successfully: {$admin->email}");

        return self::SUCCESS;
    }
}
"""
ensure_content(
    BACKEND / "app" / "Console" / "Commands" / "CreateFirstAdmin.php",
    "'is_active' => true,\n        ]);",
    CREATE_FIRST_ADMIN_FINAL,
    "Drop subscription_status from CreateFirstAdmin",
)

# ── B5. Tests ────────────────────────────────────────────────────────
print("\n=== B5. Tests ===")

AUTH_TEST_FINAL = """<?php

namespace Tests\\Feature;

use App\\Models\\User;
use Illuminate\\Foundation\\Testing\\RefreshDatabase;
use Tests\\TestCase;

class AuthTest extends TestCase
{
    use RefreshDatabase;

    public function test_buyer_can_register(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Jane Buyer',
            'email' => 'jane@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
            'phone' => '+255700000000',
            'location' => 'Dar es Salaam',
        ]);

        $response->assertStatus(201)
            ->assertJsonStructure(['user', 'token'])
            ->assertJsonPath('user.role', 'buyer');

        $this->assertDatabaseHas('users', ['email' => 'jane@example.com']);
    }

    public function test_seller_registers_immediately_active(): void
    {
        // No subscription/plan step — sellers are immediately active
        // and usable right after registering.
        $response = $this->postJson('/api/register', [
            'name' => 'John Seller',
            'business_name' => 'Fresh Fish Co',
            'email' => 'john@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'seller',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('user.business_name', 'Fresh Fish Co');
    }

    public function test_name_and_business_name_are_auto_capitalized(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'john seller',
            'business_name' => 'fresh fish co',
            'email' => 'autocap@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'seller',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('user.name', 'John Seller')
            ->assertJsonPath('user.business_name', 'Fresh Fish Co');
    }

    public function test_registration_rejects_phone_with_wrong_digit_count(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Bad Phone',
            'email' => 'badphone@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
            'phone' => '+25570000000', // only 8 digits after +255
        ]);

        $response->assertStatus(422);
    }

    public function test_registration_rejects_phone_without_255_prefix(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Bad Phone',
            'email' => 'badphone2@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
            'phone' => '0700000000', // local format, not +255...
        ]);

        $response->assertStatus(422);
    }

    public function test_registration_accepts_a_valid_255_phone_number(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Good Phone',
            'email' => 'goodphone@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
            'phone' => '+255712345678',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('user.phone', '+255712345678');
    }

    public function test_registration_allows_phone_to_be_omitted_entirely(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'No Phone',
            'email' => 'nophone@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('user.phone', null);
    }

    public function test_registration_rejects_weak_password_without_special_character(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Weak Pass',
            'email' => 'weak@example.com',
            'password' => 'password123', // letters + numbers, no special char
            'password_confirmation' => 'password123',
            'role' => 'buyer',
        ]);

        $response->assertStatus(422);
    }

    public function test_registration_rejects_invalid_role(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Bad Role',
            'email' => 'badrole@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'admin', // not allowed at registration
        ]);

        $response->assertStatus(422);
    }

    public function test_registration_fails_with_duplicate_email(): void
    {
        User::factory()->create(['email' => 'taken@example.com']);

        $response = $this->postJson('/api/register', [
            'name' => 'Duplicate',
            'email' => 'taken@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
        ]);

        $response->assertStatus(422);
    }

    public function test_user_can_login_with_correct_credentials(): void
    {
        User::factory()->create([
            'email' => 'login@example.com',
            'password' => bcrypt('mypassword'),
        ]);

        $response = $this->postJson('/api/login', [
            'email' => 'login@example.com',
            'password' => 'mypassword',
        ]);

        $response->assertStatus(200)
            ->assertJsonStructure(['user', 'token']);
    }

    public function test_login_fails_with_wrong_password(): void
    {
        User::factory()->create([
            'email' => 'wrongpass@example.com',
            'password' => bcrypt('correctpassword'),
        ]);

        $response = $this->postJson('/api/login', [
            'email' => 'wrongpass@example.com',
            'password' => 'wrongpassword',
        ]);

        $response->assertStatus(401)
            ->assertJson(['message' => 'Invalid credentials']);
    }

    public function test_login_fails_for_nonexistent_user(): void
    {
        $response = $this->postJson('/api/login', [
            'email' => 'doesnotexist@example.com',
            'password' => 'whatever',
        ]);

        $response->assertStatus(401);
    }

    public function test_authenticated_user_can_fetch_own_profile(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user, 'sanctum')->getJson('/api/me');

        $response->assertStatus(200)
            ->assertJsonPath('id', $user->id);
    }

    public function test_guest_cannot_access_protected_route(): void
    {
        $response = $this->getJson('/api/me');

        $response->assertStatus(401);
    }

    public function test_user_can_logout(): void
    {
        $user = User::factory()->create();
        $token = $user->createToken('test')->plainTextToken;

        $response = $this->withHeader('Authorization', "Bearer {$token}")
            ->postJson('/api/logout');

        $response->assertStatus(200);
    }
}
"""
ensure_content(
    BACKEND / "tests" / "Feature" / "AuthTest.php",
    "test_registration_allows_phone_to_be_omitted_entirely",
    AUTH_TEST_FINAL,
    "Restore phone-optional tests, drop subscription_status assertion",
)

ORDER_TEST_FINAL = """<?php

namespace Tests\\Feature;

use App\\Models\\DeliveryAgency;
use App\\Models\\FishStock;
use App\\Models\\User;
use Illuminate\\Foundation\\Testing\\RefreshDatabase;
use Tests\\TestCase;

class OrderTest extends TestCase
{
    use RefreshDatabase;

    public function test_buyer_can_place_an_order_without_choosing_a_delivery_agency(): void
    {
        // Choosing a delivery agency is optional — a buyer may have
        // their own delivery arrangement.
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => null,
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('total_amount', '10000.00') // 2kg * 5000, no delivery fee
            ->assertJsonPath('delivery', null);
    }

    public function test_order_total_includes_the_chosen_agencys_delivery_fee(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id, 'delivery_fee' => 2000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
            'delivery_address' => '123 Uhuru Street, Dar es Salaam',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('total_amount', '12000.00') // 10000 fish + 2000 delivery
            ->assertJsonPath('delivery.delivery_fee', '2000.00')
            ->assertJsonPath('delivery.agency_id', $agency->id)
            ->assertJsonPath('delivery.delivery_address', '123 Uhuru Street, Dar es Salaam');
    }

    public function test_order_rejected_when_agency_chosen_without_a_delivery_address(): void
    {
        // delivery_address is required once an agency is chosen, so
        // the agency/delivery driver knows exactly where to go.
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id, 'delivery_fee' => 2000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
        ]);

        $response->assertStatus(422);
    }

    public function test_changing_an_agencys_fee_later_does_not_change_a_past_orders_total(): void
    {
        // delivery_fee is snapshotted onto the order at placement time,
        // same as fish_name/price_per_kg on OrderItem.
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id, 'delivery_fee' => 2000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 1]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
            'delivery_address' => '45 Kariakoo Road, Dar es Salaam',
        ]);
        $orderId = $response->json('id');

        $agency->update(['delivery_fee' => 9000]);

        $this->assertEquals('2000.00', $this->actingAs($seller, 'sanctum')
            ->getJson('/api/orders')
            ->json('data.0.delivery.delivery_fee'));
    }

    public function test_order_rejected_when_agency_belongs_to_a_different_seller(): void
    {
        $seller = User::factory()->seller()->create();
        $otherSeller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10]);
        $otherSellerAgency = DeliveryAgency::factory()->create(['seller_id' => $otherSeller->id]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $otherSellerAgency->id,
        ]);

        $response->assertStatus(422);
    }

    public function test_order_rejected_when_stock_belongs_to_a_different_seller(): void
    {
        $seller = User::factory()->seller()->create();
        $otherSeller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $otherSellerStock = FishStock::factory()->create(['seller_id' => $otherSeller->id, 'quantity_kg' => 10]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $otherSellerStock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => null,
        ]);

        $response->assertStatus(422);
    }

    public function test_order_rejected_when_quantity_exceeds_available_stock(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 1]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 5]],
            'payment_method' => 'mobile',
            'agency_id' => null,
        ]);

        $response->assertStatus(422);
    }
}
"""
ensure_content(
    BACKEND / "tests" / "Feature" / "OrderTest.php",
    "test_order_total_includes_the_chosen_agencys_delivery_fee",
    ORDER_TEST_FINAL,
    "Restore full agency/delivery test suite",
)

ADMIN_TEST_PATH = BACKEND / "tests" / "Feature" / "AdminUserManagementTest.php"
_admin_test_content = read(ADMIN_TEST_PATH)
if _admin_test_content:
    _old_structure = "'table_sizes' => ['users', 'fish_stocks', 'orders', 'subscriptions'],"
    _new_structure = "'table_sizes' => ['users', 'fish_stocks', 'orders'],"
    if _new_structure in _admin_test_content and _old_structure not in _admin_test_content:
        print(f"  [skip] Drop 'subscriptions' from metrics test assertion (already applied) — {ADMIN_TEST_PATH.name}")
    elif _old_structure in _admin_test_content:
        write(ADMIN_TEST_PATH, _admin_test_content.replace(_old_structure, _new_structure, 1))
        print(f"  [ok]   Drop 'subscriptions' from metrics test assertion — {ADMIN_TEST_PATH.name}")
    else:
        FAILS.append(f"PATTERN NOT FOUND: metrics table_sizes assertion in {ADMIN_TEST_PATH}")
        print(f"  [FAIL] Drop 'subscriptions' from metrics test assertion — pattern not found in {ADMIN_TEST_PATH.name}")

# ── B6. Frontend — AdminPanel.jsx + delete api/subscriptions.js ────
print("\n=== B6. AdminPanel.jsx — remove Manage Sellers ===")

ADMIN_PANEL_FINAL = """import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import client from '../../api/client'
import { useAuthStore } from '../../store/authStore'
import DashboardLayout from '../../components/dashboard/DashboardLayout'
import ChangePasswordModal from '../../components/dashboard/ChangePasswordModal'
import ModalShell from '../../components/auth/ModalShell'
import {
  HomeIcon, UsersIcon, ActivityIcon, LockIcon, LogoutIcon,
} from '../../components/dashboard/Icons'

const SECTIONS = [
  { key: 'home', label: 'Home', icon: HomeIcon },
  { key: 'users', label: 'Manage Users', icon: UsersIcon },
  { key: 'performance', label: 'System Performance', icon: ActivityIcon },
  { key: 'password', label: 'Change Password', icon: LockIcon },
  { key: 'logout', label: 'Logout', icon: LogoutIcon },
]

export default function AdminPanel() {
  const [active, setActive] = useState('home')
  const [showPasswordModal, setShowPasswordModal] = useState(false)
  const { clearAuth } = useAuthStore()

  const handleSelect = (key) => {
    if (key === 'logout') {
      clearAuth()
      window.location.href = '/'
      return
    }
    if (key === 'password') {
      setShowPasswordModal(true)
      return
    }
    setActive(key)
  }

  return (
    <>
      <DashboardLayout items={SECTIONS} activeKey={active} onSelect={handleSelect}>
        {active === 'home' && <HomePanel />}
        {active === 'users' && <UsersPanel />}
        {active === 'performance' && <PerformancePanel />}
      </DashboardLayout>

      {showPasswordModal && (
        <ChangePasswordModal onClose={() => setShowPasswordModal(false)} />
      )}
    </>
  )
}

// ── HOME — overview stats ────────────────────────────────────────────
function HomePanel() {
  const { data } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: () => client.get('/admin/stats').then((r) => r.data),
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-6">Admin Overview</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Users" value={data?.total_users} />
        <StatCard label="Active Sellers" value={data?.active_sellers} />
        <StatCard label="Total Buyers" value={data?.total_buyers} />
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

// ── MANAGE USERS — list + suspend/delete + register-admin button ───
function UsersPanel() {
  const qc = useQueryClient()
  const [showRegisterAdmin, setShowRegisterAdmin] = useState(false)

  const { data: users } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => client.get('/admin/users').then((r) => r.data),
  })

  const toggleUser = useMutation({
    mutationFn: (id) => client.put(`/admin/users/${id}/toggle`),
    onSuccess: () => {
      toast.success('User status updated')
      qc.invalidateQueries(['admin-users'])
    },
  })

  const deleteUser = useMutation({
    mutationFn: (id) => client.delete(`/admin/users/${id}`),
    onSuccess: () => {
      toast.success('User deleted')
      qc.invalidateQueries(['admin-users'])
    },
    onError: (err) => toast.error(err.response?.data?.message || 'Could not delete user'),
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-blue-900">Manage Users</h1>
        <button onClick={() => setShowRegisterAdmin(true)} className="btn-primary">
          + Register Admin
        </button>
      </div>

      <div className="bg-white rounded-xl shadow divide-y">
        {users?.data?.map((u) => (
          <div key={u.id} className="flex flex-wrap justify-between items-center gap-3 p-4">
            <div>
              <p className="font-semibold">
                {u.name} <span className="text-xs text-gray-400 capitalize">({u.role})</span>
              </p>
              <p className="text-sm text-gray-500">{u.email}</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => toggleUser.mutate(u.id)}
                className={`text-sm px-3 py-1.5 rounded-lg ${
                  u.is_active ? 'bg-yellow-50 text-yellow-700' : 'bg-green-50 text-green-700'
                }`}
              >
                {u.is_active ? 'Suspend' : 'Activate'}
              </button>
              <button
                onClick={() => {
                  if (confirm(`Permanently delete ${u.name}? This cannot be undone.`)) {
                    deleteUser.mutate(u.id)
                  }
                }}
                className="text-sm px-3 py-1.5 rounded-lg bg-red-50 text-red-600"
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {showRegisterAdmin && (
        <RegisterAdminModal onClose={() => setShowRegisterAdmin(false)} />
      )}
    </div>
  )
}

function RegisterAdminModal({ onClose }) {
  const qc = useQueryClient()
  const [form, setForm] = useState({
    email: '', phone: '+255', password: '', password_confirmation: '',
  })
  const [error, setError] = useState('')

  const createAdmin = useMutation({
    mutationFn: (data) => client.post('/admin/users', data),
    onSuccess: () => {
      toast.success('New admin registered')
      qc.invalidateQueries(['admin-users'])
      onClose()
    },
    onError: (err) => setError(err.response?.data?.message || 'Failed to register admin'),
  })

  const handlePhoneChange = (e) => {
    let val = e.target.value
    if (!val.startsWith('+255')) val = '+255'
    setForm({ ...form, phone: val })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')
    if (form.password !== form.password_confirmation) {
      setError('Passwords do not match')
      return
    }
    createAdmin.mutate(form)
  }

  return (
    <ModalShell onClose={onClose}>
      <h2 className="text-xl font-bold text-blue-900 mb-4">Register New Admin</h2>

      {error && (
        <div className="bg-red-50 text-red-600 text-sm rounded-lg px-4 py-2 mb-4">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <input
          type="email" required placeholder="Email" className="input"
          value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <input
          placeholder="+255 7XX XXX XXX" className="input"
          value={form.phone} onChange={handlePhoneChange}
        />
        <input
          type="password" required placeholder="Password" className="input"
          value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <input
          type="password" required placeholder="Confirm Password" className="input"
          value={form.password_confirmation}
          onChange={(e) => setForm({ ...form, password_confirmation: e.target.value })}
        />
        <button type="submit" disabled={createAdmin.isPending} className="btn-primary w-full">
          {createAdmin.isPending ? 'Creating…' : 'Register Admin'}
        </button>
      </form>
    </ModalShell>
  )
}

// ── SYSTEM PERFORMANCE — live polling metrics ───────────────────────
function PerformancePanel() {
  const { data } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: () => client.get('/admin/metrics').then((r) => r.data),
    refetchInterval: 5000, // live polling every 5s
  })

  return (
    <div>
      <h1 className="text-2xl font-bold text-blue-900 mb-2">System Performance</h1>
      <p className="text-gray-500 text-sm mb-6">
        Live application metrics · refreshes every 5 seconds
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <StatCard label="Active Users (15 min)" value={data?.active_users_last_15_min} />
        <StatCard label="Queries This Request" value={data?.queries_this_request} />
        <StatCard label="PHP Version" value={data?.php_version} />
        <StatCard label="Laravel Version" value={data?.laravel_version} />
      </div>

      <h2 className="text-lg font-bold text-blue-900 mb-3">Table Sizes</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Users" value={data?.table_sizes?.users} />
        <StatCard label="Fish Stocks" value={data?.table_sizes?.fish_stocks} />
        <StatCard label="Orders" value={data?.table_sizes?.orders} />
      </div>

      {data?.server_time && (
        <p className="text-xs text-gray-400 mt-6">
          Server time: {new Date(data.server_time).toLocaleString()}
        </p>
      )}
    </div>
  )
}
"""
ensure_content(
    FRONTEND / "pages" / "admin" / "AdminPanel.jsx",
    "{ key: 'users', label: 'Manage Users', icon: UsersIcon },\n  { key: 'performance'",
    ADMIN_PANEL_FINAL,
    "Remove Manage Sellers tab + subscription stats from AdminPanel",
)

delete_if_exists(FRONTEND / "api" / "subscriptions.js", "Delete api/subscriptions.js")


# ═══════════════════════════════════════════════════════════════════
print("\n=== Summary ===")
if FAILS:
    print(f"{len(FAILS)} issue(s) found:")
    for f in FAILS:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All patches applied successfully (or were already applied).")
    print("\nNext steps:")
    print("  backend:  php artisan migrate")
    print("            php artisan test")
    print("  frontend: no build step needed beyond your normal dev/build flow")
