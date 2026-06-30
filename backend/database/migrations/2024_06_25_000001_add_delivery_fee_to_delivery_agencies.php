<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Every delivery agency may charge a different fee depending on the
 * area it covers, so the fee is set once per agency at registration
 * time (not per order) and shown to buyers before they choose it.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::table('delivery_agencies', function (Blueprint $table) {
            $table->decimal('delivery_fee', 10, 2)->default(0)->after('area_covered');
        });
    }

    public function down(): void
    {
        Schema::table('delivery_agencies', function (Blueprint $table) {
            $table->dropColumn('delivery_fee');
        });
    }
};
