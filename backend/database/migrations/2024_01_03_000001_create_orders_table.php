<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('orders', function (Blueprint $table) {
            $table->id();
            $table->foreignId('buyer_id')->constrained('users');
            $table->foreignId('seller_id')->constrained('users');
            $table->enum('status', ['pending', 'received', 'confirmed', 'processed', 'cancelled'])
                ->default('pending');
            $table->enum('payment_method', ['mobile', 'bank'])->nullable();
            $table->enum('payment_status', ['unpaid', 'paid'])->default('unpaid');
            $table->decimal('total_amount', 12, 2)->default(0);
            $table->timestamps();

            $table->index(['seller_id', 'status']);
            $table->index(['buyer_id', 'status']);
        });

        Schema::create('order_items', function (Blueprint $table) {
            $table->id();
            $table->foreignId('order_id')->constrained()->cascadeOnDelete();
            $table->foreignId('stock_id')->constrained('fish_stocks');
            $table->string('fish_name');
            $table->decimal('quantity_kg', 10, 2);
            $table->decimal('price_per_kg', 10, 2);
            $table->decimal('subtotal', 12, 2);
        });

        Schema::create('order_deliveries', function (Blueprint $table) {
            $table->id();
            $table->foreignId('order_id')->constrained()->cascadeOnDelete();
            $table->foreignId('agency_id')->constrained('delivery_agencies');
            $table->string('delivery_method')->nullable();
            $table->enum('delivery_status', ['pending', 'dispatched', 'delivered'])->default('pending');
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('order_deliveries');
        Schema::dropIfExists('order_items');
        Schema::dropIfExists('orders');
    }
};
