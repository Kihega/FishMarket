<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class DeliveryAgency extends Model
{
    use HasFactory;

    protected $fillable = ['seller_id', 'agency_name', 'contact', 'area_covered', 'delivery_fee', 'is_active'];

    protected function casts(): array
    {
        return [
            'is_active' => 'boolean',
            'delivery_fee' => 'decimal:2',
        ];
    }

    public function seller()
    {
        return $this->belongsTo(User::class, 'seller_id');
    }
}
