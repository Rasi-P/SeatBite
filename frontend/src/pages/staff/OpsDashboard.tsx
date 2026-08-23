import { CheckOutlined, ClockCircleOutlined, EnvironmentOutlined, FireOutlined, ReloadOutlined, RocketOutlined } from "@ant-design/icons";
import { Button, Empty, Segmented, Select, Spin, Tag, message } from "antd";
import { useEffect, useState } from "react";
import OpsLayout from "../../components/OpsLayout";
import MetricCard from "../../components/MetricCard";
import { useAuth } from "../../context/AuthContext";
import { apiFetch, money } from "../../services/api";
import type { Order, OrderStatus, Overview } from "../../types";

type Board = Record<"CONFIRMED" | "PREPARING" | "READY" | "OUT_FOR_DELIVERY", Order[]>;
interface MapSeat { id: number; row_label: string; seat_number: number; seat_code: string; order_status: OrderStatus | null; order_id: number | null; order_number: string | null; }
interface SeatMap { screen: { id: number; name: string }; seats: MapSeat[]; }

const columns: { key: keyof Board; label: string; hint: string }[] = [
  { key: "CONFIRMED", label: "New", hint: "Needs acceptance" },
  { key: "PREPARING", label: "Preparing", hint: "In the kitchen" },
  { key: "READY", label: "Ready", hint: "Awaiting runner" },
  { key: "OUT_FOR_DELIVERY", label: "On the way", hint: "Moving to seat" },
];

const statusAction: Partial<Record<OrderStatus, { next: OrderStatus; label: string }>> = {
  CONFIRMED: { next: "PREPARING", label: "Accept & prepare" },
  PREPARING: { next: "READY", label: "Mark ready" },
  READY: { next: "OUT_FOR_DELIVERY", label: "Start delivery" },
  OUT_FOR_DELIVERY: { next: "DELIVERED", label: "Mark delivered" },
};

export default function OpsDashboard() {
  const { user } = useAuth();
  const [view, setView] = useState("board");
  const [board, setBoard] = useState<Board | null>(null);
  const [overview, setOverview] = useState<Overview | null>(null);
  const [seatMap, setSeatMap] = useState<SeatMap | null>(null);
  const [screenId, setScreenId] = useState<number | null>(null);

  const load = async () => {
    const [boardData, overviewData] = await Promise.all([
      apiFetch<Board>("/orders/board/"), apiFetch<Overview>("/analytics/overview/"),
    ]);
    setBoard(boardData); setOverview(overviewData);
    const first = Object.values(boardData).flat()[0];
    if (first && !screenId) setScreenId(first.screen);
  };
  useEffect(() => { load(); const timer = window.setInterval(load, 5000); return () => window.clearInterval(timer); }, []);
  useEffect(() => { if (screenId) apiFetch<SeatMap>(`/delivery/seat-map/?screen=${screenId}`).then(setSeatMap); }, [screenId, board]);

  const transition = async (order: Order) => {
    const action = statusAction[order.status];
    if (!action) return;
    try {
      if (action.next === "OUT_FOR_DELIVERY" && user?.role === "DELIVERY_STAFF") {
        await apiFetch("/delivery/", { method: "POST", body: JSON.stringify({ order: order.id }) }).catch(() => undefined);
      }
      await apiFetch(`/orders/${order.id}/transition/`, { method: "POST", body: JSON.stringify({ status: action.next }) });
      message.success(`${order.order_number} updated`); await load();
    } catch { message.error("This transition is not allowed for your role."); }
  };
  const canAct = (status: OrderStatus) => {
    if (user?.role === "KITCHEN_STAFF") return status === "CONFIRMED" || status === "PREPARING";
    if (user?.role === "DELIVERY_STAFF") return status === "READY" || status === "OUT_FOR_DELIVERY";
    return true;
  };
  const allOrders = board ? Object.values(board).flat() : [];
  const screens = Array.from(new Map(allOrders.map((order) => [order.screen, order.screen_name])).entries());

  return (
    <OpsLayout section="staff">
      <header className="ops-header"><div><span className="eyebrow">LIVE VENUE OPERATIONS</span><h1>Good evening, {user?.first_name}.</h1><p>{user?.venue_name} · Orders refresh every 5 seconds</p></div><div><Segmented value={view} onChange={(value) => setView(value as string)} options={[{ label: "Order board", value: "board" }, { label: "Seat map", value: "map" }]} /><Button icon={<ReloadOutlined />} onClick={load}>Refresh</Button></div></header>
      <section className="metric-grid ops-metrics">
        <MetricCard label="Orders today" value={overview?.orders ?? "–"} detail="Across all screens" icon={<ClockCircleOutlined />} />
        <MetricCard label="In kitchen" value={(overview?.status_counts?.CONFIRMED || 0) + (overview?.status_counts?.PREPARING || 0)} detail="Live workload" icon={<FireOutlined />} />
        <MetricCard label="Ready now" value={overview?.status_counts?.READY || 0} detail="Needs a runner" icon={<RocketOutlined />} />
        <MetricCard label="Delivered" value={overview?.status_counts?.DELIVERED || 0} detail="Completed today" icon={<CheckOutlined />} />
      </section>
      {view === "board" && <section className="kanban">
        {columns.map((column) => <div className={`kanban-column status-${column.key.toLowerCase()}`} key={column.key}><header><div><i /><strong>{column.label}</strong><span>{board?.[column.key].length || 0}</span></div><small>{column.hint}</small></header><div className="kanban-list">{!board ? <Spin /> : board[column.key].length === 0 ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Nothing here" /> : board[column.key].map((order) => <article className="order-card" key={order.id}><div className="order-top"><div><small>{order.order_number}</small><strong><EnvironmentOutlined /> {order.screen_name} · {order.seat_code}</strong></div><Tag>{Math.max(1, Math.round((Date.now() - new Date(order.created_at).getTime()) / 60000))} min</Tag></div><div className="order-items">{order.items.map((item) => <div key={item.id}><span><b>{item.quantity}×</b> {item.product_name}</span></div>)}</div><div className="order-total"><span>{order.items.reduce((sum, item) => sum + item.quantity, 0)} items</span><strong>{money(order.total)}</strong></div>{canAct(order.status) && statusAction[order.status] && <Button type="primary" block onClick={() => transition(order)}>{statusAction[order.status]?.label}</Button>}</article>)}</div></div>)}
      </section>}
      {view === "map" && <section className="seat-map-panel"><header><div><span className="eyebrow">DELIVERY NAVIGATOR</span><h2>Find the right seat at a glance</h2></div><Select placeholder="Select screen" value={screenId} onChange={setScreenId} options={screens.map(([value, label]) => ({ value, label }))} /></header>{seatMap ? <><div className="cinema-screen">SCREEN</div><div className="seat-map">{Array.from(new Set(seatMap.seats.map((seat) => seat.row_label))).map((row) => <div className="seat-row" key={row}><b>{row}</b><div>{seatMap.seats.filter((seat) => seat.row_label === row).map((seat) => <button key={seat.id} title={seat.order_number || seat.seat_code} className={seat.order_status ? `seat-${seat.order_status.toLowerCase()}` : ""}><span>{seat.seat_number}</span>{seat.order_status && <i />}</button>)}</div><b>{row}</b></div>)}</div><div className="map-legend"><span><i className="new" /> New</span><span><i className="preparing" /> Preparing</span><span><i className="ready" /> Ready</span><span><i className="moving" /> On the way</span></div></> : <Empty description="Select an active screen" />}</section>}
    </OpsLayout>
  );
}

