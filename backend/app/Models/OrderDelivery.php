<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class OrderDelivery extends Model
{
    use HasFactory;

    protected $fillable = [
        'order_id', 'agency_id', 'delivery_fee', 'delivery_method', 'delivery_status',
    ];

    protected function casts(): array
    {
        return [
            'delivery_fee' => 'decimal:2',
        ];
    }

    public function order()
    {
        return $this->belongsTo(Order::class);
    }

    public function agency()
    {
        return $this->belongsTo(DeliveryAgency::class, 'agency_id');
    }
}
