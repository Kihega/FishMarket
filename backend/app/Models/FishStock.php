<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class FishStock extends Model
{
    use HasFactory;

    protected $fillable = [
        'seller_id', 'category_id', 'fish_name',
        'image', 'quantity_kg', 'price_per_kg', 'status',
    ];

    protected function casts(): array
    {
        return [
            'quantity_kg' => 'decimal:2',
            'price_per_kg' => 'decimal:2',
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

        if ($this->quantity_kg <= 0) {
            $this->update(['status' => 'out_of_stock']);
        }
    }
}
