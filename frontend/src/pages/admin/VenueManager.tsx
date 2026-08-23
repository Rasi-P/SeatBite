import { DownloadOutlined, QrcodeOutlined, ReloadOutlined } from "@ant-design/icons";
import { Button, Select, Table, Tag, message } from "antd";
import { useEffect, useState } from "react";
import OpsLayout from "../../components/OpsLayout";
import { apiFetch, apiList } from "../../services/api";

interface Screen { id: number; name: string; venue_name: string; seat_count: number; status: string; }
interface Seat { id: number; seat_code: string; row_label: string; seat_number: number; seat_type: string; status: string; qr_token: string; }

export default function VenueManager() {
  const [screens, setScreens] = useState<Screen[]>([]);
  const [screen, setScreen] = useState<number | null>(null);
  const [seats, setSeats] = useState<Seat[]>([]);
  useEffect(() => { apiList<Screen>("/screens/").then((data) => { setScreens(data); if (data[0]) setScreen(data[0].id); }); }, []);
  const loadSeats = () => screen ? apiList<Seat>(`/seats/?screen=${screen}`).then(setSeats) : Promise.resolve();
  useEffect(() => { loadSeats(); }, [screen]);
  const regenerate = async (seat: Seat) => { await apiFetch(`/seats/${seat.id}/regenerate_qr/`, { method: "POST", body: "{}" }); message.success(`QR rotated for ${seat.seat_code}`); loadSeats(); };
  const download = async (seat: Seat) => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
    const response = await fetch(`${apiUrl}/qr/${seat.id}/image/`, { headers: { Authorization: `Bearer ${localStorage.getItem("seatbite_access")}` } });
    const blob = await response.blob(); const href = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = href; link.download = `${seat.seat_code}.png`; link.click(); URL.revokeObjectURL(href);
  };
  const downloadSheet = async () => {
    if (!screen) return; const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
    const response = await fetch(`${apiUrl}/qr/print-sheet/?screen=${screen}`, { headers: { Authorization: `Bearer ${localStorage.getItem("seatbite_access")}` } });
    if (!response.ok) return message.error("Could not generate QR sheet."); const blob = await response.blob(); const href = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = href; link.download = "seatbite-qr-sheet.pdf"; link.click(); URL.revokeObjectURL(href);
  };
  return <OpsLayout section="admin"><header className="ops-header"><div><span className="eyebrow">VENUE STRUCTURE</span><h1>Every seat, addressable.</h1><p>Manage screens and secure QR codes for seat delivery.</p></div><Button type="primary" icon={<DownloadOutlined />} onClick={downloadSheet}>Print QR sheet</Button></header><section className="screen-strip">{screens.map((item) => <button className={screen === item.id ? "active" : ""} onClick={() => setScreen(item.id)} key={item.id}><span><QrcodeOutlined /></span><div><strong>{item.name}</strong><small>{item.seat_count} seats · {item.status}</small></div></button>)}</section><section className="management-card"><header><div><span className="eyebrow">SEAT DIRECTORY</span><h2>{screens.find((item) => item.id === screen)?.name}</h2></div><Select defaultValue="all" options={[{ value: "all", label: "All rows" }]} /></header><Table rowKey="id" pagination={{ pageSize: 12 }} dataSource={seats} columns={[
    { title: "Seat", render: (_, seat: Seat) => <strong>{seat.seat_code}</strong> },
    { title: "Row", dataIndex: "row_label" }, { title: "Number", dataIndex: "seat_number" },
    { title: "Type", dataIndex: "seat_type", render: (value) => <Tag>{value}</Tag> },
    { title: "QR status", render: () => <Tag color="green">Active</Tag> },
    { title: "Actions", render: (_, seat: Seat) => <div className="table-actions"><Button icon={<DownloadOutlined />} onClick={() => download(seat)}>QR</Button><Button icon={<ReloadOutlined />} onClick={() => regenerate(seat)}>Rotate</Button></div> },
  ]} /></section></OpsLayout>;
}
