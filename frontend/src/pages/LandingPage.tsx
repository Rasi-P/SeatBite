import { ArrowRightOutlined, DashboardOutlined, MobileOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { Link } from "react-router";
import BrandMark from "../components/BrandMark";

export default function LandingPage() {
  return (
    <main className="landing">
      <header className="landing-nav"><BrandMark /><span>Venue ordering platform</span></header>
      <section className="landing-hero">
        <div className="landing-copy reveal">
          <span className="eyebrow">ORDER. WATCH. ENJOY.</span>
          <h1>Great food.<br /><em>Zero intermission.</em></h1>
          <p>Guests scan their seat QR, place orders, and get food delivered without leaving the show. Staff manage the full workflow from one operations console.</p>
          <div className="hero-actions">
            <Link className="primary-action" to="/login">Open operations <ArrowRightOutlined /></Link>
            <span className="text-action">Customer ordering begins from a live seat QR</span>
          </div>
          <div className="trust-row"><span><SafetyCertificateOutlined /> Secure seat QR</span><span>10 min average prep</span></div>
        </div>
        <div className="hero-visual reveal delay-1">
          <div className="poster-card">
            <img src="https://images.unsplash.com/photo-1578849278619-e73505e9610f?auto=format&fit=crop&w=1000&q=90" alt="Fresh caramel popcorn" />
            <div className="poster-caption"><span>NOW SERVING</span><strong>Caramel<br />Popcorn</strong><small>delivered to your seat</small></div>
          </div>
          <div className="floating-ticket"><span>SCAN QR</span><b>SEAT</b><small>ORDER HERE</small></div>
        </div>
      </section>
      <section className="portal-links">
        <div><MobileOutlined /><span><small>CUSTOMER FLOW</small>Use live seat QR codes inside the venue</span></div>
        <Link to="/login"><DashboardOutlined /><span><small>LIVE ORDER BOARD</small>Staff dashboard</span><ArrowRightOutlined /></Link>
        <Link to="/login"><DashboardOutlined /><span><small>VENUE CONTROL</small>Admin dashboard</span><ArrowRightOutlined /></Link>
      </section>
    </main>
  );
}
