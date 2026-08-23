import { CheckCircleFilled, EnvironmentOutlined } from "@ant-design/icons";
import { Button, Spin } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import BrandMark from "../../components/BrandMark";
import { apiFetch } from "../../services/api";
import type { CustomerSession } from "../../types";

export default function CustomerEntryPage() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [session, setSession] = useState<CustomerSession | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const key = `resolved_${token}`;
    const cached = sessionStorage.getItem(key);
    if (cached) {
      const parsed = JSON.parse(cached) as CustomerSession;
      localStorage.setItem("seatbite_session", parsed.session_token);
      setSession(parsed);
      return;
    }
    apiFetch<CustomerSession>("/sessions/resolve/", {
      method: "POST", customer: true,
      body: JSON.stringify({ qr_token: token, device_identifier: navigator.userAgent }),
    }).then((value) => {
      localStorage.setItem("seatbite_session", value.session_token);
      localStorage.setItem("seatbite_venue", value.seat.venue_code);
      sessionStorage.setItem(key, JSON.stringify(value));
      setSession(value);
    }).catch(() => setError(true));
  }, [token]);

  return (
    <main className="customer-entry">
      <div className="entry-glow" />
      <BrandMark />
      {!session && !error && <div className="entry-loading"><Spin size="large" /><h2>Finding your seat</h2><p>Securely checking this QR code...</p></div>}
      {error && <div className="entry-loading"><h2>That seat code is not active</h2><p>Please scan the QR on your seat again or ask a staff member for help.</p></div>}
      {session && (
        <section className="seat-confirm reveal">
          <CheckCircleFilled className="confirm-icon" />
          <span className="eyebrow">SEAT CONFIRMED</span>
          <h1>{session.seat.screen}</h1>
          <div className="seat-number"><small>ROW</small><b>{session.seat.row_label}</b><i /><small>SEAT</small><b>{session.seat.seat_number}</b></div>
          <p><EnvironmentOutlined /> {session.seat.venue}</p>
          <Button type="primary" size="large" block onClick={() => navigate("/customer/menu")}>Yes, this is my seat</Button>
          <small>Your order will be delivered here.</small>
        </section>
      )}
    </main>
  );
}

