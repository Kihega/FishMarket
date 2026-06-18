<?php
namespace Database\Seeders;

use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class FishCategorySeeder extends Seeder
{
    public function run(): void
    {
        $categories = [
            'Tilapia', 'Dagaa (Sardine)', 'Nile Perch', 'Catfish',
            'Mackerel', 'Tuna', 'Kingfish', 'Octopus', 'Prawns', 'Crab',
        ];

        foreach ($categories as $name) {
            DB::table('fish_categories')->insertOrIgnore(['name' => $name, 'created_at' => now(), 'updated_at' => now()]);
        }
    }
}
