<?php

namespace Tests\Feature;

use App\Models\DeliveryAgency;
use App\Models\FishStock;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class OrderTest extends TestCase
{
    use RefreshDatabase;

    public function test_buyer_can_place_an_order_without_choosing_a_delivery_agency(): void
    {
        // Choosing a delivery agency is optional — a buyer may have
        // their own delivery arrangement.
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => null,
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('total_amount', '10000.00') // 2kg * 5000, no delivery fee
            ->assertJsonPath('delivery', null);
    }

    public function test_order_total_includes_the_chosen_agencys_delivery_fee(): void
    {
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id, 'delivery_fee' => 2000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
            'delivery_address' => '123 Uhuru Street, Dar es Salaam',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('total_amount', '12000.00') // 10000 fish + 2000 delivery
            ->assertJsonPath('delivery.delivery_fee', '2000.00')
            ->assertJsonPath('delivery.agency_id', $agency->id)
            ->assertJsonPath('delivery.delivery_address', '123 Uhuru Street, Dar es Salaam');
    }

    public function test_order_rejected_when_agency_chosen_without_a_delivery_address(): void
    {
        // delivery_address is now required once an agency is chosen,
        // so the agency/delivery driver knows exactly where to go.
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id, 'delivery_fee' => 2000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
        ]);

        $response->assertStatus(422);
    }

    public function test_changing_an_agencys_fee_later_does_not_change_a_past_orders_total(): void
    {
        // delivery_fee is snapshotted onto the order at placement time,
        // same as fish_name/price_per_kg on OrderItem.
        $seller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10, 'price_per_kg' => 5000]);
        $agency = DeliveryAgency::factory()->create(['seller_id' => $seller->id, 'delivery_fee' => 2000]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 1]],
            'payment_method' => 'mobile',
            'agency_id' => $agency->id,
            'delivery_address' => '45 Kariakoo Road, Dar es Salaam',
        ]);
        $orderId = $response->json('id');

        $agency->update(['delivery_fee' => 9000]);

        $this->assertEquals('2000.00', $this->actingAs($seller, 'sanctum')
            ->getJson('/api/orders')
            ->json('data.0.delivery.delivery_fee'));
    }

    public function test_order_rejected_when_agency_belongs_to_a_different_seller(): void
    {
        $seller = User::factory()->seller()->create();
        $otherSeller = User::factory()->seller()->create();
        $buyer = User::factory()->create();
        $stock = FishStock::factory()->create(['seller_id' => $seller->id, 'quantity_kg' => 10]);
        $otherSellerAgency = DeliveryAgency::factory()->create(['seller_id' => $otherSeller->id]);

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/orders', [
            'seller_id' => $seller->id,
            'items' => [['stock_id' => $stock->id, 'quantity_kg' => 2]],
            'payment_method' => 'mobile',
            'agency_id' => $otherSellerAgency->id,
        ]);

        $response->assertStatus(422);
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
            'agency_id' => null,
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
            'agency_id' => null,
        ]);

        $response->assertStatus(422);
    }
}
