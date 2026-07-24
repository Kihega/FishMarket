<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\Schema;

/**
 * "Manage Sellers" (the admin panel's subscription/billing approval
 * screen) is removed — sellers are activated immediately at
 * registration with no billing step, so there was nothing left for
 * this screen to actually manage. Drops the subscriptions table and
 * the now-unused subscription_status column on users.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::dropIfExists('subscriptions');

        if (Schema::hasColumn('users', 'subscription_status')) {
            Schema::table('users', function ($table) {
                $table->dropColumn('subscription_status');
            });
        }
    }

    public function down(): void
    {
        // Intentionally not reversible — see class docblock above.
    }
};
