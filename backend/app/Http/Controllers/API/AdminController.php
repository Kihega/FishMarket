<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Models\FishStock;
use App\Models\Order;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Hash;

class AdminController extends Controller
{
    public function users(Request $request)
    {
        return response()->json(
            User::when($request->role, fn ($q) => $q->where('role', $request->role))
                ->latest()
                ->paginate(30)
        );
    }

    /**
     * Admin registers a NEW admin account. Requires an authenticated
     * admin token to call — the very first admin must instead be
     * created via the `php artisan admin:create-first` CLI command,
     * since no admin exists yet to authorize this endpoint.
     */
    public function createAdmin(Request $request)
    {
        $data = $request->validate([
            'email' => 'required|email|unique:users,email',
            'phone' => 'nullable|string',
            'password' => 'required|string|min:8|confirmed',
        ]);

        $admin = User::create([
            'name' => $data['email'], // admins are identified by email; name can be edited later
            'email' => $data['email'],
            'phone' => $data['phone'] ?? null,
            'password' => Hash::make($data['password']),
            'role' => 'admin',
            'is_active' => true,
        ]);

        return response()->json($admin, 201);
    }

    public function toggleUser(User $user)
    {
        $user->update(['is_active' => ! $user->is_active]);

        return response()->json($user);
    }

    /**
     * Permanently deletes a user. Distinct from toggleUser (suspend),
     * which is reversible. This is not.
     */
    public function deleteUser(Request $request, User $user)
    {
        abort_if($user->id === $request->user()->id, 422, 'You cannot delete your own account.');

        $user->delete();

        return response()->json(null, 204);
    }

    public function stats()
    {
        return response()->json([
            'total_users' => User::count(),
            // No subscription gate — "active" here just means not
            // suspended by an admin.
            'active_sellers' => User::where('role', 'seller')->where('is_active', true)->count(),
            'total_buyers' => User::where('role', 'buyer')->count(),
        ]);
    }

    /**
     * Application-level performance metrics. Render's free tier
     * doesn't expose OS-level CPU/RAM to the app, so this reports
     * metrics that are actually meaningful for a Laravel app:
     * table sizes, query volume on this request, and active-user
     * approximation (logged in within the last 15 minutes via
     * personal_access_tokens.last_used_at).
     */
    public function metrics()
    {
        DB::enableQueryLog();

        $tableSizes = [
            'users' => User::count(),
            'fish_stocks' => FishStock::count(),
            'orders' => Order::count(),
        ];

        $activeUsersLast15Min = DB::table('personal_access_tokens')
            ->where('last_used_at', '>=', now()->subMinutes(15))
            ->distinct('tokenable_id')
            ->count('tokenable_id');

        $queryCount = count(DB::getQueryLog());
        DB::disableQueryLog();

        return response()->json([
            'table_sizes' => $tableSizes,
            'active_users_last_15_min' => $activeUsersLast15Min,
            'queries_this_request' => $queryCount,
            'server_time' => now()->toIso8601String(),
            'php_version' => PHP_VERSION,
            'laravel_version' => app()->version(),
        ]);
    }
}
