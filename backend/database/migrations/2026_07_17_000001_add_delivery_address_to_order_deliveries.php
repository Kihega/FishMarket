<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\Schema;

/**
 * Buyers now enter the exact physical location they want their order
 * delivered to whenever they pick a delivery agency at checkout.
 * Stored on order_deliveries (same place delivery_fee is snapshotted)
 * so the seller/agency can see it in "Manage Buyers".
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::table('order_deliveries', function ($table) {
            $table->text('delivery_address')->nullable()->after('delivery_fee');
        });
    }

    public function down(): void
    {
        Schema::table('order_deliveries', function ($table) {
            $table->dropColumn('delivery_address');
        });
    }
};
