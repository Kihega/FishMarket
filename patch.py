#!/usr/bin/env python3
"""
patch_18.py

Run from the FishMarket project root:

    python3 patch_18.py

Major fix — removes the delivery-agency/delivery-tracking feature
entirely and replaces it with a simpler flow: every buyer must give a
valid Tanzanian mobile number when they create their account, and the
seller sees that number on the order (both in "Manage Orders" and
"Manage Buyers") so they can call the buyer directly for delivery
coordination or anything else.

Removed completely (backend + frontend + tests):
  - Delivery Partners / delivery agencies (register, list, remove)
  - Delivery address field on orders
  - Delivery fee added to order totals
  - Delivery status tracking + buyer's "Confirm Delivery" action
  - order_deliveries / delivery_agencies database tables

Added:
  - Buyer registration now REQUIRES a valid +255 phone number
    (sellers are unaffected — their phone stays optional)
  - Buyer's phone number is shown to the seller in "Manage Orders"
    (not just "Manage Buyers")

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


def patch(path: Path, old: str, new: str, label: str, already_marker: str = None):
    """Exact-string patch, idempotent."""
    content = read(path)
    if not content:
        return
    marker = already_marker if already_marker is not None else new
    if marker in content:
        print(f"  [skip] {label} (already applied) — {path.name}")
        return
    if old not in content:
        FAILS.append(f"PATTERN NOT FOUND: {label} in {path}")
        print(f"  [FAIL] {label} — pattern not found in {path.name}")
        return
    if content.count(old) > 1:
        FAILS.append(f"PATTERN NOT UNIQUE: {label} in {path}")
        print(f"  [FAIL] {label} — pattern not unique in {path.name}")
        return
    write(path, content.replace(old, new, 1))
    print(f"  [ok]   {label} — {path.name}")


def rewrite_file(path: Path, old_marker: str, new_content: str, label: str):
    """
    Full-file rewrite, idempotent: skips if old_marker (something only
    present in the pre-patch version) is already gone from the file —
    meaning this patch (or something equivalent) already ran.
    """
    content = read(path)
    if not content:
        return
    if old_marker not in content:
        print(f"  [skip] {label} (already applied) — {path.name}")
        return
    write(path, new_content)
    print(f"  [ok]   {label} — {path.name}")


def delete_if_exists(path: Path, label: str):
    if not path.exists():
        print(f"  [skip] {label} (already removed) — {path.name}")
        return
    path.unlink()
    print(f"  [ok]   {label} — deleted {path.name}")


def create_if_missing(path: Path, content: str, label: str):
    if path.exists():
        print(f"  [skip] {label} (file already exists) — {path.name}")
        return
    write(path, content)
    print(f"  [ok]   {label} — created {path.name}")


# ═══════════════════════════════════════════════════════════════════
# 1. DATABASE — drop delivery-related tables
# ═══════════════════════════════════════════════════════════════════
print("\n=== 1. Drop delivery tables ===")

migration_path = (
    BACKEND / "database" / "migrations"
    / "2026_07_22_000001_drop_delivery_feature_tables.php"
)
MIGRATION_CONTENT = """<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Support\\Facades\\Schema;

/**
 * The delivery-agency / delivery-tracking feature has been removed
 * entirely. Buyers now give the seller a phone number at checkout
 * time (via their account) instead of picking a delivery partner or
 * typing an address, so these tables are no longer used anywhere in
 * the app.
 *
 * order_deliveries is dropped first since it holds a foreign key onto
 * delivery_agencies.
 *
 * This migration is intentionally one-way: reconstructing the exact
 * historical shape of both tables (they were altered by several later
 * migrations) in down() would just leave two empty, unused tables
 * back in place. If this ever needs reverting, restore from the
 * migrations this superseded instead.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::dropIfExists('order_deliveries');
        Schema::dropIfExists('delivery_agencies');
    }

    public function down(): void
    {
        // Intentionally not reversible — see class docblock above.
    }
};
"""
create_if_missing(migration_path, MIGRATION_CONTENT, "Create drop-delivery-tables migration")


# ═══════════════════════════════════════════════════════════════════
# 2. BACKEND — delete files that only existed for this feature
# ═══════════════════════════════════════════════════════════════════
print("\n=== 2. Delete delivery-agency backend files ===")

delete_if_exists(
    BACKEND / "app" / "Http" / "Controllers" / "API" / "DeliveryAgencyController.php",
    "Delete DeliveryAgencyController",
)
delete_if_exists(BACKEND / "app" / "Models" / "DeliveryAgency.php", "Delete DeliveryAgency model")
delete_if_exists(BACKEND / "app" / "Models" / "OrderDelivery.php", "Delete OrderDelivery model")
delete_if_exists(
    BACKEND / "database" / "factories" / "DeliveryAgencyFactory.php",
    "Delete DeliveryAgencyFactory",
)
delete_if_exists(
    BACKEND / "tests" / "Feature" / "DeliveryAgencyTest.php",
    "Delete DeliveryAgencyTest",
)


# ═══════════════════════════════════════════════════════════════════
# 3. BACKEND — routes
# ═══════════════════════════════════════════════════════════════════
print("\n=== 3. Routes ===")

routes_path = BACKEND / "routes" / "api.php"

ROUTES_API_NEW = """<?php

use Illuminate\\Support\\Facades\\Route;
use App\\Http\\Controllers\\API\\AuthController;
use App\\Http\\Controllers\\API\\SellerController;
use App\\Http\\Controllers\\API\\FishStockController;
use App\\Http\\Controllers\\API\\FishCategoryController;
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
    // /seller/stocks is the seller's OWN scoped list (used by the
    // dashboard) — distinct from the public /stocks marketplace feed.
    Route::get('/seller/stocks', [FishStockController::class, 'mine']);
    Route::post('/stocks', [FishStockController::class, 'store']);
    Route::put('/stocks/{fishStock}', [FishStockController::class, 'update']);
    Route::delete('/stocks/{fishStock}', [FishStockController::class, 'destroy']);

    // Orders
    Route::get('/orders', [OrderController::class, 'index']);
    Route::post('/orders', [OrderController::class, 'store']);
    Route::post('/orders/{order}/pay', [OrderController::class, 'pay']);
    Route::post('/orders/{order}/confirm', [OrderController::class, 'confirm']);
    Route::post('/orders/{order}/cancel', [OrderController::class, 'cancel']);

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
"""

rewrite_file(
    routes_path,
    "DeliveryAgencyController",
    ROUTES_API_NEW,
    "Rewrite routes/api.php (remove /agencies + confirm-delivery routes/import)",
)


# ═══════════════════════════════════════════════════════════════════
# 4. BACKEND — models
# ═══════════════════════════════════════════════════════════════════
print("\n=== 4. Models ===")

USER_MODEL_NEW = """<?php

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
        'is_active', 'subscription_status',
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

    public function ordersAsBuyer()
    {
        return $this->hasMany(Order::class, 'buyer_id');
    }

    public function ordersAsSeller()
    {
        return $this->hasMany(Order::class, 'seller_id');
    }

    public function subscriptions()
    {
        return $this->hasMany(Subscription::class, 'seller_id');
    }
}
"""

rewrite_file(
    BACKEND / "app" / "Models" / "User.php",
    "deliveryAgencies",
    USER_MODEL_NEW,
    "Remove User::deliveryAgencies()",
)

ORDER_MODEL_NEW = """<?php

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

    public function bill()
    {
        return $this->hasOne(Bill::class);
    }
}
"""

rewrite_file(
    BACKEND / "app" / "Models" / "Order.php",
    "OrderDelivery",
    ORDER_MODEL_NEW,
    "Remove Order::delivery()",
)


# ═══════════════════════════════════════════════════════════════════
# 5. BACKEND — OrderController (full rewrite, agency/delivery-free)
# ═══════════════════════════════════════════════════════════════════
print("\n=== 5. OrderController ===")

ORDER_CONTROLLER_NEW = """<?php

namespace App\\Http\\Controllers\\API;

use App\\Http\\Controllers\\Controller;
use App\\Models\\Order;
use App\\Models\\FishStock;
use App\\Models\\Bill;
use Illuminate\\Http\\Request;
use Illuminate\\Support\\Str;

class OrderController extends Controller
{
    // How long a buyer has, after placing an order, to cancel it
    // themselves without seller involvement.
    private const CANCEL_WINDOW_MINUTES = 2;

    // Buyer places an order (one or more fish items from one seller).
    // Delivery itself isn't tracked in the app — the seller sees the
    // buyer's phone number on the order (their account requires one)
    // and calls them directly to sort out delivery.
    public function store(Request $request)
    {
        $data = $request->validate([
            'seller_id' => 'required|exists:users,id',
            'items' => 'required|array|min:1',
            'items.*.stock_id' => 'required|exists:fish_stocks,id',
            'items.*.quantity_kg' => 'required|numeric|min:0.1',
            'payment_method' => 'required|in:mobile,bank',
        ]);

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

        return response()->json($order->load('items'), 201);
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

    // List orders for the current user (buyer sees own orders, seller sees incoming orders).
    // Sellers get the buyer relation loaded so the buyer's phone number
    // is available on every order for delivery coordination calls.
    public function index(Request $request)
    {
        $user = $request->user();

        $orders = $user->role === 'seller'
            ? $user->ordersAsSeller()->with('buyer', 'items', 'bill')
            : $user->ordersAsBuyer()->with('seller', 'items', 'bill');

        return response()->json($orders->latest()->paginate(20));
    }
}
"""

rewrite_file(
    BACKEND / "app" / "Http" / "Controllers" / "API" / "OrderController.php",
    "use App\\Models\\DeliveryAgency;",
    ORDER_CONTROLLER_NEW,
    "Rewrite OrderController (remove agency/delivery logic + confirmDelivery)",
)


# ═══════════════════════════════════════════════════════════════════
# 6. BACKEND — SellerController (drop agencies + delivery fields)
# ═══════════════════════════════════════════════════════════════════
print("\n=== 6. SellerController ===")

SELLER_CONTROLLER_NEW = """<?php

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
            ->where('subscription_status', 'active')
            ->when($request->location, fn ($q) => $q->where('location', 'like', "%{$request->location}%"))
            ->withCount('fishStocks')
            ->paginate(20);

        return response()->json($sellers);
    }

    // Public: single seller profile + stocks
    public function show(User $user)
    {
        abort_unless($user->role === 'seller', 404);

        return response()->json([
            'seller' => $user,
            'stocks' => $user->fishStocks()->with('category')->where('status', 'active')->get(),
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
     * platform — contact info (including phone, so the seller can
     * call them) and when they ordered. Powers the "Manage Buyers"
     * sidebar section.
     */
    public function buyers(Request $request)
    {
        $seller = $request->user();
        abort_unless($seller->role === 'seller', 403);

        $orders = \\App\\Models\\Order::with('buyer')
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
            ];
        });

        return response()->json($buyers);
    }
}
"""

rewrite_file(
    BACKEND / "app" / "Http" / "Controllers" / "API" / "SellerController.php",
    "'agencies' => $user->deliveryAgencies()->where('is_active', true)->get(),",
    SELLER_CONTROLLER_NEW,
    "Rewrite SellerController (drop agencies + delivery fields)",
)


# ═══════════════════════════════════════════════════════════════════
# 7. BACKEND — AuthController: buyer phone becomes required
# ═══════════════════════════════════════════════════════════════════
print("\n=== 7. AuthController — required buyer phone ===")

auth_controller = BACKEND / "app" / "Http" / "Controllers" / "API" / "AuthController.php"
patch(
    auth_controller,
    """            'role' => 'required|in:seller,buyer',
            // +255 followed by exactly 9 digits (e.g. +255712345678).
            // Stays optional — 'nullable' skips this rule entirely when
            // the field isn't sent at all, but enforces the exact
            // format whenever a value is present.
            'phone' => ['nullable', 'regex:/^\\+255\\d{9}$/'],""",
    """            'role' => 'required|in:seller,buyer',
            // +255 followed by exactly 9 digits (e.g. +255712345678).
            // REQUIRED for buyers — the seller needs a real number to
            // call them about delivery. Sellers can still skip it.
            'phone' => ['required_if:role,buyer', 'regex:/^\\+255\\d{9}$/'],""",
    "Make phone required_if role=buyer",
)
patch(
    auth_controller,
    "'phone.regex' => 'Phone number must be +255 followed by exactly 9 digits.',",
    "'phone.regex' => 'Phone number must be +255 followed by exactly 9 digits.',\n            'phone.required_if' => 'A valid Tanzanian mobile number is required to create a buyer account.',",
    "Add phone.required_if error message",
)


# ═══════════════════════════════════════════════════════════════════
# 8. BACKEND — tests
# ═══════════════════════════════════════════════════════════════════
print("\n=== 8. Tests ===")

ORDER_TEST_NEW = """<?php

namespace Tests\\Feature;

use App\\Models\\FishStock;
use App\\Models\\User;
use Illuminate\\Foundation\\Testing\\RefreshDatabase;
use Tests\\TestCase;

class OrderTest extends TestCase
{
    use RefreshDatabase;

    public function test_buyer_can_place_an_order(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('total_amount', '10000.00'); // 2kg * 5000
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
        ]);

        $response->assertStatus(422);
    }

    public function test_seller_sees_buyer_phone_number_on_their_orders(): void
    {
        // The seller needs to be able to call the buyer directly
        // (about delivery or anything else), so the buyer relation
        // must expose their phone number on every order.
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create(['phone' => '+255712345678']);
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10]);

        $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 1]],
            'payment_method' => 'mobile',
        ]);

        $response = $this->actingAs($seller, 'sanctum')->getJson('/api/orders');

        $response->assertStatus(200)
            ->assertJsonPath('data.0.buyer.phone', '+255712345678');
    }
}
"""

rewrite_file(
    BACKEND / "tests" / "Feature" / "OrderTest.php",
    "use App\\Models\\DeliveryAgency;",
    ORDER_TEST_NEW,
    "Rewrite OrderTest (remove agency/delivery tests, add buyer-phone-on-order test)",
)

auth_test = BACKEND / "tests" / "Feature" / "AuthTest.php"
patch(
    auth_test,
    """    public function test_registration_allows_phone_to_be_omitted_entirely(): void
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
    }""",
    """    public function test_registration_rejects_buyer_without_phone(): void
    {
        // Buyers must give a real, callable number so the seller can
        // reach them about delivery — sellers are unaffected (see
        // test_seller_registers_immediately_active, which registers
        // successfully with no phone at all).
        $response = $this->postJson('/api/register', [
            'name' => 'No Phone',
            'email' => 'nophone@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
        ]);

        $response->assertStatus(422);
    }""",
    "Turn phone-omission test into a required-phone-for-buyers test",
)


# ═══════════════════════════════════════════════════════════════════
# 9. FRONTEND — api/orders.js
# ═══════════════════════════════════════════════════════════════════
print("\n=== 9. frontend/src/api/orders.js ===")

ORDERS_API_NEW = """import client from './client'

export const getOrders        = ()   => client.get('/orders')
export const placeOrder       = (data) => client.post('/orders', data)
export const payOrder         = (id) => client.post(`/orders/${id}/pay`)
export const confirmOrder     = (id) => client.post(`/orders/${id}/confirm`)
// Buyer-only actions
export const cancelOrder      = (id) => client.post(`/orders/${id}/cancel`)
"""

rewrite_file(
    FRONTEND / "api" / "orders.js",
    "confirmDelivery",
    ORDERS_API_NEW,
    "Remove confirmDelivery API call",
)


# ═══════════════════════════════════════════════════════════════════
# 10. FRONTEND — OrderModal.jsx (rewrite, agency/delivery-free)
# ═══════════════════════════════════════════════════════════════════
print("\n=== 10. OrderModal.jsx ===")

ORDER_MODAL_NEW = """import { useState } from 'react'
import { Smartphone, Landmark, Phone } from 'lucide-react'
import { placeOrder, payOrder } from '../../api/orders'
import { formatTsh } from '../../utils/currency'
import toast from 'react-hot-toast'

// Delivery itself isn't arranged through the app — the seller sees
// the buyer's phone number on the order (every buyer account has one)
// and calls them directly to sort out where/how to deliver.
export default function OrderModal({ data: { stock, seller }, onClose }) {
  const [qty, setQty]       = useState(1)
  const [method, setMethod] = useState('mobile')
  const [loading, setLoading] = useState(false)

  const total = (qty * stock.price_per_kg).toFixed(2)

  const handleOrder = async () => {
    setLoading(true)
    try {
      const { data: order } = await placeOrder({
        seller_id: seller.id,
        items: [{ stock_id: stock.id, quantity_kg: qty }],
        payment_method: method,
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

        <p className="text-xs text-gray-400 mb-4">
          The seller will call the phone number on your account to arrange delivery.
        </p>

        <div className="bg-blue-50 rounded-lg p-3 mb-4 space-y-1">
          <p className="font-semibold text-blue-900 flex justify-between">
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

rewrite_file(
    FRONTEND / "components" / "orders" / "OrderModal.jsx",
    "agencies",
    ORDER_MODAL_NEW,
    "Rewrite OrderModal (remove agency select + delivery address + delivery fee)",
)


# ═══════════════════════════════════════════════════════════════════
# 11. FRONTEND — SellerPage.jsx (drop Delivery Agencies block)
# ═══════════════════════════════════════════════════════════════════
print("\n=== 11. SellerPage.jsx ===")

SELLER_PAGE_NEW = """import { useState } from 'react'
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
    refetchInterval: 20000,     // stocks refresh every 20 s
    staleTime: 0,
  })

  if (isLoading) return <div className="p-8">Loading seller…</div>

  const { seller, stocks } = data

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
                  onClick={() => setOrderItem({ stock, seller })}
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

rewrite_file(
    FRONTEND / "pages" / "market" / "SellerPage.jsx",
    "agencies",
    SELLER_PAGE_NEW,
    "Rewrite SellerPage (remove Delivery Agencies block)",
)


# ═══════════════════════════════════════════════════════════════════
# 12. FRONTEND — BuyerDashboard.jsx (drop delivery tracking/confirm)
# ═══════════════════════════════════════════════════════════════════
print("\n=== 12. BuyerDashboard.jsx ===")

BUYER_DASHBOARD_NEW = """import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Fish, MapPin, Receipt } from 'lucide-react'
import { getOrders, cancelOrder } from '../../api/orders'
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

rewrite_file(
    FRONTEND / "pages" / "dashboard" / "BuyerDashboard.jsx",
    "confirmDelivery",
    BUYER_DASHBOARD_NEW,
    "Rewrite BuyerDashboard (remove delivery status + Confirm Delivery)",
)


# ═══════════════════════════════════════════════════════════════════
# 13. FRONTEND — SellerDashboard.jsx (drop Delivery Partners tab,
#     drop delivery fields, show buyer phone in Manage Orders too)
# ═══════════════════════════════════════════════════════════════════
print("\n=== 13. SellerDashboard.jsx ===")

SELLER_DASHBOARD_NEW = """import { useState } from 'react'
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
  LockIcon, LogoutIcon,
} from '../../components/dashboard/Icons'

const SECTIONS = [
  { key: 'home',     label: 'Home',              icon: HomeIcon },
  { key: 'orders',   label: 'Manage Orders',     icon: ClipboardListIcon },
  { key: 'stocks',   label: 'Manage Stocks',     icon: PackageIcon },
  { key: 'buyers',   label: 'Manage Buyers',     icon: ContactIcon },
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
// Shows the buyer's phone number on every order so the seller can call
// them directly about delivery or anything else — there's no in-app
// delivery tracking, this is the handoff point to a real phone call.
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
                {order.buyer?.phone && (
                  <p className="text-gray-500 text-sm">Call buyer: {order.buyer.phone}</p>
                )}
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
"""

rewrite_file(
    FRONTEND / "pages" / "dashboard" / "SellerDashboard.jsx",
    "Delivery Partners",
    SELLER_DASHBOARD_NEW,
    "Rewrite SellerDashboard (remove Delivery Partners tab + show buyer phone in Manage Orders)",
)


# ═══════════════════════════════════════════════════════════════════
# 14. FRONTEND — BuyerSignupModal.jsx: phone becomes mandatory
# ═══════════════════════════════════════════════════════════════════
print("\n=== 14. BuyerSignupModal.jsx — required phone ===")

buyer_signup = FRONTEND / "components" / "auth" / "BuyerSignupModal.jsx"
patch(
    buyer_signup,
    """    if (form.phone !== '+255' && !isCompleteTzPhone(form.phone)) {
      setError('Phone number must be +255 followed by exactly 9 digits')
      return
    }""",
    """    if (!isCompleteTzPhone(form.phone)) {
      setError('A valid Tanzanian phone number (+255 followed by 9 digits) is required')
      return
    }""",
    "Require complete TZ phone before submit",
)
patch(
    buyer_signup,
    "        phone: form.phone === '+255' ? null : form.phone,",
    "        phone: form.phone,",
    "Always send phone (no longer optional)",
)
patch(
    buyer_signup,
    """        <Field
          icon={Phone}
          placeholder="+255 7XX XXX XXX"
          value={form.phone}
          onChange={handlePhoneChange}
        />""",
    """        <Field
          icon={Phone}
          placeholder="+255 7XX XXX XXX (required)"
          value={form.phone}
          onChange={handlePhoneChange}
        />
        <p className="text-xs text-gray-400 -mt-2 ml-1">
          Sellers use this number to call you about delivery.
        </p>""",
    "Note why phone is required under the field",
)


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
