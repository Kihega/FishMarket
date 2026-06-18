<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class FishListing extends Model
{
    protected $fillable = [
        'fisher_id', 'species', 'quantity_kg',
        'price_per_kg', 'location', 'description', 'image', 'status',
    ];

    public function fisher()   { return $this->belongsTo(User::class, 'fisher_id'); }
    public function orders()   { return $this->hasMany(Order::class, 'listing_id'); }
}
