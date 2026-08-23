import { ArrowRightOutlined, DashboardOutlined, MobileOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import { Link } from "react-router";
import BrandMark from "../components/BrandMark";

const demoToken = "uJ7cV2nQ9mL4xR8pK6sT3wZ5aB1dF0hG";

export default function LandingPage() {
  return (
    <main className="landing">
      <header className="landing-nav"><BrandMark /><span>Phase 1 cinema demo</span></header>
      <section className="landing-hero">
        <div className="landing-copy reveal">
          <span className="eyebrow">ORDER. WATCH. ENJOY.</span>
          <h1>Great food.<br /><em>Zero intermission.</em></h1>
          <p>Scan your cinema seat, order the snacks you love, and get them delivered without missing a scene.</p>
          <div className="hero-actions">
            <Link className="primary-action" to={`/customer/qr/${demoToken}`}>Try customer demo <ArrowRightOutlined /></Link>
            <Link className="text-action" to="/login">Open operations</Link>
          </div>
          <div className="trust-row"><span><SafetyCertificateOutlined /> Secure seat QR</span><span>10 min average prep</span></div>
        </div>
        <div className="hero-visual reveal delay-1">
          <div className="poster-card">
            <img src="https://images.unsplash.com/photo-1578849278619-e73505e9610f?auto=format&fit=crop&w=1000&q=90" alt="Fresh caramel popcorn" />
            <div className="poster-caption"><span>NOW SERVING</span><strong>Caramel<br />Popcorn</strong><small>delivered to F12</small></div>
          </div>
          <div className="floating-ticket"><span>SCREEN 2</span><b>F12</b><small>YOUR SEAT</small></div>
        </div>
      </section>
      <section className="demo-doors">
        <Link to={`/customer/qr/${demoToken}`}><MobileOutlined /><span><small>MOBILE EXPERIENCE</small>Customer Demo</span><ArrowRightOutlined /></Link>
        <Link to="/login?role=kitchen"><DashboardOutlined /><span><small>LIVE ORDER BOARD</small>Staff Dashboard</span><ArrowRightOutlined /></Link>
        <Link to="/login?role=admin"><DashboardOutlined /><span><small>VENUE CONTROL</small>Admin Dashboard</span><ArrowRightOutlined /></Link>
      </section>
    </main>
  );
}

