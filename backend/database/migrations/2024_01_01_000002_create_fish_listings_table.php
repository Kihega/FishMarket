<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('fish_listings', function (Blueprint $table) {
            $table->id();
            $table->foreignId('fisher_id')->constrained('users')->cascadeOnDelete();
            $table->string('species');
            $table->decimal('quantity_kg', 8, 2);
            $table->decimal('price_per_kg', 8, 2);
            $table->string('location');
            $table->text('description')->nullable();
            $table->string('image')->nullable();
            $table->enum('status', ['available', 'reserved', 'sold'])->default('available');
            $table->timestamps();
        });
    }

    public function down(): void { Schema::dropIfExists('fish_listings'); }
};
