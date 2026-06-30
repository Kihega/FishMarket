<?php

namespace App\Console\Commands;

use App\Models\FishStock;
use Illuminate\Console\Command;

class PruneZeroStock extends Command
{
    protected $signature = 'stocks:prune-zero';

    protected $description = 'Delete fish stock items that have sat at 0.0kg for 7+ days without being restocked.';

    public function handle(): int
    {
        $deleted = FishStock::pruneExpiredZeroStock();

        $this->info("Pruned {$deleted} zeroed-out stock item(s).");

        return self::SUCCESS;
    }
}
