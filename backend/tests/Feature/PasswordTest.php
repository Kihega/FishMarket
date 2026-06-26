<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Tests\TestCase;

class PasswordTest extends TestCase
{
    use RefreshDatabase;

    public function test_user_can_change_password_with_correct_current_password(): void
    {
        $user = User::factory()->create(['password' => bcrypt('oldpassword123')]);

        $response = $this->actingAs($user, 'sanctum')->putJson('/api/password', [
            'current_password' => 'oldpassword123',
            'password' => 'NewPassword456!',
            'password_confirmation' => 'NewPassword456!',
        ]);

        $response->assertStatus(200);
        $this->assertTrue(Hash::check('NewPassword456!', $user->fresh()->password));
    }

    public function test_password_change_fails_with_wrong_current_password(): void
    {
        $user = User::factory()->create(['password' => bcrypt('oldpassword123')]);

        $response = $this->actingAs($user, 'sanctum')->putJson('/api/password', [
            'current_password' => 'wrongpassword',
            'password' => 'NewPassword456!',
            'password_confirmation' => 'NewPassword456!',
        ]);

        $response->assertStatus(422);
    }

    public function test_password_change_requires_confirmation_match(): void
    {
        $user = User::factory()->create(['password' => bcrypt('oldpassword123')]);

        $response = $this->actingAs($user, 'sanctum')->putJson('/api/password', [
            'current_password' => 'oldpassword123',
            'password' => 'NewPassword456!',
            'password_confirmation' => 'doesnotmatch',
        ]);

        $response->assertStatus(422);
    }

    public function test_password_change_rejects_weak_password_without_special_character(): void
    {
        $user = User::factory()->create(['password' => bcrypt('oldpassword123')]);

        $response = $this->actingAs($user, 'sanctum')->putJson('/api/password', [
            'current_password' => 'oldpassword123',
            'password' => 'password456', // letters + numbers, no special char
            'password_confirmation' => 'password456',
        ]);

        $response->assertStatus(422);
    }

    public function test_guest_cannot_change_password(): void
    {
        $response = $this->putJson('/api/password', [
            'current_password' => 'x',
            'password' => 'NewPassword456!',
            'password_confirmation' => 'NewPassword456!',
        ]);

        $response->assertStatus(401);
    }
}
