<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Order extends Model
{
    protected $fillable = [
        'buyer_id', 'seller_id', 'status',
        'payment_method', 'payment_status', 'total_amount',
    ];

    public function buyer()    { return $this->belongsTo(User::class, 'buyer_id'); }
    public function seller()   { return $this->belongsTo(User::class, 'seller_id'); }
    public function items()    { return $this->hasMany(OrderItem::class); }
    public function delivery() { return $this->hasOne(OrderDelivery::class); }
    public function bill()     { return $this->hasOne(Bill::class); }
}
