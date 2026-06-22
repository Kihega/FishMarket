<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class FishCategory extends Model
{
    use HasFactory;

    protected $fillable = ['name', 'description'];

    public function stocks()
    {
        return $this->hasMany(FishStock::class, 'category_id');
    }
}
