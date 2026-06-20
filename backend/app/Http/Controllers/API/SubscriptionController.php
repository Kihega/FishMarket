<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\Subscription;
use Illuminate\Http\Request;

class SubscriptionController extends Controller
{
    /**
     * Plan prices in TZS. Kept server-side so the frontend cannot
     * spoof the amount — only 'plan' is accepted from the client.
     */
    private const PLAN_PRICES = [
        'monthly' => 15000,
        'annual'  => 150000,
    ];

    /**
     * Seller creates a new subscription request for their account.
     * Status starts as 'pending' — an admin must confirm it before
     * the seller's account-level subscription_status becomes 'active'.
     *
     * Free tier never reaches this endpoint: the frontend only calls
     * it for 'monthly' or 'annual' plans (see SellerSignupModal.jsx).
     */
    public function store(Request $request)
    {
        $user = $request->user();
        abort_unless($user->role === 'seller', 403, 'Only sellers can subscribe.');

        $data = $request->validate([
            'plan' => 'required|in:monthly,annual',
        ]);

        // A seller should not be able to stack multiple pending
        // subscriptions — reuse the existing pending one if present.
        $subscription = Subscription::firstOrCreate(
            [
                'seller_id' => $user->id,
                'status'    => 'pending',
            ],
            [
                'plan'   => $data['plan'],
                'amount' => self::PLAN_PRICES[$data['plan']],
            ]
        );

        // If a pending subscription already existed with a different
        // plan, update it to reflect the seller's latest choice.
        if ($subscription->plan !== $data['plan']) {
            $subscription->update([
                'plan'   => $data['plan'],
                'amount' => self::PLAN_PRICES[$data['plan']],
            ]);
        }

        return response()->json($subscription, 201);
    }

    /**
     * Seller views their own subscription history.
     */
    public function mine(Request $request)
    {
        $user = $request->user();
        abort_unless($user->role === 'seller', 403, 'Only sellers can view this.');

        return response()->json(
            $user->subscriptions()->latest()->get()
        );
    }
}
