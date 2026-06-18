<?php
namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\DeliveryAgency;
use Illuminate\Http\Request;

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
