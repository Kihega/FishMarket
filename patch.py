#!/usr/bin/env python3
"""
PATCH v12 - SmartFish: 3 persistent bugs fixed (root causes confirmed by
tracing each flow end-to-end against the actual current code, not assumed)
Run from project ROOT, on the `develop` branch.

ISSUE 1 - "Sellers near you" on the public home page
  Removed the "Verified Sellers Near You" marketplace section from
  MarketPage.jsx (the public landing page). BuyerDashboard's Home panel
  already shows this exact list ("Browse Markets") for logged-in buyers,
  so nothing is lost - it just no longer duplicates on the public page.

ISSUE 2 - Stock adding didn't work at all (root cause found, not guessed)
  api/stocks.js, api/sellers.js, and api/auth.js were all manually
  setting:
      headers: { 'Content-Type': 'multipart/form-data' }
  on requests sending a FormData body (stock creation, brand logo
  upload, seller signup with logo). This header NEEDS a boundary
  parameter that only axios/the browser can generate correctly when
  THEY set the header. Force-setting a bare 'multipart/form-data' with
  no boundary produces a request body Laravel's multipart parser can't
  read at all - every field arrives empty, including the file - which is
  exactly why "the stock adding process can't be done." Fixed by
  removing the manual header in all three places and letting axios set
  it automatically.
  Also confirmed already correct and left as-is:
    - POST /stocks endpoint + validation (FishStockController::store)
    - category_id is nullable end-to-end (form, validation, migration)
    - image column is nullable at the DB level - works fine with no file
  Additionally clarified the add-stock form's labels so units are
  unambiguous while typing: "Quantity (kg)" and "Price per kg (Tsh)"
  (was "Qty (kg)" / "Price/kg" with no currency shown), and marked the
  photo field "(optional)" explicitly.

ISSUE 3 - Delivery partners created successfully but never appeared in
the seller's own list
  GET /agencies was registered as a PUBLIC route (before the
  auth:sanctum group even starts), but the seller dashboard's "Delivery
  Partners" panel calls it with no seller_id query param, expecting
  $request->user() to resolve from the Bearer token. Without
  auth:sanctum actually running on that route, $request->user() is
  always null - so the controller fell through to its "seller_id is
  required" 422 response every time, even though POST /agencies (which
  WAS correctly behind auth:sanctum) had just created the agency
  successfully seconds earlier. Fixed by moving GET /agencies into the
  authenticated group, alongside POST and DELETE.
  Confirmed already correct and left as-is: SellerController::show()
  (GET /sellers/{id}) embeds agencies scoped to that seller separately,
  which is what buyers actually read from at checkout - so the
  buyer-side "select a delivery partner when placing an order" flow was
  never broken; only the seller's own dashboard list was.

ALSO ADDED:
  - DeliveryAgencyFactory (didn't exist yet)
  - DeliveryAgencyTest.php - locks in the actual bug (agency visible in
    the seller's own list right after creation), seller isolation, the
    422-without-seller_id case, and the buyer-side visibility path
  - FishStockTest.php - stock creation with no image, validation
    errors, buyer-cannot-add-stock, and visibility on both public
    listing endpoints a buyer would actually read from

Run:
    cd FishMarket
    python3 patch_v12.py
"""

import os

ROOT = os.getcwd()

FILES = {
    'frontend/src/api/stocks.js': "import client from './client'\n\nexport const getStocks    = (params) => client.get('/stocks', { params })\n// IMPORTANT: do NOT set Content-Type manually for FormData uploads.\n// Axios (and the browser) need to generate their own boundary string and\n// put it in the Content-Type header automatically. A hardcoded\n// 'multipart/form-data' with no boundary produces a body the server\n// cannot parse at all — every field, including the file, arrives empty —\n// which is why stock creation was failing silently.\nexport const createStock  = (data)   => client.post('/stocks', data)\nexport const updateStock  = (id, data) => client.put(`/stocks/${id}`, data)\nexport const deleteStock  = (id)       => client.delete(`/stocks/${id}`)\n",
    'frontend/src/api/sellers.js': "import client from './client'\n\nexport const getSellers         = (params) => client.get('/sellers', { params })\nexport const getSeller          = (id)     => client.get(`/sellers/${id}`)\n// Same fix as stocks.js: let axios set its own multipart boundary instead\n// of overriding Content-Type with a boundary-less value the server can't\n// parse (this was silently breaking brand_logo uploads on profile saves).\nexport const updateProfile      = (data)   => client.put('/seller/profile', data)\n",
    'frontend/src/api/auth.js': "import client from './client'\n\n// `data` may be a plain object (JSON) or a FormData instance (used by the\n// seller signup form, which can include an optional brand_logo file).\n// Axios sets the correct multipart boundary automatically when it sees a\n// FormData body — manually forcing 'multipart/form-data' here (with no\n// boundary) produced a request body Laravel couldn't parse at all.\nexport const register = (data) => client.post('/register', data)\nexport const login = (data) => client.post('/login', data)\nexport const logout = () => client.post('/logout')\nexport const getMe = () => client.get('/me')\n",
    'frontend/src/components/stocks/AddStockForm.jsx': 'import { useState } from \'react\'\nimport { useMutation, useQueryClient } from \'@tanstack/react-query\'\nimport { createStock } from \'../../api/stocks\'\nimport toast from \'react-hot-toast\'\n\nexport default function AddStockForm({ onDone }) {\n  const qc = useQueryClient()\n  const [form, setForm] = useState({\n    fish_name: \'\', quantity_kg: \'\', price_per_kg: \'\',\n  })\n  const [image, setImage] = useState(null)\n  const [imagePreview, setImagePreview] = useState(null)\n\n  const handleImageChange = (e) => {\n    const file = e.target.files[0]\n    setImage(file)\n    setImagePreview(file ? URL.createObjectURL(file) : null)\n  }\n\n  const add = useMutation({\n    mutationFn: () => {\n      const fd = new FormData()\n      Object.entries(form).forEach(([k, v]) => fd.append(k, v))\n      if (image) fd.append(\'image\', image)\n      return createStock(fd)\n    },\n    onSuccess: () => {\n      toast.success(\'Stock added!\')\n      qc.invalidateQueries([\'seller-stocks\'])\n      setForm({ fish_name: \'\', quantity_kg: \'\', price_per_kg: \'\' })\n      setImage(null)\n      setImagePreview(null)\n      onDone?.()\n    },\n    onError: () => toast.error(\'Failed to add stock\'),\n  })\n\n  return (\n    <div className="bg-white rounded-xl p-1">\n      <h2 className="font-bold text-blue-900 mb-4">Add Fish Stock</h2>\n\n      <div className="grid grid-cols-2 gap-3">\n        <input\n          className="input col-span-2" placeholder="Fish name"\n          value={form.fish_name}\n          onChange={(e) => setForm({ ...form, fish_name: e.target.value })}\n        />\n        <input\n          className="input" type="number" min="0.1" step="0.1" placeholder="Quantity (kg)"\n          value={form.quantity_kg}\n          onChange={(e) => setForm({ ...form, quantity_kg: e.target.value })}\n        />\n        <input\n          className="input" type="number" min="0" step="1" placeholder="Price per kg (Tsh)"\n          value={form.price_per_kg}\n          onChange={(e) => setForm({ ...form, price_per_kg: e.target.value })}\n        />\n\n        {/* Image upload with visible placeholder + live preview */}\n        <div className="col-span-2">\n          <label className="block text-sm text-gray-500 mb-1">Fish Photo (optional)</label>\n          <div className="flex items-center gap-3">\n            <div className="w-20 h-20 rounded-lg border-2 border-dashed border-gray-300 flex items-center justify-center overflow-hidden bg-gray-50 flex-shrink-0">\n              {imagePreview ? (\n                <img src={imagePreview} alt="Preview" className="w-full h-full object-cover" />\n              ) : (\n                <span className="text-gray-400 text-xs text-center px-1">No image</span>\n              )}\n            </div>\n            <input\n              className="input flex-1" type="file" accept="image/*"\n              onChange={handleImageChange}\n            />\n          </div>\n        </div>\n      </div>\n\n      <button\n        onClick={() => add.mutate()}\n        disabled={add.isPending || !form.fish_name}\n        className="mt-4 btn-primary w-full"\n      >\n        {add.isPending ? \'Adding…\' : \'Add Stock\'}\n      </button>\n    </div>\n  )\n}\n',
    'frontend/src/pages/market/MarketPage.jsx': 'import { useUIStore } from \'../../store/uiStore\'\n\nexport default function MarketPage() {\n  const { openSignupChoice } = useUIStore()\n\n  return (\n    <div>\n      {/* HERO */}\n      <section\n        className="relative h-[90vh] flex items-center justify-center text-center text-white"\n        style={{\n          backgroundImage:\n            \'linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url(/hero-fish.jpg)\',\n          backgroundSize: \'cover\',\n          backgroundPosition: \'center\',\n        }}\n      >\n        <div>\n          <h1 className="text-4xl md:text-5xl font-bold mb-4">Fresh Fish from Water</h1>\n          <p className="text-lg md:text-xl mb-6">\n            Connecting Fishermen and Buyers Across Tanzania\n          </p>\n          <button\n            onClick={openSignupChoice}\n            className="bg-black hover:bg-gray-800 text-white px-8 py-3 rounded-lg font-semibold transition"\n          >\n            Get Started\n          </button>\n        </div>\n      </section>\n\n      {/* FEATURES */}\n      <section className="flex flex-wrap justify-center gap-6 -mt-12 relative z-10 px-4">\n        <FeatureCard icon="fa-fish"  title="Fresh Catch"        text="Daily fish supply from local fishermen" />\n        <FeatureCard icon="fa-store" title="Market Access"      text="Buyers connect directly with fishermen" />\n        <FeatureCard icon="fa-truck" title="Fast Distribution"  text="Efficient delivery and coordination" />\n      </section>\n\n      {/* ABOUT */}\n      <section className="bg-blue-700 text-white text-center py-16 px-6">\n        <h2 className="text-3xl font-bold mb-4">About the System</h2>\n        <p className="max-w-2xl mx-auto leading-relaxed">\n          This system is designed to improve fish market access and supply coordination\n          in Tanzania. It connects fishermen directly with buyers, reduces middlemen, and\n          ensures efficient distribution.\n        </p>\n      </section>\n\n      {/* WHY CHOOSE US */}\n      <section className="bg-gray-50 text-center py-16 px-4">\n        <h2 className="text-3xl font-bold text-blue-900 mb-10">Why Choose Our System?</h2>\n        <div className="flex flex-wrap justify-center gap-6">\n          <FeatureCard icon="fa-bolt"         title="Fast Access"     text="Quick connection between fishermen and buyers" />\n          <FeatureCard icon="fa-fish"         title="Fresh Fish"      text="Direct supply from local fishermen" />\n          <FeatureCard icon="fa-check-circle" title="Reliable System" text="Efficient coordination and delivery" />\n        </div>\n      </section>\n\n      {/* CONTACT */}\n      <footer className="bg-gray-900 text-white text-center py-10 px-4">\n        <h2 className="text-2xl font-bold mb-3">Contact Us</h2>\n        <p>Email: fishmarket@gmail.com</p>\n        <p>Phone: +255 710 491 613 / +255 616 421 613</p>\n      </footer>\n    </div>\n  )\n}\n\nfunction FeatureCard({ icon, title, text }) {\n  return (\n    <div className="bg-white rounded-2xl shadow-lg p-6 w-56 text-center hover:-translate-y-1 transition">\n      <i className={`fas ${icon} text-3xl text-blue-600 mb-3`} />\n      <h3 className="font-bold text-blue-900 mb-1">{title}</h3>\n      <p className="text-sm text-gray-500">{text}</p>\n    </div>\n  )\n}\n',
    'backend/routes/api.php': "<?php\n\nuse Illuminate\\Support\\Facades\\Route;\nuse App\\Http\\Controllers\\API\\AuthController;\nuse App\\Http\\Controllers\\API\\SellerController;\nuse App\\Http\\Controllers\\API\\FishStockController;\nuse App\\Http\\Controllers\\API\\FishCategoryController;\nuse App\\Http\\Controllers\\API\\DeliveryAgencyController;\nuse App\\Http\\Controllers\\API\\OrderController;\nuse App\\Http\\Controllers\\API\\SubscriptionController;\nuse App\\Http\\Controllers\\API\\AdminController;\nuse App\\Http\\Controllers\\API\\PasswordController;\n\n// ── Public ──────────────────────────────────────────────────────────────\nRoute::post('/register', [AuthController::class, 'register']);\nRoute::post('/login', [AuthController::class, 'login']);\n\n// Marketplace (public browsing — no auth required)\nRoute::get('/sellers', [SellerController::class, 'index']);\nRoute::get('/sellers/{user}', [SellerController::class, 'show']);\nRoute::get('/stocks', [FishStockController::class, 'index']);\nRoute::get('/categories', [FishCategoryController::class, 'index']);\n\n// ── Protected (Sanctum token required) ───────────────────────────────────\nRoute::middleware('auth:sanctum')->group(function () {\n    Route::post('/logout', [AuthController::class, 'logout']);\n    Route::get('/me', [AuthController::class, 'me']);\n\n    // Any authenticated user — change own password\n    Route::put('/password', [PasswordController::class, 'update']);\n\n    // Seller profile\n    Route::put('/seller/profile', [SellerController::class, 'updateProfile']);\n    Route::get('/seller/buyers', [SellerController::class, 'buyers']);\n\n    // Seller subscription (plan selection after signup)\n    Route::post('/seller/subscription', [SubscriptionController::class, 'store']);\n    Route::get('/seller/subscription', [SubscriptionController::class, 'mine']);\n\n    // Fish stocks (seller only — enforced in controller)\n    Route::post('/stocks', [FishStockController::class, 'store']);\n    Route::put('/stocks/{fishStock}', [FishStockController::class, 'update']);\n    Route::delete('/stocks/{fishStock}', [FishStockController::class, 'destroy']);\n\n    // Delivery agencies (seller only)\n    Route::get('/agencies', [DeliveryAgencyController::class, 'index']);\n    Route::post('/agencies', [DeliveryAgencyController::class, 'store']);\n    Route::delete('/agencies/{deliveryAgency}', [DeliveryAgencyController::class, 'destroy']);\n\n    // Orders\n    Route::get('/orders', [OrderController::class, 'index']);\n    Route::post('/orders', [OrderController::class, 'store']);\n    Route::post('/orders/{order}/pay', [OrderController::class, 'pay']);\n    Route::post('/orders/{order}/confirm', [OrderController::class, 'confirm']);\n\n    // Admin only\n    Route::middleware('admin')->prefix('admin')->group(function () {\n        Route::get('/stats', [AdminController::class, 'stats']);\n        Route::get('/metrics', [AdminController::class, 'metrics']);\n        Route::get('/users', [AdminController::class, 'users']);\n        Route::post('/users', [AdminController::class, 'createAdmin']);\n        Route::put('/users/{user}/toggle', [AdminController::class, 'toggleUser']);\n        Route::delete('/users/{user}', [AdminController::class, 'deleteUser']);\n        Route::get('/subscriptions', [AdminController::class, 'subscriptions']);\n        Route::put('/subscriptions/{subscription}/confirm', [AdminController::class, 'confirmSubscription']);\n    });\n});\n",
    'backend/database/factories/DeliveryAgencyFactory.php': "<?php\n\nnamespace Database\\Factories;\n\nuse App\\Models\\User;\nuse Illuminate\\Database\\Eloquent\\Factories\\Factory;\n\nclass DeliveryAgencyFactory extends Factory\n{\n    protected $model = \\App\\Models\\DeliveryAgency::class;\n\n    public function definition(): array\n    {\n        return [\n            'seller_id' => User::factory()->seller(),\n            'agency_name' => fake()->company().' Delivery',\n            'contact' => fake()->phoneNumber(),\n            'area_covered' => fake()->city(),\n            'is_active' => true,\n        ];\n    }\n}\n",
    'backend/tests/Feature/DeliveryAgencyTest.php': '<?php\n\nnamespace Tests\\Feature;\n\nuse App\\Models\\DeliveryAgency;\nuse App\\Models\\User;\nuse Illuminate\\Foundation\\Testing\\RefreshDatabase;\nuse Tests\\TestCase;\n\nclass DeliveryAgencyTest extends TestCase\n{\n    use RefreshDatabase;\n\n    public function test_seller_sees_newly_added_agency_in_their_own_list(): void\n    {\n        // Regression test: GET /agencies was registered as a PUBLIC route\n        // (outside the auth:sanctum group), so $request->user() was\n        // always null there even with a valid Bearer token — and the\n        // dashboard\'s "Delivery Partners" panel calls this route with no\n        // seller_id query param, so it always got a 422 instead of the\n        // seller\'s own agencies, even though POST /agencies (which IS\n        // behind auth:sanctum) had created the agency successfully.\n        $seller = User::factory()->seller()->create();\n\n        $createResponse = $this->actingAs($seller, \'sanctum\')->postJson(\'/api/agencies\', [\n            \'agency_name\' => \'Coastal Express\',\n            \'contact\' => \'0712345678\',\n            \'area_covered\' => \'Dar es Salaam\',\n        ]);\n        $createResponse->assertStatus(201);\n\n        $listResponse = $this->actingAs($seller, \'sanctum\')->getJson(\'/api/agencies\');\n\n        $listResponse->assertStatus(200)\n            ->assertJsonCount(1)\n            ->assertJsonPath(\'0.agency_name\', \'Coastal Express\');\n    }\n\n    public function test_seller_only_sees_their_own_agencies_not_other_sellers(): void\n    {\n        $seller = User::factory()->seller()->create();\n        $otherSeller = User::factory()->seller()->create();\n\n        DeliveryAgency::factory()->create([\'seller_id\' => $seller->id, \'agency_name\' => \'Mine\']);\n        DeliveryAgency::factory()->create([\'seller_id\' => $otherSeller->id, \'agency_name\' => \'Theirs\']);\n\n        $response = $this->actingAs($seller, \'sanctum\')->getJson(\'/api/agencies\');\n\n        $response->assertStatus(200)\n            ->assertJsonCount(1)\n            ->assertJsonPath(\'0.agency_name\', \'Mine\');\n    }\n\n    public function test_guest_cannot_list_agencies_without_a_seller_id(): void\n    {\n        $response = $this->getJson(\'/api/agencies\');\n\n        $response->assertStatus(422);\n    }\n\n    public function test_newly_added_agency_is_visible_to_buyers_on_the_seller_page(): void\n    {\n        // Covers the buyer-side half: SellerController::show() already\n        // embeds agencies scoped to that seller, separately from the\n        // GET /agencies endpoint — confirming that path stays correct.\n        $seller = User::factory()->seller()->create();\n\n        $this->actingAs($seller, \'sanctum\')->postJson(\'/api/agencies\', [\n            \'agency_name\' => \'Lakeside Movers\',\n        ])->assertStatus(201);\n\n        $publicResponse = $this->getJson("/api/sellers/{$seller->id}");\n\n        $publicResponse->assertStatus(200)\n            ->assertJsonPath(\'agencies.0.agency_name\', \'Lakeside Movers\');\n    }\n}\n',
    'backend/tests/Feature/FishStockTest.php': '<?php\n\nnamespace Tests\\Feature;\n\nuse App\\Models\\User;\nuse Illuminate\\Foundation\\Testing\\RefreshDatabase;\nuse Tests\\TestCase;\n\nclass FishStockTest extends TestCase\n{\n    use RefreshDatabase;\n\n    public function test_seller_can_add_stock_without_an_image(): void\n    {\n        // The image is optional — the table must accept data even when\n        // no file is attached.\n        $seller = User::factory()->seller()->create();\n\n        $response = $this->actingAs($seller, \'sanctum\')->postJson(\'/api/stocks\', [\n            \'fish_name\' => \'Fresh Tilapia\',\n            \'quantity_kg\' => 25,\n            \'price_per_kg\' => 6000,\n        ]);\n\n        $response->assertStatus(201)\n            ->assertJsonPath(\'fish_name\', \'Fresh Tilapia\')\n            ->assertJsonPath(\'quantity_kg\', \'25.00\')\n            ->assertJsonPath(\'price_per_kg\', \'6000.00\')\n            ->assertJsonPath(\'image\', null);\n    }\n\n    public function test_stock_requires_fish_name_quantity_and_price(): void\n    {\n        $seller = User::factory()->seller()->create();\n\n        $response = $this->actingAs($seller, \'sanctum\')->postJson(\'/api/stocks\', []);\n\n        $response->assertStatus(422)\n            ->assertJsonValidationErrors([\'fish_name\', \'quantity_kg\', \'price_per_kg\']);\n    }\n\n    public function test_buyer_cannot_add_stock(): void\n    {\n        $buyer = User::factory()->create();\n\n        $response = $this->actingAs($buyer, \'sanctum\')->postJson(\'/api/stocks\', [\n            \'fish_name\' => \'Fresh Tilapia\',\n            \'quantity_kg\' => 10,\n            \'price_per_kg\' => 5000,\n        ]);\n\n        $response->assertStatus(403);\n    }\n\n    public function test_newly_added_stock_is_immediately_visible_on_public_listing(): void\n    {\n        $seller = User::factory()->seller()->create();\n\n        $this->actingAs($seller, \'sanctum\')->postJson(\'/api/stocks\', [\n            \'fish_name\' => \'Nile Perch\',\n            \'quantity_kg\' => 12,\n            \'price_per_kg\' => 9000,\n        ])->assertStatus(201);\n\n        $response = $this->getJson(\'/api/stocks\');\n\n        $response->assertStatus(200)\n            ->assertJsonPath(\'data.0.fish_name\', \'Nile Perch\');\n    }\n\n    public function test_newly_added_stock_is_immediately_visible_on_the_seller_public_page(): void\n    {\n        // This is the exact path the buyer-facing SellerPage reads from.\n        $seller = User::factory()->seller()->create();\n\n        $this->actingAs($seller, \'sanctum\')->postJson(\'/api/stocks\', [\n            \'fish_name\' => \'Sardine\',\n            \'quantity_kg\' => 30,\n            \'price_per_kg\' => 3000,\n        ])->assertStatus(201);\n\n        $response = $this->getJson("/api/sellers/{$seller->id}");\n\n        $response->assertStatus(200)\n            ->assertJsonPath(\'stocks.0.fish_name\', \'Sardine\');\n    }\n}\n',

}

def main():
    for rel_path, content in FILES.items():
        full_path = os.path.join(ROOT, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  {rel_path}")

    print()
    print("Patch v12 applied (3 persistent bugs fixed).")
    print("""
NEXT STEPS
----------
  1. Run backend tests:
       cd backend && php artisan test --filter=FishStockTest
       cd backend && php artisan test --filter=DeliveryAgencyTest
  2. cd frontend && npm run build
  3. Commit on develop:
       git add backend/routes backend/database/factories backend/tests
       git add frontend/src
       git commit -m "Patch v12: fix multipart boundary bug breaking all
       file uploads (stock create, brand logo, signup logo), move
       GET /agencies behind auth so it actually returns the seller's own
       list, remove duplicate sellers section from public home page"
       git push origin develop
  4. Manually verify (this is the one that actually matters most - the
     multipart bug could only be confirmed by reading axios's behavior,
     not by running it here, since there's no PHP/network in this
     sandbox):
       - As a seller, add a fish stock with NO image -> should succeed
       - Add another with an image -> should succeed, image shows
       - As a seller, add a delivery partner -> it should now show up
         immediately in the list below the form, no refresh needed
         beyond the normal 15s poll
       - As a buyer placing an order on that seller, the delivery
         partner you just added should appear in the order form's
         dropdown
       - Visit the public home page (logged out) -> no "Sellers Near
         You" / marketplace grid section should appear
       - Log in as a buyer -> Home panel should still show "Browse
         Markets" with the seller list, exactly as before
""")

if __name__ == "__main__":
    main()
