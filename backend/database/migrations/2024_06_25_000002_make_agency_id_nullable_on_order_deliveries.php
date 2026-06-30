<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

/**
 * Choosing a delivery agency when placing an order is now optional —
 * a buyer may have their own delivery arrangement, so agency_id can no
 * longer be a required NOT NULL foreign key here.
 *
 * delivery_fee is snapshotted onto the order at the moment it's placed
 * (same pattern as OrderItem already snapshotting fish_name and
 * price_per_kg) so a later change to an agency's fee never rewrites
 * the cost of an order that already happened. It's 0 when no agency
 * was chosen.
 *
 * Raw SQL is used for the NOT NULL -> NULL column change because
 * doctrine/dbal (required by Schema::table()->change()) isn't
 * installed in this app — same approach as the fish_stocks.category_id
 * migration.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::table('order_deliveries', function ($table) {
            $table->dropForeign('order_deliveries_agency_id_foreign');
            $table->decimal('delivery_fee', 10, 2)->default(0)->after('agency_id');
        });

        DB::statement('ALTER TABLE order_deliveries MODIFY agency_id BIGINT UNSIGNED NULL');

        Schema::table('order_deliveries', function ($table) {
            $table->foreign('agency_id')
                ->references('id')->on('delivery_agencies')
                ->nullOnDelete();
        });
    }

    public function down(): void
    {
        Schema::table('order_deliveries', function ($table) {
            $table->dropForeign('order_deliveries_agency_id_foreign');
            $table->dropColumn('delivery_fee');
        });

        DB::statement('ALTER TABLE order_deliveries MODIFY agency_id BIGINT UNSIGNED NOT NULL');

        Schema::table('order_deliveries', function ($table) {
            $table->foreign('agency_id')->references('id')->on('delivery_agencies');
        });
    }
};
