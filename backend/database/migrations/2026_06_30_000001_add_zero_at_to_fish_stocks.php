<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Tracks the moment a stock item's quantity hit 0.0kg, so it can be
 * pruned automatically 7 days later instead of requiring a manual
 * "Remove Stock" button. Cleared (set back to NULL) the moment the
 * seller tops the quantity back up above zero.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::table('fish_stocks', function (Blueprint $table) {
            $table->timestamp('zero_at')->nullable()->after('status');
        });
    }

    public function down(): void
    {
        Schema::table('fish_stocks', function (Blueprint $table) {
            $table->dropColumn('zero_at');
        });
    }
};
