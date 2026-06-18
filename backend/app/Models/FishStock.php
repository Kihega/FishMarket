<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class FishStock extends Model
{
    protected $fillable = [
        'seller_id', 'category_id', 'fish_name',
        'image', 'quantity_kg', 'price_per_kg', 'status',
    ];

    public function seller()   { return $this->belongsTo(User::class, 'seller_id'); }
    public function category() { return $this->belongsTo(FishCategory::class); }
    public function orderItems(){ return $this->hasMany(OrderItem::class, 'stock_id'); }

    public function decreaseStock(float $qty): void
    {
        $this->decrement('quantity_kg', $qty);
        if ($this->quantity_kg <= 0) {
            $this->update(['status' => 'out_of_stock']);
        }
    }
}
