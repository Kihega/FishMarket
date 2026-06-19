<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\API\AuthController;
use App\Http\Controllers\API\SellerController;
use App\Http\Controllers\API\FishStockController;
use App\Http\Controllers\API\FishCategoryController;
use App\Http\Controllers\API\DeliveryAgencyController;
use App\Http\Controllers\API\OrderController;
use App\Http\Controllers\API\AdminController;

// ── Public ──────────────────────────────────────────────────────────────
Route::post('/register', [AuthController::class, 'register']);
Route::post('/login', [AuthController::class, 'login']);

// Marketplace (public browsing — no auth required)
Route::get('/sellers', [SellerController::class, 'index']);
Route::get('/sellers/{user}', [SellerController::class, 'show']);
Route::get('/stocks', [FishStockController::class, 'index']);
Route::get('/categories', [FishCategoryController::class, 'index']);
Route::get('/agencies', [DeliveryAgencyController::class, 'index']);

// ── Protected (Sanctum token required) ───────────────────────────────────
Route::middleware('auth:sanctum')->group(function () {
    Route::post('/logout', [AuthController::class, 'logout']);
    Route::get('/me', [AuthController::class, 'me']);

    // Seller profile
    Route::put('/seller/profile', [SellerController::class, 'updateProfile']);

    // Fish stocks (seller only — enforced in controller)
    Route::post('/stocks', [FishStockController::class, 'store']);
    Route::put('/stocks/{fishStock}', [FishStockController::class, 'update']);
    Route::delete('/stocks/{fishStock}', [FishStockController::class, 'destroy']);

    // Delivery agencies (seller only)
    Route::post('/agencies', [DeliveryAgencyController::class, 'store']);
    Route::delete('/agencies/{deliveryAgency}', [DeliveryAgencyController::class, 'destroy']);

    // Orders
    Route::get('/orders', [OrderController::class, 'index']);
    Route::post('/orders', [OrderController::class, 'store']);
    Route::post('/orders/{order}/pay', [OrderController::class, 'pay']);
    Route::post('/orders/{order}/confirm', [OrderController::class, 'confirm']);

    // Admin only
    Route::middleware('admin')->prefix('admin')->group(function () {
        Route::get('/stats', [AdminController::class, 'stats']);
        Route::get('/users', [AdminController::class, 'users']);
        Route::put('/users/{user}/toggle', [AdminController::class, 'toggleUser']);
        Route::get('/subscriptions', [AdminController::class, 'subscriptions']);
        Route::put('/subscriptions/{subscription}/confirm', [AdminController::class, 'confirmSubscription']);
    });
});
