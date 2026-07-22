<?php

namespace Tests\Feature;

use App\Models\FishStock;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class OrderTest extends TestCase
{
    use RefreshDatabase;

    public function test_buyer_can_place_an_order(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('total_amount', '10000.00'); // 2kg * 5000
    }

    public function test_order_rejected_when_stock_belongs_to_a_different_seller(): void
    {
        $seller = User::factory()->seller()->create();
        $otherSeller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $otherSellerStock = FishStock::factory()->create(['seller_id' => $otherSeller->id, 'quantity_kg' => 10]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $otherSellerStock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
        ]);

        $response->assertStatus(422);
    }

    public function test_order_rejected_when_quantity_exceeds_available_stock(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 1]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 5]],
            'payment_method' => 'mobile',
        ]);

        $response->assertStatus(422);
    }

    public function test_seller_sees_buyer_phone_number_on_their_orders(): void
    {
        // The seller needs to be able to call the buyer directly
        // (about delivery or anything else), so the buyer relation
        // must expose their phone number on every order.
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create(['phone' => '+255712345678']);
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10]);

        $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 1]],
            'payment_method' => 'mobile',
        ]);

        $response = $this->actingAs($seller, 'sanctum')->getJson('/api/orders');

        $response->assertStatus(200)
            ->assertJsonPath('data.0.buyer.phone', '+255712345678');
    }
}
