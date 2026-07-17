#!/usr/bin/env python3
"""
patch_16.py

Run from the FishMarket project root (the folder that contains
`frontend/` and `backend/`):

    python3 patch_16.py

Fixes:
  1. In-app "Back" button on every page (Market / Seller / Dashboard /
     Admin) so users no longer have to rely on the browser's back icon.
  2. Delivery address: when a buyer places an order and picks a
     delivery agency, they must now type the exact physical location
     they want the order delivered to. It's saved on the order and
     shown to the seller in "Manage Buyers".

Safe to re-run: every change is guarded so already-patched files are
skipped instead of re-applied or corrupted.
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
    path.write_text(content, encoding="utf-8")


def patch(path: Path, old: str, new: str, label: str, already_marker: str = None):
    """
    Exact-string patch. Skips (idempotent) if `already_marker` (or `new`,
    when no marker given) is already present. Records a failure if
    neither the old nor the "already applied" state is found.
    """
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

    content = content.replace(old, new, 1)
    write(path, content)
    print(f"  [ok]   {label} — {path.name}")


def create_if_missing(path: Path, content: str, label: str):
    if path.exists():
        print(f"  [skip] {label} (file already exists) — {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    write(path, content)
    print(f"  [ok]   {label} — created {path.name}")


# ─────────────────────────────────────────────────────────────────────
# 1. BACK BUTTON
# ─────────────────────────────────────────────────────────────────────
print("\n=== 1. Back button ===")

BACK_BUTTON_JSX = """import { useNavigate, useLocation } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'

// Global in-app "Back" button. Shown on every page except the home
// page. Uses browser history when the user actually navigated here
// from somewhere inside the app (location.key !== 'default'); falls
// back to the home page when the page was opened directly (e.g. a
// refresh or a bookmarked/deep link), since there's no in-app history
// to go back to in that case.
export default function BackButton() {
  const navigate = useNavigate()
  const location = useLocation()

  if (location.pathname === '/') return null

  const handleBack = () => {
    if (location.key !== 'default') {
      navigate(-1)
    } else {
      navigate('/')
    }
  }

  return (
    <button
      onClick={handleBack}
      aria-label="Go back"
      className="flex items-center gap-1.5 text-white/90 hover:text-white transition text-sm font-medium mr-4"
    >
      <ArrowLeft className="w-5 h-5" />
      <span className="hidden sm:inline">Back</span>
    </button>
  )
}
"""

create_if_missing(
    FRONTEND / "components" / "layout" / "BackButton.jsx",
    BACK_BUTTON_JSX,
    "Create BackButton component",
)

navbar_path = FRONTEND / "components" / "layout" / "Navbar.jsx"
patch(
    navbar_path,
    "import { Link } from 'react-router-dom'\nimport { Fish } from 'lucide-react'",
    "import { Link } from 'react-router-dom'\nimport { Fish } from 'lucide-react'\nimport BackButton from './BackButton'",
    "Import BackButton in Navbar",
)
patch(
    navbar_path,
    '''  return (
    <header className="flex justify-between items-center px-8 py-4 bg-blue-700 text-white sticky top-0 z-40 shadow">
      <Link to="/" className="text-xl font-bold flex items-center gap-2">
        <Fish className="w-6 h-6" /> SmartFish
      </Link>
    </header>
  )''',
    '''  return (
    <header className="flex justify-between items-center px-8 py-4 bg-blue-700 text-white sticky top-0 z-40 shadow">
      <div className="flex items-center">
        <BackButton />
        <Link to="/" className="text-xl font-bold flex items-center gap-2">
          <Fish className="w-6 h-6" /> SmartFish
        </Link>
      </div>
    </header>
  )''',
    "Render BackButton next to logo in Navbar",
)

# ─────────────────────────────────────────────────────────────────────
# 2. DELIVERY ADDRESS — BACKEND
# ─────────────────────────────────────────────────────────────────────
print("\n=== 2. Delivery address (backend) ===")

migration_path = (
    BACKEND
    / "database"
    / "migrations"
    / "2026_07_17_000001_add_delivery_address_to_order_deliveries.php"
)
MIGRATION_CONTENT = """<?php

use Illuminate\\Database\\Migrations\\Migration;
use Illuminate\\Support\\Facades\\Schema;

/**
 * Buyers now enter the exact physical location they want their order
 * delivered to whenever they pick a delivery agency at checkout.
 * Stored on order_deliveries (same place delivery_fee is snapshotted)
 * so the seller/agency can see it in "Manage Buyers".
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::table('order_deliveries', function ($table) {
            $table->text('delivery_address')->nullable()->after('delivery_fee');
        });
    }

    public function down(): void
    {
        Schema::table('order_deliveries', function ($table) {
            $table->dropColumn('delivery_address');
        });
    }
};
"""
create_if_missing(migration_path, MIGRATION_CONTENT, "Create delivery_address migration")

order_delivery_model = BACKEND / "app" / "Models" / "OrderDelivery.php"
patch(
    order_delivery_model,
    "protected $fillable = [\n        'order_id', 'agency_id', 'delivery_fee', 'delivery_method', 'delivery_status',\n    ];",
    "protected $fillable = [\n        'order_id', 'agency_id', 'delivery_fee', 'delivery_address', 'delivery_method', 'delivery_status',\n    ];",
    "Add delivery_address to OrderDelivery fillable",
)

order_controller = BACKEND / "app" / "Http" / "Controllers" / "API" / "OrderController.php"

patch(
    order_controller,
    """            // Choosing a delivery agency is optional — a buyer may
            // arrange their own delivery instead.
            'agency_id' => 'nullable|exists:delivery_agencies,id',
            'delivery_method' => 'nullable|string',
        ]);""",
    """            // Choosing a delivery agency is optional — a buyer may
            // arrange their own delivery instead.
            'agency_id' => 'nullable|exists:delivery_agencies,id',
            'delivery_method' => 'nullable|string',
            // Required whenever an agency is chosen: the exact physical
            // location the buyer wants the order delivered to.
            'delivery_address' => 'nullable|string|max:500',
        ]);

        if (! empty($data['agency_id']) && empty(trim($data['delivery_address'] ?? ''))) {
            abort(422, 'Please enter the physical location for delivery.');
        }""",
    "Validate delivery_address when agency chosen",
)

patch(
    order_controller,
    """        if ($agency) {
            OrderDelivery::create([
                'order_id' => $order->id,
                'agency_id' => $agency->id,
                // Snapshotted at order time (like fish_name/price_per_kg
                // on OrderItem) so a later change to the agency's fee
                // never rewrites the cost of a past order.
                'delivery_fee' => $deliveryFee,
                'delivery_method' => $data['delivery_method'] ?? null,
            ]);
        }""",
    """        if ($agency) {
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
        }""",
    "Persist delivery_address on order",
)

# ─────────────────────────────────────────────────────────────────────
# 3. DELIVERY ADDRESS — SHOW TO SELLER
# ─────────────────────────────────────────────────────────────────────
print("\n=== 3. Delivery address (seller view) ===")

seller_controller = BACKEND / "app" / "Http" / "Controllers" / "API" / "SellerController.php"
patch(
    seller_controller,
    "'delivery_status' => $order->delivery?->delivery_status ?? 'pending',",
    "'delivery_status' => $order->delivery?->delivery_status ?? 'pending',\n                'delivery_address' => $order->delivery?->delivery_address,",
    "Expose delivery_address on seller buyers() endpoint",
)

seller_dashboard = FRONTEND / "pages" / "dashboard" / "SellerDashboard.jsx"
patch(
    seller_dashboard,
    """                <p className="text-xs text-gray-400 mt-1 capitalize">
                  Delivery: {b.delivery_status}
                </p>""",
    """                <p className="text-xs text-gray-400 mt-1 capitalize">
                  Delivery: {b.delivery_status}
                </p>
                {b.delivery_address && (
                  <p className="text-xs text-gray-400 mt-1 max-w-xs text-right">
                    Deliver to: {b.delivery_address}
                  </p>
                )}""",
    "Show delivery_address in seller Manage Buyers panel",
)

# ─────────────────────────────────────────────────────────────────────
# 4. DELIVERY ADDRESS — ORDER MODAL (BUYER INPUT)
# ─────────────────────────────────────────────────────────────────────
print("\n=== 4. Delivery address (order modal) ===")

order_modal = FRONTEND / "components" / "orders" / "OrderModal.jsx"

patch(
    order_modal,
    "  const [qty, setQty]       = useState(1)\n  // '' = no agency chosen yet, 'self' = buyer will arrange their own\n  // delivery, otherwise an agency id.\n  const [agency, setAgency] = useState('')",
    "  const [qty, setQty]       = useState(1)\n  // '' = no agency chosen yet, 'self' = buyer will arrange their own\n  // delivery, otherwise an agency id.\n  const [agency, setAgency] = useState('')\n  const [deliveryAddress, setDeliveryAddress] = useState('')",
    "Add deliveryAddress state",
)

patch(
    order_modal,
    """  const handleOrder = async () => {
    // Agency selection is optional — the buyer may arrange their own
    // delivery — so there's nothing to validate here beyond what the
    // <select> already allows.
    setLoading(true)
    try {
      const { data: order } = await placeOrder({
        seller_id: seller.id,
        items: [{ stock_id: stock.id, quantity_kg: qty }],
        payment_method: method,
        agency_id: selectedAgency ? selectedAgency.id : null,
      })""",
    """  const handleOrder = async () => {
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
      })""",
    "Validate + send delivery_address on order placement",
)

patch(
    order_modal,
    """        <p className="text-xs text-gray-400 mb-4">
          Choosing a delivery partner is optional — skip it if you have your own delivery arrangement.
        </p>""",
    """        <p className="text-xs text-gray-400 mb-4">
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
        )}""",
    "Render delivery location textarea when agency selected",
)

# ─────────────────────────────────────────────────────────────────────
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
    print("  frontend: no build step needed beyond your normal dev/build flow")
