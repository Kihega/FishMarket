<?php
namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\FishListing;
use Illuminate\Http\Request;

class FishListingController extends Controller
{
    public function index(Request $request)
    {
        $query = FishListing::with('fisher')->where('status', 'available');

        if ($request->species)   $query->where('species', 'like', "%{$request->species}%");
        if ($request->location)  $query->where('location', 'like', "%{$request->location}%");
        if ($request->max_price) $query->where('price_per_kg', '<=', $request->max_price);

        return response()->json($query->latest()->paginate(20));
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'species'       => 'required|string',
            'quantity_kg'   => 'required|numeric|min:0.1',
            'price_per_kg'  => 'required|numeric|min:0',
            'location'      => 'required|string',
            'description'   => 'nullable|string',
            'image'         => 'nullable|image|max:2048',
        ]);

        if ($request->hasFile('image')) {
            $data['image'] = $request->file('image')->store('listings', 'public');
        }

        $listing = $request->user()->fishListings()->create($data);

        return response()->json($listing, 201);
    }

    public function show(FishListing $fishListing)
    {
        return response()->json($fishListing->load('fisher', 'orders'));
    }

    public function update(Request $request, FishListing $fishListing)
    {
        $this->authorize('update', $fishListing);
        $fishListing->update($request->validate([
            'species'      => 'sometimes|string',
            'quantity_kg'  => 'sometimes|numeric|min:0.1',
            'price_per_kg' => 'sometimes|numeric|min:0',
            'location'     => 'sometimes|string',
            'status'       => 'sometimes|in:available,sold,reserved',
        ]));
        return response()->json($fishListing);
    }

    public function destroy(FishListing $fishListing)
    {
        $this->authorize('delete', $fishListing);
        $fishListing->delete();
        return response()->json(null, 204);
    }
}
