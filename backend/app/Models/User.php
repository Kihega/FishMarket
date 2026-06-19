<?php

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;

class User extends Authenticatable
{
    use HasApiTokens, Notifiable;

    protected $fillable = [
        'name', 'email', 'password', 'role', 'phone', 'location',
        'brand_logo', 'office_address', 'location_address', 'bio',
        'is_active', 'subscription_status',
    ];

    protected $hidden = ['password', 'remember_token'];

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
            'is_active' => 'boolean',
        ];
    }

    public function fishStocks()
    {
        return $this->hasMany(FishStock::class, 'seller_id');
    }

    public function deliveryAgencies()
    {
        return $this->hasMany(DeliveryAgency::class, 'seller_id');
    }

    public function ordersAsBuyer()
    {
        return $this->hasMany(Order::class, 'buyer_id');
    }

    public function ordersAsSeller()
    {
        return $this->hasMany(Order::class, 'seller_id');
    }

    public function subscriptions()
    {
        return $this->hasMany(Subscription::class, 'seller_id');
    }
}
