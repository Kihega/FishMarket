<?php

namespace Tests\Feature;

use App\Models\User;
use App\Models\Order;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class SellerBuyersTest extends TestCase
{
    use RefreshDatabase;

    public function test_seller_can_view_their_buyers(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create(['name' => 'Jane Buyer', 'phone' => '+255700111222']);

        Order::factory()->create([
            'seller_id' => $seller->id,
            'buyer_id' => $buyer->id,
        ]);

        $response = $this->actingAs($seller, 'sanctum')->getJson('/api/seller/buyers');

        $response->assertStatus(200)
            ->assertJsonCount(1)
            ->assertJsonPath('0.buyer_name', 'Jane Buyer')
            ->assertJsonPath('0.buyer_phone', '+255700111222');
    }

    public function test_seller_only_sees_their_own_buyers(): void
    {
        $sellerA = User::factory()->seller()->create();
        $sellerB = User::factory()->seller()->create();
        $buyer = User::factory()->create();

        Order::factory()->create(['seller_id' => $sellerB->id, 'buyer_id' => $buyer->id]);

        $response = $this->actingAs($sellerA, 'sanctum')->getJson('/api/seller/buyers');

        $response->assertStatus(200)->assertJsonCount(0);
    }

    public function test_buyer_cannot_access_seller_buyers_endpoint(): void
    {
        $buyer = User::factory()->create();

        $response = $this->actingAs($buyer, 'sanctum')->getJson('/api/seller/buyers');

        $response->assertStatus(403);
    }
}
