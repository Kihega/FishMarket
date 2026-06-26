<?php

namespace App\Http\Controllers\API\Concerns;

use Illuminate\Http\UploadedFile;

/**
 * Decides HOW to store an uploaded image based on the current database
 * connection:
 *   - Local MySQL (127.0.0.1 / localhost)  → base64-encode and store
 *     directly in the database column (no disk dependency, works
 *     immediately on a fresh laptop setup for presentations/demos).
 *   - Remote database (e.g. Aiven on Render) → store on local disk via
 *     Laravel's filesystem, since Render's disk is ephemeral per
 *     deploy but fine for the lifetime of a single running container.
 *
 * Both modes are written to the SAME database column (a string),
 * so no schema change is needed: it either holds a disk path like
 * "stocks/abc123.jpg" or a full data URI like "data:image/jpeg;base64,...".
 * The frontend already does the right thing for disk paths
 * (`/storage/${path}`) — see StoredImage below for the base64 case.
 */
trait StoresImages
{
    protected function isLocalDatabase(): bool
    {
        $host = config('database.connections.mysql.host', '');

        // When DATABASE_URL is used (Aiven/production), the parsed host
        // will be the Aiven hostname, never 127.0.0.1/localhost.
        return in_array($host, ['127.0.0.1', 'localhost'], true);
    }

    /**
     * Stores the file and returns the value to save in the DB column.
     * - Local DB: returns a base64 data URI (e.g. "data:image/png;base64,...")
     * - Remote DB: returns a disk path (e.g. "stocks/abc123.jpg"), same
     *   as before this patch — no behavior change for Aiven/Render.
     */
    protected function storeImage(UploadedFile $file, string $folder): string
    {
        if ($this->isLocalDatabase()) {
            $mime = $file->getMimeType();
            $contents = base64_encode(file_get_contents($file->getRealPath()));

            return "data:{$mime};base64,{$contents}";
        }

        return $file->store($folder, 'public');
    }
}
