<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\User;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;

class AuthController extends Controller
{
    public function register(Request $request)
    {
        $data = $request->validate([
            'name' => 'required|string|max:255',
            'business_name' => 'nullable|string|max:255',
            'email' => 'required|email|unique:users',
            'password' => [
                'required', 'min:8', 'confirmed',
                'regex:/^(?=.*[a-zA-Z])(?=.*\d)(?=.*[^a-zA-Z\d]).+$/',
            ],
            'role' => 'required|in:seller,buyer',
            'phone' => 'nullable|string',
            'location' => 'nullable|string',
            'office_address' => 'nullable|string',
        ], [
            'password.regex' => 'Password must contain letters, numbers, and at least one special character.',
        ]);

        // Auto-capitalize each word (e.g. "john doe" -> "John Doe") rather
        // than rejecting lowercase input — friendlier than a validation error.
        $data['name'] = ucwords(strtolower($data['name']));
        if (! empty($data['business_name'])) {
            $data['business_name'] = ucwords(strtolower($data['business_name']));
        }

        $user = User::create([
            'name' => $data['name'],
            'business_name' => $data['business_name'] ?? null,
            'email' => $data['email'],
            'password' => Hash::make($data['password']),
            'role' => $data['role'],
            'phone' => $data['phone'] ?? null,
            'location' => $data['location'] ?? null,
            'office_address' => $data['office_address'] ?? null,
            // No subscription gate — sellers are immediately active.
            // This is a research/testing build, not a live payment system.
            'subscription_status' => 'active',
        ]);

        $token = $user->createToken('auth_token')->plainTextToken;

        return response()->json([
            'user' => $user,
            'token' => $token,
        ], 201);
    }

    public function login(Request $request)
    {
        $data = $request->validate([
            'email' => 'required|email',
            'password' => 'required',
        ]);

        $user = User::where('email', $data['email'])->first();

        if (! $user || ! Hash::check($data['password'], $user->password)) {
            return response()->json(['message' => 'Invalid credentials'], 401);
        }

        $token = $user->createToken('auth_token')->plainTextToken;

        return response()->json(['user' => $user, 'token' => $token]);
    }

    public function logout(Request $request)
    {
        $request->user()->currentAccessToken()->delete();

        return response()->json(['message' => 'Logged out']);
    }

    public function me(Request $request)
    {
        return response()->json($request->user());
    }
}
