<?php

namespace Tests\Feature;

use App\Models\User;
use App\Models\Subscription;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class SubscriptionTest extends TestCase
{
    use RefreshDatabase;

    public function test_seller_can_create_a_monthly_subscription(): void
    {
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')
            ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

        $response->assertStatus(201)
            ->assertJsonPath('plan', 'monthly')
            ->assertJsonPath('status', 'pending')
            ->assertJsonPath('amount', '15000.00');

        $this->assertDatabaseHas('subscriptions', [
            'seller_id' => $seller->id,
            'plan'      => 'monthly',
            'status'    => 'pending',
        ]);
    }

    public function test_seller_can_create_an_annual_subscription(): void
    {
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')
            ->postJson('/api/seller/subscription', ['plan' => 'annual']);

        $response->assertStatus(201)
            ->assertJsonPath('plan', 'annual')
            ->assertJsonPath('amount', '150000.00');
    }

    public function test_subscription_rejects_invalid_plan(): void
    {
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')
            ->postJson('/api/seller/subscription', ['plan' => 'free']);

        $response->assertStatus(422);
    }

    public function test_subscription_rejects_missing_plan(): void
    {
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')
            ->postJson('/api/seller/subscription', []);

        $response->assertStatus(422);
    }

    public function test_buyer_cannot_create_a_subscription(): void
    {
        $buyer = User::factory()->create(['role' => 'buyer']);

        $response = $this->actingAs($buyer, 'sanctum')
            ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

        $response->assertStatus(403);
    }

    public function test_guest_cannot_create_a_subscription(): void
    {
        $response = $this->postJson('/api/seller/subscription', ['plan' => 'monthly']);

        $response->assertStatus(401);
    }

    public function test_repeated_calls_reuse_the_same_pending_subscription(): void
    {
        $seller = User::factory()->seller()->create();

        $this->actingAs($seller, 'sanctum')
            ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

        $this->actingAs($seller, 'sanctum')
            ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

        $this->assertEquals(
            1,
            Subscription::where('seller_id', $seller->id)->where('status', 'pending')->count()
        );
    }

    public function test_changing_plan_choice_updates_the_pending_subscription(): void
    {
        $seller = User::factory()->seller()->create();

        $this->actingAs($seller, 'sanctum')
            ->postJson('/api/seller/subscription', ['plan' => 'monthly']);

        $response = $this->actingAs($seller, 'sanctum')
            ->postJson('/api/seller/subscription', ['plan' => 'annual']);

        $response->assertJsonPath('plan', 'annual');

        $this->assertEquals(
            1,
            Subscription::where('seller_id', $seller->id)->count()
        );
    }

    public function test_seller_can_view_own_subscription_history(): void
    {
        $seller = User::factory()->seller()->create();
        Subscription::factory()->count(2)->create(['seller_id' => $seller->id]);

        $response = $this->actingAs($seller, 'sanctum')
            ->getJson('/api/seller/subscription');

        $response->assertStatus(200)
            ->assertJsonCount(2);
    }

    public function test_seller_cannot_view_another_sellers_subscriptions(): void
    {
        $sellerA = User::factory()->seller()->create();
        $sellerB = User::factory()->seller()->create();
        Subscription::factory()->create(['seller_id' => $sellerB->id]);

        $response = $this->actingAs($sellerA, 'sanctum')
            ->getJson('/api/seller/subscription');

        $response->assertStatus(200)->assertJsonCount(0);
    }

    public function test_admin_confirming_subscription_activates_seller(): void
    {
        $seller = User::factory()->seller()->create(['subscription_status' => 'pending']);
        $admin = User::factory()->admin()->create();
        $subscription = Subscription::factory()->create([
            'seller_id' => $seller->id,
            'status'    => 'pending',
        ]);

        $response = $this->actingAs($admin, 'sanctum')
            ->putJson("/api/admin/subscriptions/{$subscription->id}/confirm");

        $response->assertStatus(200)
            ->assertJsonPath('status', 'active');

        $this->assertEquals('active', $seller->fresh()->subscription_status);
    }
}
