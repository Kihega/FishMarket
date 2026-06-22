<?php

namespace Database\Factories;

use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

class OrderFactory extends Factory
{
    protected $model = \App\Models\Order::class;

    public function definition(): array
    {
        return [
            'buyer_id' => User::factory(),
            'seller_id' => User::factory()->seller(),
            'status' => 'pending',
            'payment_method' => 'mobile',
            'payment_status' => 'unpaid',
            'total_amount' => fake()->randomFloat(2, 1000, 50000),
        ];
    }
}
