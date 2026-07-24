<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

/**
 * Restores delivery_agencies and order_deliveries — the delivery
 * agency / delivery-tracking feature that a previous patch removed
 * by mistake is back. Guarded with hasTable() so this is safe
 * whether or not that removal migration ever actually ran on a given
 * database.
 *
 * Schema matches the tables' final shape from before they were
 * dropped (i.e. after all of the original create + alter
 * migrations), so no separate "add delivery_fee" / "add
 * delivery_address" follow-up migrations are needed here.
 */
return new class extends Migration
{
    public function up(): void
    {
        if (! Schema::hasTable('delivery_agencies')) {
            Schema::create('delivery_agencies', function (Blueprint $table) {
                $table->id();
                $table->foreignId('seller_id')->constrained('users')->cascadeOnDelete();
                $table->string('agency_name');
                $table->string('contact')->nullable();
                $table->string('area_covered')->nullable();
                $table->decimal('delivery_fee', 10, 2)->default(0);
                $table->boolean('is_active')->default(true);
                $table->timestamps();
            });
        }

        if (! Schema::hasTable('order_deliveries')) {
            Schema::create('order_deliveries', function (Blueprint $table) {
                $table->id();
                $table->foreignId('order_id')->constrained()->cascadeOnDelete();
                $table->foreignId('agency_id')->nullable()
                    ->constrained('delivery_agencies')->nullOnDelete();
                $table->decimal('delivery_fee', 10, 2)->default(0);
                $table->text('delivery_address')->nullable();
                $table->string('delivery_method')->nullable();
                $table->enum('delivery_status', ['pending', 'dispatched', 'delivered'])->default('pending');
                $table->timestamps();
            });
        }
    }

    public function down(): void
    {
        Schema::dropIfExists('order_deliveries');
        Schema::dropIfExists('delivery_agencies');
    }
};
