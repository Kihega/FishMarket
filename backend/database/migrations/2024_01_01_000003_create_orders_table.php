<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('orders', function (Blueprint $table) {
            $table->id();
            $table->foreignId('buyer_id')->constrained('users')->cascadeOnDelete();
            $table->foreignId('listing_id')->constrained('fish_listings')->cascadeOnDelete();
            $table->decimal('quantity_kg', 8, 2);
            $table->decimal('total_price', 10, 2);
            $table->enum('status', ['pending','confirmed','delivered','cancelled'])->default('pending');
            $table->timestamps();
        });
    }

    public function down(): void { Schema::dropIfExists('orders'); }
};
