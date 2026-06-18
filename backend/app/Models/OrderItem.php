<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class OrderItem extends Model
{
    public $timestamps = false;
    protected $fillable = [
        'order_id', 'stock_id', 'fish_name', 'quantity_kg', 'price_per_kg', 'subtotal',
    ];
    public function stock() { return $this->belongsTo(FishStock::class); }
}
