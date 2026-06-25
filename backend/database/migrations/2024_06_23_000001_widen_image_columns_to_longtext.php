<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Support\Facades\DB;

/**
 * Widens 'image' and 'brand_logo' columns from VARCHAR(255) to LONGTEXT.
 *
 * Why: when running against a LOCAL database, images are now stored as
 * base64 data URIs directly in these columns (see StoresImages trait) —
 * a single photo easily exceeds 255 characters once encoded. VARCHAR(255)
 * would silently truncate the data. LONGTEXT supports up to 4GB, far more
 * than any reasonable image upload (capped at a few MB by validation).
 *
 * This is safe for BOTH modes: when running against Aiven/remote DB,
 * these columns still just hold short disk paths like "stocks/abc.jpg",
 * which fit easily into LONGTEXT too — no behavior change there.
 *
 * Uses raw SQL (not Schema::table()->change()) because that method
 * requires the doctrine/dbal package, which this project doesn't have
 * installed — adding it just for one column-width change isn't worth
 * the extra dependency surface.
 */
return new class extends Migration
{
    public function up(): void
    {
        DB::statement('ALTER TABLE fish_stocks MODIFY image LONGTEXT NULL');
        DB::statement('ALTER TABLE users MODIFY brand_logo LONGTEXT NULL');
    }

    public function down(): void
    {
        DB::statement('ALTER TABLE fish_stocks MODIFY image VARCHAR(255) NULL');
        DB::statement('ALTER TABLE users MODIFY brand_logo VARCHAR(255) NULL');
    }
};
