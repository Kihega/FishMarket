<?php

namespace App\Providers;

use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        //
    }

    public function boot(): void
    {
        // Stock decrease on order confirmation is handled directly in
        // OrderController::confirm() via FishStock::decreaseStock().
        // (No observer needed — keeps the side effect explicit and testable.)
    }
}
