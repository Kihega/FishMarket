<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\Schema;

/**
 * The delivery-agency / delivery-tracking feature has been removed
 * entirely. Buyers now give the seller a phone number at checkout
 * time (via their account) instead of picking a delivery partner or
 * typing an address, so these tables are no longer used anywhere in
 * the app.
 *
 * order_deliveries is dropped first since it holds a foreign key onto
 * delivery_agencies.
 *
 * This migration is intentionally one-way: reconstructing the exact
 * historical shape of both tables (they were altered by several later
 * migrations) in down() would just leave two empty, unused tables
 * back in place. If this ever needs reverting, restore from the
 * migrations this superseded instead.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::dropIfExists('order_deliveries');
        Schema::dropIfExists('delivery_agencies');
    }

    public function down(): void
    {
        // Intentionally not reversible — see class docblock above.
    }
};
