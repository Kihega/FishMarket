<?php

namespace App\Http\Controllers\API;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\FishStock;
use App\Models\Bill;
use Illuminate\Http\Request;
use Illuminate\Support\Str;

class OrderController extends Controller
{
    // How long a buyer has, after placing an order, to cancel it
    // themselves without seller involvement.
    private const CANCEL_WINDOW_MINUTES = 2;

    // Buyer places an order (one or more fish items from one seller).
    // Delivery itself isn't tracked in the app — the seller sees the
    // buyer's phone number on the order (their account requires one)
    // and calls them directly to sort out delivery.
    public function store(Request $request)
    {
        $data = $request->validate([
            'seller_id' => 'required|exists:users,id',
            'items' => 'required|array|min:1',
            'items.*.stock_id' => 'required|exists:fish_stocks,id',
            'items.*.quantity_kg' => 'required|numeric|min:0.1',
            'payment_method' => 'required|in:mobile,bank',
        ]);

        $total = 0;
        $orderItems = [];

        foreach ($data['items'] as $item) {
            $stock = FishStock::findOrFail($item['stock_id']);
            abort_unless((int) $stock->seller_id === (int) $data['seller_id'], 422, 'One of the items no longer belongs to this seller.');
            abort_if($stock->quantity_kg < $item['quantity_kg'], 422, 'Insufficient stock for '.$stock->fish_name);

            $subtotal = $stock->price_per_kg * $item['quantity_kg'];
            $total += $subtotal;

            $orderItems[] = [
                'stock_id' => $stock->id,
                'fish_name' => $stock->fish_name,
                'quantity_kg' => $item['quantity_kg'],
                'price_per_kg' => $stock->price_per_kg,
                'subtotal' => $subtotal,
            ];
        }

        $order = Order::create([
            'buyer_id' => $request->user()->id,
            'seller_id' => $data['seller_id'],
            'total_amount' => $total,
            'payment_method' => $data['payment_method'],
            'payment_status' => 'unpaid',
            'status' => 'pending',
        ]);

        foreach ($orderItems as $item) {
            $order->items()->create($item);
        }

        return response()->json($order->load('items'), 201);
    }

    // Buyer marks payment done → order becomes "received", seller can now confirm
    public function pay(Request $request, Order $order)
    {
        abort_unless($order->buyer_id === $request->user()->id, 403);

        $order->update([
            'payment_status' => 'paid',
            'status' => 'received',
        ]);

        return response()->json($order);
    }

    // Seller confirms order → stock decreases, bill is generated
    public function confirm(Request $request, Order $order)
    {
        abort_unless($order->seller_id === $request->user()->id, 403);
        abort_unless($order->payment_status === 'paid', 422, 'Payment not received yet');

        $order->update(['status' => 'confirmed']);

        foreach ($order->items as $item) {
            $item->stock->decreaseStock((float) $item->quantity_kg);
        }

        Bill::firstOrCreate(
            ['order_id' => $order->id],
            [
                'buyer_id' => $order->buyer_id,
                'bill_number' => 'BILL-'.strtoupper(Str::random(8)),
                'issued_at' => now(),
            ]
        );

        return response()->json($order->load('items', 'bill'));
    }

    // Buyer: cancel their own order, but only within the first
    // CANCEL_WINDOW_MINUTES minutes and only before the seller has
    // confirmed/processed it. After that, the order has to play out.
    public function cancel(Request $request, Order $order)
    {
        abort_unless($order->buyer_id === $request->user()->id, 403);

        abort_if(
            in_array($order->status, ['confirmed', 'processed', 'cancelled']),
            422,
            'This order can no longer be cancelled.'
        );

        abort_if(
            $order->created_at->diffInMinutes(now()) > self::CANCEL_WINDOW_MINUTES,
            422,
            'The '.self::CANCEL_WINDOW_MINUTES.'-minute cancellation window has expired.'
        );

        $order->update(['status' => 'cancelled']);

        return response()->json($order);
    }

    // List orders for the current user (buyer sees own orders, seller sees incoming orders).
    // Sellers get the buyer relation loaded so the buyer's phone number
    // is available on every order for delivery coordination calls.
    public function index(Request $request)
    {
        $user = $request->user();

        $orders = $user->role === 'seller'
            ? $user->ordersAsSeller()->with('buyer', 'items', 'bill')
            : $user->ordersAsBuyer()->with('seller', 'items', 'bill');

        return response()->json($orders->latest()->paginate(20));
    }
}
