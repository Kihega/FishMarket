<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Subscription extends Model
{
    protected $fillable = ['seller_id', 'plan', 'amount', 'status', 'paid_at'];
    public function seller() { return $this->belongsTo(User::class, 'seller_id'); }
}
