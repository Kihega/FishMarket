<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void {
        Schema::create('fish_stocks', function (Blueprint $table) {
            $table->id();
            $table->foreignId('seller_id')->constrained('users')->cascadeOnDelete();
            $table->foreignId('category_id')->constrained('fish_categories');
            $table->string('fish_name');
            $table->string('image')->nullable();
            $table->decimal('quantity_kg', 10, 2)->default(0);
            $table->decimal('price_per_kg', 10, 2);
            $table->enum('status', ['active', 'out_of_stock'])->default('active');
            $table->timestamps();
        });
    }
    public function down(): void { Schema::dropIfExists('fish_stocks'); }
};
