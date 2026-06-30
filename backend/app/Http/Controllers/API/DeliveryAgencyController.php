<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\DeliveryAgency;
use Illuminate\Http\Request;

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
