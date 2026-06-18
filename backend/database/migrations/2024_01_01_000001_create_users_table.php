<?php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void {
        Schema::create('users', function (Blueprint $table) {
            $table->id();
            $table->string('name');
            $table->string('email')->unique();
            $table->string('password');
            $table->enum('role', ['admin', 'seller', 'buyer'])->default('buyer');
            $table->string('phone')->nullable();
            $table->string('location')->nullable();
            $table->boolean('is_active')->default(true);
            // Seller-specific fields
            $table->string('brand_logo')->nullable();
            $table->string('office_address')->nullable();
            $table->string('location_address')->nullable();
            $table->string('bio')->nullable();
            $table->enum('subscription_status', ['active','pending','inactive'])
                  ->default('inactive');
            $table->timestamps();
        });
    }
    public function down(): void { Schema::dropIfExists('users'); }
};
