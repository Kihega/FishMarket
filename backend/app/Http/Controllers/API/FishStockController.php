<?php
namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\FishStock;
use Illuminate\Http\Request;

class FishStockController extends Controller
{
    // Public: list stocks for a seller
    public function index(Request $request)
    {
        $sellerId = $request->seller_id;
        $query = FishStock::with('category')
            ->where('status', 'active')
            ->when($sellerId, fn($q) => $q->where('seller_id', $sellerId))
            ->when($request->category_id, fn($q) => $q->where('category_id', $request->category_id));

        return response()->json($query->latest()->paginate(20));
    }

    // Seller: create stock
    public function store(Request $request)
    {
        $this->ensureSeller($request);

        $data = $request->validate([
            'category_id'  => 'required|exists:fish_categories,id',
            'fish_name'    => 'required|string',
            'quantity_kg'  => 'required|numeric|min:0.1',
            'price_per_kg' => 'required|numeric|min:0',
            'image'        => 'nullable|image|max:3072',
        ]);

        if ($request->hasFile('image')) {
            $data['image'] = $request->file('image')->store('stocks', 'public');
        }

        $stock = $request->user()->fishStocks()->create($data);
        return response()->json($stock->load('category'), 201);
    }

    // Seller: update stock
    public function update(Request $request, FishStock $fishStock)
    {
        abort_unless($fishStock->seller_id === $request->user()->id, 403);

        $fishStock->update($request->validate([
            'fish_name'    => 'sometimes|string',
            'quantity_kg'  => 'sometimes|numeric|min:0',
            'price_per_kg' => 'sometimes|numeric|min:0',
            'status'       => 'sometimes|in:active,out_of_stock',
        ]));

        return response()->json($fishStock);
    }

    public function destroy(Request $request, FishStock $fishStock)
    {
        abort_unless($fishStock->seller_id === $request->user()->id, 403);
        $fishStock->delete();
        return response()->json(null, 204);
    }

    private function ensureSeller(Request $request): void
    {
        abort_unless($request->user()->role === 'seller', 403, 'Sellers only');
    }
}
