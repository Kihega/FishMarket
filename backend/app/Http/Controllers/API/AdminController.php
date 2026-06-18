<?php
namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\{User, Subscription};
use Illuminate\Http\Request;

class AdminController extends Controller
{
    public function users(Request $request)
    {
        return response()->json(
            User::when($request->role, fn($q) => $q->where('role', $request->role))
                ->latest()->paginate(30)
        );
    }

    public function toggleUser(User $user)
    {
        $user->update(['is_active' => !$user->is_active]);
        return response()->json($user);
    }

    public function subscriptions()
    {
        return response()->json(
            Subscription::with('seller')->latest()->paginate(30)
        );
    }

    public function confirmSubscription(Subscription $subscription)
    {
        $subscription->update([
            'status'  => 'active',
            'paid_at' => now(),
        ]);
        $subscription->seller->update(['subscription_status' => 'active']);
        return response()->json($subscription);
    }

    public function stats()
    {
        return response()->json([
            'total_users'    => User::count(),
            'active_sellers' => User::where('role','seller')->where('subscription_status','active')->count(),
            'total_buyers'   => User::where('role','buyer')->count(),
            'pending_subs'   => Subscription::where('status','pending')->count(),
        ]);
    }
}
