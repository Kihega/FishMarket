<?php

return [

    'paths' => ['api/*'],

    'allowed_methods' => ['*'],

    'allowed_origins' => array_filter([
        env('FRONTEND_URL', 'http://localhost:5173'),
        'http://localhost:5173',
        'http://127.0.0.1:5173',
    ]),

    'allowed_origins_patterns' => [
        // Allow any Vercel preview deployment URL, e.g. fishmarket-git-xyz.vercel.app
        '#^https://.*\.vercel\.app$#',
    ],

    'allowed_headers' => ['*'],

    'exposed_headers' => [],

    'max_age' => 0,

    // false: auth is via Bearer token (Authorization header), not cookies —
    // no need for the browser to send/receive credentials cross-origin.
    'supports_credentials' => false,

];
