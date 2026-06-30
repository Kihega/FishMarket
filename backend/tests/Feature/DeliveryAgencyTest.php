<?php

namespace Tests\Feature;

use App\Models\DeliveryAgency;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class DeliveryAgencyTest extends TestCase
{
    use RefreshDatabase;

    public function test_seller_sees_newly_added_agency_in_their_own_list(): void
    {
        // Regression test: GET /agencies was registered as a PUBLIC route
        // (outside the auth:sanctum group), so $request->user() was
        // always null there even with a valid Bearer token — and the
        // dashboard's "Delivery Partners" panel calls this route with no
        // seller_id query param, so it always got a 422 instead of the
        // seller's own agencies, even though POST /agencies (which IS
        // behind auth:sanctum) had created the agency successfully.
        $seller = User::factory()->seller()->create();

        $createResponse = $this->actingAs($seller, 'sanctum')->postJson('/api/agencies', [
            'agency_name' => 'Coastal Express',
            'contact' => '0712345678',
            'area_covered' => 'Dar es Salaam',
        ]);
        $createResponse->assertStatus(201);

        $listResponse = $this->actingAs($seller, 'sanctum')->getJson('/api/agencies');

        $listResponse->assertStatus(200)
            ->assertJsonCount(1)
            ->assertJsonPath('0.agency_name', 'Coastal Express');
    }

    public function test_seller_only_sees_their_own_agencies_not_other_sellers(): void
    {
        $seller = User::factory()->seller()->create();
        $otherSeller = User::factory()->seller()->create();

        DeliveryAgency::factory()->create(['seller_id' => $seller->id, 'agency_name' => 'Mine']);
        DeliveryAgency::factory()->create(['seller_id' => $otherSeller->id, 'agency_name' => 'Theirs']);

        $response = $this->actingAs($seller, 'sanctum')->getJson('/api/agencies');

        $response->assertStatus(200)
            ->assertJsonCount(1)
            ->assertJsonPath('0.agency_name', 'Mine');
    }

    public function test_guest_is_rejected_with_401_not_a_silent_empty_list(): void
    {
        // GET /agencies now sits fully behind auth:sanctum (the actual
        // v12 fix for issue 3), so an unauthenticated request is
        // rejected by the middleware itself with 401 before the
        // controller's own "seller_id is required" 422 check ever runs.
        // (422 would have been correct for the OLD, buggy public-route
        // version of this endpoint — asserting it here was leftover
        // from that and is now the wrong expectation, not a new bug.)
        $response = $this->getJson('/api/agencies');

        $response->assertStatus(401);
    }

    public function test_seller_can_set_a_delivery_fee_when_registering_an_agency(): void
    {
        // Every agency may charge a different fee depending on the area
        // it serves, so the fee is captured once here, at registration.
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')->postJson('/api/agencies', [
            'agency_name' => 'Coastal Express',
            'area_covered' => 'Dar es Salaam',
            'delivery_fee' => 3500,
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('delivery_fee', '3500.00');
    }

    public function test_agency_delivery_fee_defaults_to_zero_when_not_given(): void
    {
        $seller = User::factory()->seller()->create();

        $response = $this->actingAs($seller, 'sanctum')->postJson('/api/agencies', [
            'agency_name' => 'No Fee Listed',
        ]);

        $response->assertStatus(201)
            ->assertJsonPath('delivery_fee', '0.00');
    }

    public function test_newly_added_agency_is_visible_to_buyers_on_the_seller_page(): void
    {
        // Covers the buyer-side half: SellerController::show() already
        // embeds agencies scoped to that seller, separately from the
        // GET /agencies endpoint — confirming that path stays correct.
        $seller = User::factory()->seller()->create();

        $this->actingAs($seller, 'sanctum')->postJson('/api/agencies', [
            'agency_name' => 'Lakeside Movers',
        ])->assertStatus(201);

        $publicResponse = $this->getJson("/api/sellers/{$seller->id}");

        $publicResponse->assertStatus(200)
            ->assertJsonPath('agencies.0.agency_name', 'Lakeside Movers');
    }
}
