<?php

namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class FishStockTest extends TestCase
{
    use RefreshDatabase;

    public function test_seller_can_add_stock_without_an_image(): void
    {
        // The image is optional — the table must accept data even when
        // no file is attached.
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')->postJson('/api/stocks', [
            'fish_name' => 'Fresh Tilapia',
            'quantity_kg' => 25,
            'price_per_kg' => 6000,
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('fish_name', 'Fresh Tilapia')
            ->assertJsonPath('quantity_kg', '25.00')
            ->assertJsonPath('price_per_kg', '6000.00')
            ->assertJsonPath('image', null);
    }

    public function test_stock_requires_fish_name_quantity_and_price(): void
    {
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')->postJson('/api/stocks', []);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['fish_name', 'quantity_kg', 'price_per_kg']);
    }

    public function test_buyer_cannot_add_stock(): void
    {
        $buyer = User::factory()->create();

        $response = $this->actingAs($buyer, 'sanctum')->postJson('/api/stocks', [
            'fish_name' => 'Fresh Tilapia',
            'quantity_kg' => 10,
            'price_per_kg' => 5000,
        ]);

        $response->assertStatus(403);
    }

    public function test_newly_added_stock_is_immediately_visible_on_public_listing(): void
    {
        $seller = User::factory()->seller()->create();

        $this->actingAs($seller, 'sanctum')->postJson('/api/stocks', [
            'fish_name' => 'Nile Perch',
            'quantity_kg' => 12,
            'price_per_kg' => 9000,
        ])->assertStatus(201);

        $response = $this->getJson('/api/stocks');

        $response->assertStatus(200)
            ->assertJsonPath('data.0.fish_name', 'Nile Perch');
    }

    public function test_newly_added_stock_is_immediately_visible_on_the_seller_public_page(): void
    {
        // This is the exact path the buyer-facing SellerPage reads from.
        $seller = User::factory()->seller()->create();

        $this->actingAs($seller, 'sanctum')->postJson('/api/stocks', [
            'fish_name' => 'Sardine',
            'quantity_kg' => 30,
            'price_per_kg' => 3000,
        ])->assertStatus(201);

        $response = $this->getJson("/api/sellers/{$seller->id}");

        $response->assertStatus(200)
            ->assertJsonPath('stocks.0.fish_name', 'Sardine');
    }
}
