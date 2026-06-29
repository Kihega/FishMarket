#!/usr/bin/env python3
"""
PATCH v13 - SmartFish: fix one wrong test assertion left over from v12
Run from project ROOT, on the `develop` branch.

WHAT THE CI RUN ACTUALLY SHOWED:
  47 of 48 tests passed. The one failure was MY mistake in v12, not a
  bug in the app:

    FAILED  DeliveryAgencyTest > guest cannot list agencies without a
            seller id
    Expected response status code [422] but received 401.

  v12 moved GET /agencies fully behind the auth:sanctum middleware
  group (the actual fix for "delivery partners not showing in the
  list" - see patch_v12.py's notes). That's correct and is NOT what
  broke - the route now rejects an unauthenticated request with 401
  before the controller's own "seller_id is required" 422 check ever
  runs, since Sanctum's middleware short-circuits first. 401 is the
  right, expected behavior for an authenticated-only route.

  The test itself, however, was written for the OLD (buggy) public
  version of that route, where the controller's manual seller_id check
  was the only gate and 422 was correct. I didn't update that one
  test's expectation when the route moved in v12 - that's on me, not a
  new defect. This patch fixes only that.

WHAT CHANGED:
  - DeliveryAgencyTest::test_guest_cannot_list_agencies_without_a_seller_id
    renamed to test_guest_is_rejected_with_401_not_a_silent_empty_list
    and now asserts 401 instead of 422, matching the route's actual
    (correct) current behavior.
  - No application code changed. No other test changed.

Run:
    cd FishMarket
    python3 patch_v13.py
"""

import os

ROOT = os.getcwd()

FILES = {
    'backend/tests/Feature/DeliveryAgencyTest.php': '<?php\n\nnamespace Tests\\Feature;\n\nuse App\\Models\\DeliveryAgency;\nuse App\\Models\\User;\nuse Illuminate\\Foundation\\Testing\\RefreshDatabase;\nuse Tests\\TestCase;\n\nclass DeliveryAgencyTest extends TestCase\n{\n    use RefreshDatabase;\n\n    public function test_seller_sees_newly_added_agency_in_their_own_list(): void\n    {\n        // Regression test: GET /agencies was registered as a PUBLIC route\n        // (outside the auth:sanctum group), so $request->user() was\n        // always null there even with a valid Bearer token — and the\n        // dashboard\'s "Delivery Partners" panel calls this route with no\n        // seller_id query param, so it always got a 422 instead of the\n        // seller\'s own agencies, even though POST /agencies (which IS\n        // behind auth:sanctum) had created the agency successfully.\n        $seller = User::factory()->seller()->create();\n\n        $createResponse = $this->actingAs($seller, \'sanctum\')->postJson(\'/api/agencies\', [\n            \'agency_name\' => \'Coastal Express\',\n            \'contact\' => \'0712345678\',\n            \'area_covered\' => \'Dar es Salaam\',\n        ]);\n        $createResponse->assertStatus(201);\n\n        $listResponse = $this->actingAs($seller, \'sanctum\')->getJson(\'/api/agencies\');\n\n        $listResponse->assertStatus(200)\n            ->assertJsonCount(1)\n            ->assertJsonPath(\'0.agency_name\', \'Coastal Express\');\n    }\n\n    public function test_seller_only_sees_their_own_agencies_not_other_sellers(): void\n    {\n        $seller = User::factory()->seller()->create();\n        $otherSeller = User::factory()->seller()->create();\n\n        DeliveryAgency::factory()->create([\'seller_id\' => $seller->id, \'agency_name\' => \'Mine\']);\n        DeliveryAgency::factory()->create([\'seller_id\' => $otherSeller->id, \'agency_name\' => \'Theirs\']);\n\n        $response = $this->actingAs($seller, \'sanctum\')->getJson(\'/api/agencies\');\n\n        $response->assertStatus(200)\n            ->assertJsonCount(1)\n            ->assertJsonPath(\'0.agency_name\', \'Mine\');\n    }\n\n    public function test_guest_is_rejected_with_401_not_a_silent_empty_list(): void\n    {\n        // GET /agencies now sits fully behind auth:sanctum (the actual\n        // v12 fix for issue 3), so an unauthenticated request is\n        // rejected by the middleware itself with 401 before the\n        // controller\'s own "seller_id is required" 422 check ever runs.\n        // (422 would have been correct for the OLD, buggy public-route\n        // version of this endpoint — asserting it here was leftover\n        // from that and is now the wrong expectation, not a new bug.)\n        $response = $this->getJson(\'/api/agencies\');\n\n        $response->assertStatus(401);\n    }\n\n    public function test_newly_added_agency_is_visible_to_buyers_on_the_seller_page(): void\n    {\n        // Covers the buyer-side half: SellerController::show() already\n        // embeds agencies scoped to that seller, separately from the\n        // GET /agencies endpoint — confirming that path stays correct.\n        $seller = User::factory()->seller()->create();\n\n        $this->actingAs($seller, \'sanctum\')->postJson(\'/api/agencies\', [\n            \'agency_name\' => \'Lakeside Movers\',\n        ])->assertStatus(201);\n\n        $publicResponse = $this->getJson("/api/sellers/{$seller->id}");\n\n        $publicResponse->assertStatus(200)\n            ->assertJsonPath(\'agencies.0.agency_name\', \'Lakeside Movers\');\n    }\n}\n',

}

def main():
    for rel_path, content in FILES.items():
        full_path = os.path.join(ROOT, rel_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  {rel_path}")

    print()
    print("Patch v13 applied (1 test assertion corrected).")
    print("""
NEXT STEPS
----------
  1. Run backend tests:
       cd backend && php artisan test --filter=DeliveryAgencyTest
     All 4 tests in this file should now pass.
  2. Commit on develop:
       git add backend/tests/Feature/DeliveryAgencyTest.php
       git commit -m "Patch v13: fix DeliveryAgencyTest - guest request to
       GET /agencies correctly returns 401 (route is auth:sanctum-gated
       since v12), not 422"
       git push origin develop
  3. Confirm GitHub Actions is fully green.
""")

if __name__ == "__main__":
    main()
