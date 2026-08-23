import { BarChartOutlined, RiseOutlined, ShoppingOutlined, TeamOutlined } from "@ant-design/icons";
import { Empty, Spin, Tag } from "antd";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import OpsLayout from "../../components/OpsLayout";
import MetricCard from "../../components/MetricCard";
import { useAuth } from "../../context/AuthContext";
import { apiFetch, apiList, money } from "../../services/api";
import type { Order, Overview } from "../../types";

export default function AdminDashboard() {
  const { user } = useAuth();
  const [overview, setOverview] = useState<Overview | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  useEffect(() => { Promise.all([apiFetch<Overview>("/analytics/overview/"), apiList<Order>("/orders/?ordering=-created_at")]).then(([data, orderData]) => { setOverview(data); setOrders(orderData.slice(0, 6)); }); }, []);
  return (
    <OpsLayout section="admin">
      <header className="ops-header admin-heading"><div><span className="eyebrow">VENUE INTELLIGENCE</span><h1>Today at {user?.venue_name || "SeatBite"}</h1><p>Live commercial and operational performance</p></div><Tag color="green">● LIVE</Tag></header>
      <section className="metric-grid">
        <MetricCard label="Revenue today" value={overview ? money(overview.revenue) : "–"} detail="Paid orders" icon={<RiseOutlined />} />
        <MetricCard label="Orders today" value={overview?.orders ?? "–"} detail="Across all screens" icon={<ShoppingOutlined />} />
        <MetricCard label="Average order" value={overview ? money(overview.average_order_value) : "–"} detail="Per transaction" icon={<BarChartOutlined />} />
        <MetricCard label="Items sold" value={overview?.items_sold ?? "–"} detail="Food & beverage" icon={<TeamOutlined />} />
      </section>
      <section className="analytics-grid">
        <article className="chart-card"><header><div><span className="eyebrow">ORDER VELOCITY</span><h2>Orders by hour</h2></div><small>Today</small></header>{overview ? <ResponsiveContainer width="100%" height={260}><BarChart data={overview.orders_by_hour}><CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e9e3da" /><XAxis dataKey="hour" tickFormatter={(value) => `${value}:00`} axisLine={false} tickLine={false} /><YAxis allowDecimals={false} axisLine={false} tickLine={false} /><Tooltip cursor={{ fill: "#fff3e5" }} /><Bar dataKey="orders" fill="#ef3f25" radius={[8, 8, 0, 0]} /></BarChart></ResponsiveContainer> : <Spin />}</article>
        <article className="top-products"><header><span className="eyebrow">WHAT'S SELLING</span><h2>Top products</h2></header>{overview?.top_products.length ? overview.top_products.map((product, index) => <div key={product.product_name}><b>{String(index + 1).padStart(2, "0")}</b><span><strong>{product.product_name}</strong><small>{money(product.revenue)} revenue</small></span><em>{product.quantity} sold</em></div>) : <Empty />}</article>
      </section>
      <section className="recent-orders"><header><div><span className="eyebrow">LATEST ACTIVITY</span><h2>Recent orders</h2></div></header><div className="admin-table"><div className="table-head"><span>Order</span><span>Location</span><span>Items</span><span>Status</span><span>Total</span></div>{orders.map((order) => <div key={order.id}><span><strong>{order.order_number}</strong><small>{new Date(order.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</small></span><span>{order.screen_name} · {order.seat_code}</span><span>{order.items.reduce((sum, item) => sum + item.quantity, 0)}</span><span><Tag>{order.status.replaceAll("_", " ")}</Tag></span><strong>{money(order.total)}</strong></div>)}</div></section>
    </OpsLayout>
  );
}

