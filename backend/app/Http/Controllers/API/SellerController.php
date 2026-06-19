<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;

class SellerController extends Controller
{
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

    // Seller: update own profile
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
            $data['brand_logo'] = $request->file('brand_logo')->store('logos', 'public');
        }

        $user->update($data);

        return response()->json($user);
    }
}
