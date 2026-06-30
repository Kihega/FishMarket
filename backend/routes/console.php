<?php

use Illuminate\Foundation\Inspiring;
use Illuminate\Support\Facades\Artisan;
use Illuminate\Support\Facades\Schedule;

Artisan::command('inspire', function () {
    $this->comment(Inspiring::quote());
})->purpose('Display an inspiring quote');

// Sweeps stock items that have sat at 0.0kg for 7+ days. On hosts
// without cron access (e.g. Render's free tier) this won't fire on
// its own — App\Models\FishStock::pruneExpiredZeroStock() is also
// called opportunistically from FishStockController@mine() so the
// behavior is correct either way. Where cron IS available (or via a
// GitHub Actions workflow_dispatch + schedule, same pattern as the
// admin:create-first bootstrap job), this keeps it tidy daily too.
Schedule::command('stocks:prune-zero')->daily();
