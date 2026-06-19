<?php

namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class FishCategorySeeder extends Seeder
{
    public function run(): void
    {
        $categories = [
            ['name' => 'Tilapia', 'description' => 'Freshwater fish, widely farmed'],
            ['name' => 'Dagaa (Sardine)', 'description' => 'Small freshwater sardine'],
            ['name' => 'Nile Perch', 'description' => 'Large freshwater fish'],
            ['name' => 'Catfish', 'description' => 'Bottom-feeding freshwater fish'],
            ['name' => 'Mackerel', 'description' => 'Saltwater fish'],
            ['name' => 'Tuna', 'description' => 'Saltwater fish'],
            ['name' => 'Kingfish', 'description' => 'Saltwater fish'],
            ['name' => 'Octopus', 'description' => 'Seafood / mollusk'],
            ['name' => 'Prawns', 'description' => 'Shellfish'],
            ['name' => 'Crab', 'description' => 'Shellfish'],
        ];

        foreach ($categories as $category) {
            DB::table('fish_categories')->insertOrIgnore([
                ...$category,
                'created_at' => now(),
                'updated_at' => now(),
            ]);
        }
    }
}
