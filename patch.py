#!/usr/bin/env python3
"""
PATCH v15 - SmartFish: fix delivery_fee showing as null instead of 0.00
right after creating an agency with no fee specified
Run from project ROOT, on the `develop` branch.

WHAT THE CI RUN ACTUALLY SHOWED:
  59 of 60 tests passed - every v14 fix held up (stock creation, order
  placement with/without an agency, the delivery fee snapshot itself,
  cross-seller checks, all of it). The one failure was a real bug in
  v14's DeliveryAgencyController, not a bad test:

    FAILED  DeliveryAgencyTest > agency delivery fee defaults to zero
            when not given
    Failed asserting that null is identical to '0.00'.

ROOT CAUSE:
  When delivery_fee isn't sent in the request at all, Laravel's
  $request->validate() simply OMITS that key from the returned array
  (it does not insert a null placeholder). That means
  ->create([...]) never passed delivery_fee to the insert, so Eloquent
  relied on the column's DB-level default(0) (set in v14's migration)
  to fill it in - which works fine for the actual database row, but
  Eloquent's create() does NOT re-fetch a row after inserting it to
  pick up server-side DEFAULT values for any column other than the
  auto-increment id. So the in-memory $agency object handed back to
  response()->json($agency, 201) genuinely had delivery_fee as null in
  PHP, even though the database itself correctly stored 0.00.
  (This only affected the immediate creation response. Everywhere else
  that reads delivery_fee - including OrderController::store(), which
  does a fresh DeliveryAgency::where(...)->first() - re-queries the
  database directly and was already getting the correct 0.00. Only the
  create() response itself was wrong.)

THE FIX:
  DeliveryAgencyController::store() now explicitly defaults
  delivery_fee to 0 in PHP ($data['delivery_fee'] ?? 0) before calling
  create(), instead of relying on the DB column default to silently
  backfill an in-memory object that Eloquent never re-reads.

Run:
    cd FishMarket
    python3 patch_v15.py
"""

import os

ROOT = os.getcwd()

FILES = {
    'backend/app/Http/Controllers/API/DeliveryAgencyController.php': "<?php\n\nnamespace App\\Http\\Controllers\\API;\n\nuse App\\Http\\Controllers\\Controller;\nuse App\\Models\\DeliveryAgency;\nuse Illuminate\\Http\\Request;\n\nclass DeliveryAgencyController extends Controller\n{\n    // Public: agencies belonging to a given seller\n    public function index(Request $request)\n    {\n        $sellerId = $request->seller_id ?? $request->user()?->id;\n\n        if (! $sellerId) {\n            return response()->json(['message' => 'seller_id is required'], 422);\n        }\n\n        return response()->json(\n            DeliveryAgency::where('seller_id', $sellerId)->where('is_active', true)->get()\n        );\n    }\n\n    // Seller: register a delivery partnership agency\n    public function store(Request $request)\n    {\n        abort_unless($request->user()->role === 'seller', 403);\n\n        $data = $request->validate([\n            'agency_name' => 'required|string',\n            'contact' => 'nullable|string',\n            'area_covered' => 'nullable|string',\n            // Every agency may charge a different fee depending on the\n            // area it serves, so it's set once here at registration\n            // rather than per order.\n            'delivery_fee' => 'nullable|numeric|min:0',\n        ]);\n\n        // validate() simply omits delivery_fee from $data when it's not\n        // sent at all (rather than setting it to null), so without this\n        // the column's DB-level default(0) would apply to the actual\n        // row, but the in-memory $agency object returned by create()\n        // below is never backfilled with that server-side default —\n        // Eloquent only re-reads the auto-increment id after an insert,\n        // not other columns — so the JSON response would show null\n        // even though the database itself correctly stored 0.\n        $data['delivery_fee'] = $data['delivery_fee'] ?? 0;\n\n        $agency = $request->user()->deliveryAgencies()->create($data);\n\n        return response()->json($agency, 201);\n    }\n\n    // Seller: remove (soft-deactivate) a delivery agency\n    public function destroy(Request $request, DeliveryAgency $deliveryAgency)\n    {\n        abort_unless($deliveryAgency->seller_id === $request->user()->id, 403);\n        $deliveryAgency->update(['is_active' => false]);\n\n        return response()->json(null, 204);\n    }\n}\n",

}

def main():
    for rel_path, content in FILES.items():
        full_path = os.path.join(ROOT, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  {rel_path}")

    print()
    print("Patch v15 applied (1 bug fixed: delivery_fee null on creation).")
    print("""
NEXT STEPS
----------
  1. Run backend tests:
       cd backend && php artisan test --filter=DeliveryAgencyTest
     All tests in this file should now pass.
  2. Commit on develop:
       git add backend/app/Http/Controllers/API/DeliveryAgencyController.php
       git commit -m "Patch v15: fix delivery_fee returning null instead
       of 0.00 right after creating an agency with no fee specified"
       git push origin develop
  3. Confirm GitHub Actions is fully green.
""")

if __name__ == "__main__":
    main()
