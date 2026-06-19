<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\FishCategory;

class FishCategoryController extends Controller
{
    public function index()
    {
        return response()->json(FishCategory::orderBy('name')->get());
    }
}
