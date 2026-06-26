<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Schema;

/**
 * The "Select category" field was removed from the seller's add-stock
 * form, so category_id is no longer guaranteed at submit time. The
 * column was created as `constrained()` (NOT NULL + FK), so we drop and
 * re-add the FK as nullable. Raw SQL is used because doctrine/dbal
 * (required by Schema::table()->change()) isn't installed in this app.
 */
return new class extends Migration
{
    public function up(): void
    {
        Schema::table('fish_stocks', function ($table) {
            $table->dropForeign('fish_stocks_category_id_foreign');
        });

        DB::statement('ALTER TABLE fish_stocks MODIFY category_id BIGINT UNSIGNED NULL');

        Schema::table('fish_stocks', function ($table) {
            $table->foreign('category_id')
                ->references('id')->on('fish_categories')
                ->nullOnDelete();
        });
    }

    public function down(): void
    {
        Schema::table('fish_stocks', function ($table) {
            $table->dropForeign('fish_stocks_category_id_foreign');
        });

        DB::statement('ALTER TABLE fish_stocks MODIFY category_id BIGINT UNSIGNED NOT NULL');

        Schema::table('fish_stocks', function ($table) {
            $table->foreign('category_id')->references('id')->on('fish_categories');
        });
    }
};
