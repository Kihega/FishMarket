<?php

namespace App\Http\Controllers\API\Concerns;

use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;

/**
 * Decides HOW to store an uploaded image:
 *
 * - Local DB (127.0.0.1 / localhost):
 *     Base64-encode and store inline in the DB column.
 *     No disk or symlink setup required — works immediately on
 *     any fresh clone.
 *
 * - Remote DB (Aiven / production):
 *     Store on Laravel's public disk; return a full URL
 *     (APP_URL/storage/path) so the frontend never has to
 *     guess the backend origin.
 *
 * The DB column always holds either:
 *   "data:image/jpeg;base64,…"   ← local
 *   "https://host/storage/…"     ← remote
 *
 * The frontend checks `startsWith('data:')` or `startsWith('http')`
 * and uses the value as-is in both cases.
 */
trait StoresImages
{
    protected function isLocalDatabase(): bool
    {
        // When DATABASE_URL is set (production), the host env var
        // is the Aiven hostname — never 127.0.0.1/localhost.
        $host = config('database.connections.mysql.host', '');
        return in_array($host, ['127.0.0.1', 'localhost'], true);
    }

    protected function storeImage(UploadedFile $file, string $folder): string
    {
        if ($this->isLocalDatabase()) {
            $mime     = $file->getMimeType();
            $contents = base64_encode(file_get_contents($file->getRealPath()));
            return "data:{$mime};base64,{$contents}";
        }

        // Production: store on disk, return full URL
        $path = $file->store($folder, 'public');
        return Storage::disk('public')->url($path);
    }
}
