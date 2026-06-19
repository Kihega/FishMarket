<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $this->call([
            FishCategorySeeder::class,
        ]);

        // Default admin account (safe to keep — change password after first login)
        User::firstOrCreate(
            ['email' => 'admin@smartfish.test'],
            [
                'name' => 'SmartFish Admin',
                'password' => Hash::make('password123'),
                'role' => 'admin',
                'is_active' => true,
                'subscription_status' => 'active',
            ]
        );
    }
}
