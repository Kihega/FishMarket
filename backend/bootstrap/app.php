<?php

use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware) {
        // statefulApi() removed: it enables session/CSRF-cookie based auth
        // for "stateful" frontend domains, which is for SPA-same-origin
        // session auth. Our app authenticates exclusively via Sanctum
        // Bearer tokens (Authorization header) — see frontend/src/api/client.js
        // — so statefulApi() was solving a problem we don't have, and was
        // the source of intermittent CSRF token mismatch errors during
        // local testing (no SESSION_DOMAIN matched localhost).

        $middleware->alias([
            'admin' => \App\Http\Middleware\EnsureUserIsAdmin::class,
            'seller' => \App\Http\Middleware\EnsureUserIsSeller::class,
        ]);
    })
    ->withExceptions(function (Exceptions $exceptions) {
        //
    })->create();
