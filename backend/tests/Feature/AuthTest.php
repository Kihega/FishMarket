<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class AuthTest extends TestCase
{
    use RefreshDatabase;

    public function test_buyer_can_register(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Jane Buyer',
            'email' => 'jane@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
            'phone' => '+255700000000',
            'location' => 'Dar es Salaam',
        ]);

        $response->assertStatus(201)
            ->assertJsonStructure(['user', 'token'])
            ->assertJsonPath('user.role', 'buyer');

        $this->assertDatabaseHas('users', ['email' => 'jane@example.com']);
    }

    public function test_seller_registers_immediately_active(): void
    {
        // No subscription/plan step anymore — sellers are immediately
        // active and usable right after registering.
        $response = $this->postJson('/api/register', [
            'name' => 'John Seller',
            'business_name' => 'Fresh Fish Co',
            'email' => 'john@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'seller',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('user.subscription_status', 'active')
            ->assertJsonPath('user.business_name', 'Fresh Fish Co');
    }

    public function test_name_and_business_name_are_auto_capitalized(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'john seller',
            'business_name' => 'fresh fish co',
            'email' => 'autocap@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'seller',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('user.name', 'John Seller')
            ->assertJsonPath('user.business_name', 'Fresh Fish Co');
    }

    public function test_registration_rejects_phone_with_wrong_digit_count(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Bad Phone',
            'email' => 'badphone@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
            'phone' => '+25570000000', // only 8 digits after +255
        ]);

        $response->assertStatus(422);
    }

    public function test_registration_rejects_phone_without_255_prefix(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Bad Phone',
            'email' => 'badphone2@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
            'phone' => '0700000000', // local format, not +255...
        ]);

        $response->assertStatus(422);
    }

    public function test_registration_accepts_a_valid_255_phone_number(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Good Phone',
            'email' => 'goodphone@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
            'phone' => '+255712345678',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('user.phone', '+255712345678');
    }

    public function test_registration_rejects_buyer_without_phone(): void
    {
        // Buyers must give a real, callable number so the seller can
        // reach them about delivery — sellers are unaffected (see
        // test_seller_registers_immediately_active, which registers
        // successfully with no phone at all).
        $response = $this->postJson('/api/register', [
            'name' => 'No Phone',
            'email' => 'nophone@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
        ]);

        $response->assertStatus(422);
    }

    public function test_registration_rejects_weak_password_without_special_character(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Weak Pass',
            'email' => 'weak@example.com',
            'password' => 'password123', // letters + numbers, no special char
            'password_confirmation' => 'password123',
            'role' => 'buyer',
        ]);

        $response->assertStatus(422);
    }

    public function test_registration_rejects_invalid_role(): void
    {
        $response = $this->postJson('/api/register', [
            'name' => 'Bad Role',
            'email' => 'badrole@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'admin', // not allowed at registration
        ]);

        $response->assertStatus(422);
    }

    public function test_registration_fails_with_duplicate_email(): void
    {
        User::factory()->create(['email' => 'taken@example.com']);

        $response = $this->postJson('/api/register', [
            'name' => 'Duplicate',
            'email' => 'taken@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!',
            'role' => 'buyer',
        ]);

        $response->assertStatus(422);
    }

    public function test_user_can_login_with_correct_credentials(): void
    {
        User::factory()->create([
            'email' => 'login@example.com',
            'password' => bcrypt('mypassword'),
        ]);

        $response = $this->postJson('/api/login', [
            'email' => 'login@example.com',
            'password' => 'mypassword',
        ]);

        $response->assertStatus(200)
            ->assertJsonStructure(['user', 'token']);
    }

    public function test_login_fails_with_wrong_password(): void
    {
        User::factory()->create([
            'email' => 'wrongpass@example.com',
            'password' => bcrypt('correctpassword'),
        ]);

        $response = $this->postJson('/api/login', [
            'email' => 'wrongpass@example.com',
            'password' => 'wrongpassword',
        ]);

        $response->assertStatus(401)
            ->assertJson(['message' => 'Invalid credentials']);
    }

    public function test_login_fails_for_nonexistent_user(): void
    {
        $response = $this->postJson('/api/login', [
            'email' => 'doesnotexist@example.com',
            'password' => 'whatever',
        ]);

        $response->assertStatus(401);
    }

    public function test_authenticated_user_can_fetch_own_profile(): void
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user, 'sanctum')->getJson('/api/me');

        $response->assertStatus(200)
            ->assertJsonPath('id', $user->id);
    }

    public function test_guest_cannot_access_protected_route(): void
    {
        $response = $this->getJson('/api/me');

        $response->assertStatus(401);
    }

    public function test_user_can_logout(): void
    {
        $user = User::factory()->create();
        $token = $user->createToken('test')->plainTextToken;

        $response = $this->withHeader('Authorization', "Bearer {$token}")
            ->postJson('/api/logout');

        $response->assertStatus(200);
    }
}
