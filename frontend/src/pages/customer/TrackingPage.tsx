import { CheckOutlined, ClockCircleOutlined, HomeOutlined } from "@ant-design/icons";
import { Button, Spin } from "antd";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router";
import { apiFetch, money } from "../../services/api";
import type { Order, OrderStatus } from "../../types";

const steps: { status: OrderStatus; title: string; text: string }[] = [
  { status: "CONFIRMED", title: "Order confirmed", text: "The kitchen has your order" },
  { status: "PREPARING", title: "Being prepared", text: "Your snacks are getting ready" },
  { status: "READY", title: "Ready for pickup", text: "Packed and moving soon" },
  { status: "OUT_FOR_DELIVERY", title: "On the way", text: "Heading to your screen" },
  { status: "DELIVERED", title: "Delivered", text: "Enjoy your movie" },
];

export default function TrackingPage() {
  const { orderId } = useParams();
  const [order, setOrder] = useState<Order | null>(null);
  useEffect(() => {
    const load = () => apiFetch<Order>(`/orders/${orderId}/track/`, { customer: true }).then(setOrder);
    load(); const timer = window.setInterval(load, 4000); return () => window.clearInterval(timer);
  }, [orderId]);
  if (!order) return <div className="tracking-loading"><Spin size="large" /><p>Confirming your order...</p></div>;
  const current = steps.findIndex((step) => step.status === order.status);
  const delivered = order.status === "DELIVERED";
  return (
    <main className={`tracking-page ${delivered ? "is-delivered" : ""}`}>
      <header><Link to="/"><HomeOutlined /></Link><span>LIVE ORDER</span><i>Updating</i></header>
      <section className="tracking-hero"><div className="pulse-ring"><span>{delivered ? <CheckOutlined /> : <ClockCircleOutlined />}</span></div><span className="eyebrow">{delivered ? "DELIVERED TO YOUR SEAT" : "EXPECTED IN 10–15 MIN"}</span><h1>{delivered ? "Delivered. Enjoy the movie!" : "Your movie snacks are in motion."}</h1><p>{order.order_number} · {money(order.total)}</p></section>
      <section className="tracking-destination"><small>DELIVERING TO</small><strong>{order.screen_name} · Seat {order.seat_code}</strong><span>{order.venue_name}</span></section>
      <section className="timeline">{steps.map((step, index) => { const complete = index <= current; const active = index === current; return <div key={step.status} className={`${complete ? "complete" : ""} ${active ? "active" : ""}`}><span>{complete ? <CheckOutlined /> : index + 1}</span><div><strong>{step.title}</strong><small>{step.text}</small></div>{index < steps.length - 1 && <i />}</div>; })}</section>
      <section className="tracking-items"><h2>Your order</h2>{order.items.map((item) => <div key={item.id}><img src={item.product_image} alt="" /><span><strong>{item.product_name}</strong><small>Qty {item.quantity}</small></span><b>{money(item.total)}</b></div>)}</section>
      {delivered && <Button block size="large" onClick={() => window.location.href = "/customer/menu"}>Order something else</Button>}
    </main>
  );
}
