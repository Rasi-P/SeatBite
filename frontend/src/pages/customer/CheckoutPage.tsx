import { ArrowLeftOutlined, CheckCircleFilled, CreditCardOutlined, DeleteOutlined, EnvironmentOutlined, MinusOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Radio, Skeleton, message } from "antd";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { apiFetch, money } from "../../services/api";
import type { Cart, CustomerSession, Order } from "../../types";

export default function CheckoutPage() {
  const navigate = useNavigate();
  const [session, setSession] = useState<CustomerSession | null>(null);
  const [cart, setCart] = useState<Cart | null>(null);
  const [method, setMethod] = useState("UPI");
  const [paying, setPaying] = useState(false);

  const load = () => Promise.all([
    apiFetch<CustomerSession>("/sessions/current/", { customer: true }),
    apiFetch<Cart>("/cart/current/", { customer: true }),
  ]).then(([sessionData, cartData]) => { setSession(sessionData); setCart(cartData); });
  useEffect(() => { load().catch(() => navigate("/")); }, [navigate]);

  const update = (productId: number, quantity: number) => {
    apiFetch<Cart>("/cart/items/", { method: "POST", customer: true, body: JSON.stringify({ product_id: productId, quantity }) }).then(setCart);
  };
  const remove = (itemId: number) => apiFetch<Cart>(`/cart/items/${itemId}/`, { method: "DELETE", customer: true }).then(setCart);
  const pay = async () => {
    setPaying(true);
    try {
      const order = await apiFetch<Order>("/cart/checkout/", { method: "POST", customer: true, body: "{}" });
      await apiFetch("/payments/simulate/", { method: "POST", customer: true, body: JSON.stringify({ order_id: order.public_id, payment_method: method }) });
      navigate(`/customer/order/${order.public_id}`);
    } catch { message.error("Payment could not be completed. Please try again."); setPaying(false); }
  };

  if (!cart || !session) return <main className="checkout-page"><Skeleton active /></main>;
  return (
    <main className="checkout-page">
      <header><button onClick={() => navigate("/customer/menu")}><ArrowLeftOutlined /></button><div><span>CHECKOUT</span><strong>Review your order</strong></div></header>
      <section className="delivery-card"><EnvironmentOutlined /><div><small>DELIVERING TO</small><strong>{session.seat.screen} · Row {session.seat.row_label} · Seat {session.seat.seat_number}</strong><span>{session.seat.venue}</span></div><CheckCircleFilled /></section>
      <section className="checkout-section"><h2>Your order <span>{cart.item_count} items</span></h2>{cart.items.map((item) => <article className="cart-line" key={item.id}><img src={item.product_detail.image} alt="" /><div><strong>{item.product_detail.name}</strong><span>{money(item.unit_price)}</span></div><div className="cart-stepper"><button onClick={() => item.quantity === 1 ? remove(item.id) : update(item.product, item.quantity - 1)}>{item.quantity === 1 ? <DeleteOutlined /> : <MinusOutlined />}</button><b>{item.quantity}</b><button onClick={() => update(item.product, item.quantity + 1)}><PlusOutlined /></button></div></article>)}</section>
      <section className="checkout-section payment-methods"><h2>Payment method</h2><Radio.Group value={method} onChange={(event) => setMethod(event.target.value)}><Radio.Button value="UPI"><b>UPI</b><span>GPay, PhonePe, BHIM</span></Radio.Button><Radio.Button value="CARD"><CreditCardOutlined /><span>Credit or debit card</span></Radio.Button><Radio.Button value="CASH"><b>₹</b><span>Cash at your seat</span></Radio.Button></Radio.Group></section>
      <section className="bill"><h2>Bill details</h2><div><span>Item total</span><b>{money(cart.subtotal)}</b></div><div className="saving"><span>Offer & product savings</span><b>-{money(cart.discount)}</b></div><div><span>Taxes</span><b>{money(cart.tax)}</b></div><div><span>Seat delivery</span><b className="free">FREE</b></div><div className="bill-total"><span>To pay</span><b>{money(cart.total)}</b></div></section>
      <div className="pay-bar"><div><small>TOTAL</small><strong>{money(cart.total)}</strong></div><Button type="primary" size="large" loading={paying} disabled={!cart.item_count} onClick={pay}>Pay & place order</Button></div>
    </main>
  );
}

