<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class AdminUserManagementTest extends TestCase
{
    use RefreshDatabase;

    public function test_admin_can_register_a_new_admin(): void
    {
        $admin = User::factory()->admin()->create();

        $response = $this->actingAs($admin, 'sanctum')->postJson('/api/admin/users', [
            'email' => 'newadmin@example.com',
            'phone' => '+255700000000',
            'password' => 'securepass123',
            'password_confirmation' => 'securepass123',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('role', 'admin')
            ->assertJsonPath('email', 'newadmin@example.com');

        $this->assertDatabaseHas('users', [
            'email' => 'newadmin@example.com',
            'role' => 'admin',
        ]);
    }

    public function test_non_admin_cannot_register_a_new_admin(): void
    {
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')->postJson('/api/admin/users', [
            'email' => 'newadmin@example.com',
            'password' => 'securepass123',
            'password_confirmation' => 'securepass123',
        ]);

        $response->assertStatus(403);
    }

    public function test_admin_registration_rejects_duplicate_email(): void
    {
        $admin = User::factory()->admin()->create();
        $existing = User::factory()->create(['email' => 'taken@example.com']);

        $response = $this->actingAs($admin, 'sanctum')->postJson('/api/admin/users', [
            'email' => 'taken@example.com',
            'password' => 'securepass123',
            'password_confirmation' => 'securepass123',
        ]);

        $response->assertStatus(422);
    }

    public function test_admin_can_delete_a_user(): void
    {
        $admin = User::factory()->admin()->create();
        $buyer = User::factory()->create();

        $response = $this->actingAs($admin, 'sanctum')->deleteJson("/api/admin/users/{$buyer->id}");

        $response->assertStatus(204);
        $this->assertDatabaseMissing('users', ['id' => $buyer->id]);
    }

    public function test_admin_cannot_delete_their_own_account(): void
    {
        $admin = User::factory()->admin()->create();

        $response = $this->actingAs($admin, 'sanctum')->deleteJson("/api/admin/users/{$admin->id}");

        $response->assertStatus(422);
        $this->assertDatabaseHas('users', ['id' => $admin->id]);
    }

    public function test_admin_can_toggle_user_active_status(): void
    {
        $admin = User::factory()->admin()->create();
        $buyer = User::factory()->create(['is_active' => true]);

        $response = $this->actingAs($admin, 'sanctum')->putJson("/api/admin/users/{$buyer->id}/toggle");

        $response->assertStatus(200)->assertJsonPath('is_active', false);
    }

    public function test_admin_can_view_metrics(): void
    {
        $admin = User::factory()->admin()->create();

        $response = $this->actingAs($admin, 'sanctum')->getJson('/api/admin/metrics');

        $response->assertStatus(200)
            ->assertJsonStructure([
                'table_sizes' => ['users', 'fish_stocks', 'orders', 'subscriptions'],
                'active_users_last_15_min',
                'queries_this_request',
                'server_time',
                'php_version',
                'laravel_version',
            ]);
    }

    public function test_non_admin_cannot_view_metrics(): void
    {
        $buyer = User::factory()->create();

        $response = $this->actingAs($buyer, 'sanctum')->getJson('/api/admin/metrics');

        $response->assertStatus(403);
    }
}
