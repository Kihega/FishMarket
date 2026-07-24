<?php

namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;
use Illuminate\Support\Facades\Hash;

class UserFactory extends Factory
{
    protected $model = \App\Models\User::class;

    public function definition(): array
    {
        return [
            'name' => fake()->name(),
            'email' => fake()->unique()->safeEmail(),
            'email_verified_at' => now(),
            'password' => Hash::make('password'),
            'role' => 'buyer',
            'phone' => fake()->phoneNumber(),
            'location' => fake()->city(),
            'is_active' => true,
            'remember_token' => \Illuminate\Support\Str::random(10),
        ];
    }

    public function seller(): static
    {
        return $this->state(fn () => [
            'role' => 'seller',
            'office_address' => fake()->address(),
            'location_address' => fake()->city(),
            'bio' => fake()->sentence(),
        ]);
    }

    public function admin(): static
    {
        return $this->state(fn () => [
            'role' => 'admin',
        ]);
    }

    public function unverified(): static
    {
        return $this->state(fn () => ['email_verified_at' => null]);
    }
}
