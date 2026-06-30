<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class FishStock extends Model
{
    use HasFactory;

    protected $fillable = [
        'seller_id', 'category_id', 'fish_name',
        'image', 'quantity_kg', 'price_per_kg', 'status', 'zero_at',
    ];

    protected function casts(): array
    {
        return [
            'quantity_kg' => 'decimal:2',
            'price_per_kg' => 'decimal:2',
            'zero_at' => 'datetime',
        ];
    }

    public function seller()
    {
        return $this->belongsTo(User::class, 'seller_id');
    }

    public function category()
    {
        return $this->belongsTo(FishCategory::class, 'category_id');
    }

    public function orderItems()
    {
        return $this->hasMany(OrderItem::class, 'stock_id');
    }

    public function decreaseStock(float $qty): void
    {
        $this->decrement('quantity_kg', $qty);
        $this->refresh();

        if ((float) $this->quantity_kg <= 0) {
            // Only stamp zero_at the first time it hits zero — don't
            // keep resetting the 7-day clock on every subsequent
            // decrement of an already-zeroed item.
            $this->update([
                'status' => 'out_of_stock',
                'zero_at' => $this->zero_at ?? now(),
            ]);
        }
    }

    /**
     * Delete any stock item that has sat at 0.0kg for 7+ days without
     * being topped back up. Cheap enough to call opportunistically on
     * every seller-stocks read (no cron access required), and is also
     * wired up as a proper scheduled command — see
     * App\Console\Commands\PruneZeroStock.
     */
    public static function pruneExpiredZeroStock(): int
    {
        return static::query()
            ->where('quantity_kg', '<=', 0)
            ->whereNotNull('zero_at')
            ->where('zero_at', '<=', now()->subDays(7))
            ->delete();
    }
}
