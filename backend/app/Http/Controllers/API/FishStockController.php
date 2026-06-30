<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\API\Concerns\StoresImages;
use App\Http\Controllers\Controller;
use App\Models\FishStock;
use Illuminate\Http\Request;

class FishStockController extends Controller
{
    use StoresImages;

    // Public: list stocks (optionally filtered by seller or category).
    // Marketplace-facing only — always 'active' rows. Left untouched.
    public function index(Request $request)
    {
        $query = FishStock::with('category')
            ->where('status', 'active')
            ->when($request->seller_id, fn ($q) => $q->where('seller_id', $request->seller_id))
            ->when($request->category_id, fn ($q) => $q->where('category_id', $request->category_id));

        return response()->json($query->latest()->paginate(20));
    }

    // Seller: own stock list for the "Manage Stocks" dashboard panel.
    // Unlike index() above, this is scoped strictly to the logged-in
    // seller (fixes stock leaking across sellers) and includes
    // out_of_stock items too, so a zeroed-out item stays visible for
    // the seller to top back up via Edit Stock.
    public function mine(Request $request)
    {
        abort_unless($request->user()->role === 'seller', 403, 'Sellers only');

        FishStock::pruneExpiredZeroStock();

        $stocks = FishStock::with('category')
            ->where('seller_id', $request->user()->id)
            ->latest()
            ->paginate(50);

        return response()->json($stocks);
    }

    // Seller: create stock
    public function store(Request $request)
    {
        abort_unless($request->user()->role === 'seller', 403, 'Sellers only');

        $data = $request->validate([
            'category_id' => 'nullable|exists:fish_categories,id',
            'fish_name' => 'required|string',
            'quantity_kg' => 'required|numeric|min:0.1',
            'price_per_kg' => 'required|numeric|min:0',
            'image' => 'nullable|image|max:3072',
        ]);

        if ($request->hasFile('image')) {
            $data['image'] = $this->storeImage($request->file('image'), 'stocks');
        }

        $stock = $request->user()->fishStocks()->create($data);

        return response()->json($stock->load('category'), 201);
    }

    // Seller: edit own stock (top up quantity and/or change price).
    // No "remove stock" path from the UI any more — a stock that stays
    // at 0.0kg for 7 days is pruned automatically instead (see
    // FishStock::pruneExpiredZeroStock). Status + zero_at are derived
    // automatically from the resulting quantity unless the caller
    // explicitly overrides 'status'.
    public function update(Request $request, FishStock $fishStock)
    {
        abort_unless($fishStock->seller_id === $request->user()->id, 403);

        $data = $request->validate([
            'fish_name' => 'sometimes|string',
            'quantity_kg' => 'sometimes|numeric|min:0',
            'price_per_kg' => 'sometimes|numeric|min:0',
            'status' => 'sometimes|in:active,out_of_stock',
        ]);

        if (array_key_exists('quantity_kg', $data) && ! array_key_exists('status', $data)) {
            if ((float) $data['quantity_kg'] <= 0) {
                $data['status'] = 'out_of_stock';
                $data['zero_at'] = $fishStock->zero_at ?? now();
            } else {
                // Restocked above zero — back to active, clear the
                // zero-quantity clock so it isn't pruned later.
                $data['status'] = 'active';
                $data['zero_at'] = null;
            }
        }

        $fishStock->update($data);

        return response()->json($fishStock->fresh('category'));
    }

    public function destroy(Request $request, FishStock $fishStock)
    {
        abort_unless($fishStock->seller_id === $request->user()->id, 403);
        $fishStock->delete();

        return response()->json(null, 204);
    }
}
