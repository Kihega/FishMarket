<?php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class FishCategory extends Model
{
    protected $fillable = ['name', 'description'];
    public function stocks() { return $this->hasMany(FishStock::class, 'category_id'); }
}
