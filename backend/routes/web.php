<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    return response()->json([
        'app' => 'SmartFish API',
        'status' => 'running',
        'docs' => '/api',
    ]);
});
