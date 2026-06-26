<?php

namespace Database\Seeders;

use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

/**
 * Seeds ONLY the test admin account.
 *
 * Fish categories are intentionally excluded from fresh clones —
 * they are created through the Admin Panel UI (or via FishCategorySeeder
 * independently).  This seeder exists solely to bootstrap the very first
 * login after `php artisan migrate --seed` on a fresh database.
 *
 * Credentials printed to console after seeding.
 */
class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        $email    = env('ADMIN_EMAIL',    'admin@smartfish.test');
        $password = env('ADMIN_PASSWORD', 'Admin@1234');

        $created = false;

        $admin = User::firstOrCreate(
            ['email' => $email],
            [
                'name'                => 'SmartFish Admin',
                'password'            => Hash::make($password),
                'role'                => 'admin',
                'is_active'           => true,
                'subscription_status' => 'active',
            ]
        );

        if ($admin->wasRecentlyCreated) {
            $created = true;
        }

        $this->command->newLine();
        $this->command->info('╔══════════════════════════════════════════════╗');
        $this->command->info('║         SmartFish — Admin Account            ║');
        $this->command->info('╠══════════════════════════════════════════════╣');
        $this->command->info("║  Email   : {$email}");
        $this->command->info("║  Password: {$password}");
        $this->command->info('║                                              ║');
        $this->command->info($created
            ? '║  ✔ Admin account CREATED successfully.       ║'
            : '║  ℹ Admin account already existed — skipped.  ║'
        );
        $this->command->info('╚══════════════════════════════════════════════╝');
        $this->command->newLine();
        $this->command->warn('Change the password after your first login!');
    }
}
