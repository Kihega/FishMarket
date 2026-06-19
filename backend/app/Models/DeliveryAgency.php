<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class DeliveryAgency extends Model
{
    protected $fillable = ['seller_id', 'agency_name', 'contact', 'area_covered', 'is_active'];

    protected function casts(): array
    {
        return [
            'is_active' => 'boolean',
        ];
    }

    public function seller()
    {
        return $this->belongsTo(User::class, 'seller_id');
    }
}
