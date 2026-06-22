<?php

namespace Database\Factories;

use App\Models\User;
use Illuminate\Database\Eloquent\Factories\Factory;

class SubscriptionFactory extends Factory
{
    protected $model = \App\Models\Subscription::class;

    public function definition(): array
    {
        $plan = fake()->randomElement(['monthly', 'annual']);

        return [
            'seller_id' => User::factory()->seller(),
            'plan'      => $plan,
            'amount'    => $plan === 'monthly' ? 15000 : 150000,
            'status'    => 'pending',
        ];
    }
}
