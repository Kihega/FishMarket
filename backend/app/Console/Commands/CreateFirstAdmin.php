<?php

namespace App\Console\Commands;

use App\Models\User;
use Illuminate\Console\Command;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Validator;

class CreateFirstAdmin extends Command
{
    protected $signature = 'admin:create-first {email} {password}';

    protected $description = 'One-time bootstrap: create the FIRST admin account. '
        . 'Refuses to run if any admin already exists — use the in-app '
        . '"Register Admin" feature for all subsequent admins.';

    public function handle(): int
    {
        if (User::where('role', 'admin')->exists()) {
            $this->error('An admin already exists. This command only bootstraps the FIRST admin.');
            $this->line('Use the in-app "Register Admin" button (requires an existing admin login) instead.');

            return self::FAILURE;
        }

        $email = $this->argument('email');
        $password = $this->argument('password');

        $validator = Validator::make(
            ['email' => $email, 'password' => $password],
            ['email' => 'required|email', 'password' => 'required|min:8']
        );

        if ($validator->fails()) {
            foreach ($validator->errors()->all() as $error) {
                $this->error($error);
            }

            return self::FAILURE;
        }

        $admin = User::create([
            'name' => $email,
            'email' => $email,
            'password' => Hash::make($password),
            'role' => 'admin',
            'is_active' => true,
            'subscription_status' => 'active',
        ]);

        $this->info("First admin created successfully: {$admin->email}");

        return self::SUCCESS;
    }
}
