import type { ReactNode } from "react";
import { AppstoreOutlined, LogoutOutlined, ShopOutlined, UnorderedListOutlined } from "@ant-design/icons";
import { NavLink, useNavigate } from "react-router";
import { useAuth } from "../context/AuthContext";
import BrandMark from "./BrandMark";

export default function OpsLayout({ children, section }: { children: ReactNode; section: "staff" | "admin" }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const signOut = () => { logout(); navigate("/"); };

  return (
    <div className="ops-shell">
      <aside className="ops-sidebar">
        <BrandMark />
        <nav>
          {section === "staff" ? (
            <NavLink to="/staff"><UnorderedListOutlined />Live operations</NavLink>
          ) : (
            <>
              <NavLink end to="/admin"><AppstoreOutlined />Overview</NavLink>
              <NavLink to="/admin/catalog"><ShopOutlined />Catalog</NavLink>
              <NavLink to="/admin/venue"><UnorderedListOutlined />Venue & QR</NavLink>
            </>
          )}
        </nav>
        <div className="sidebar-user">
          <span className="user-avatar">{user?.first_name?.[0] || "S"}</span>
          <div><strong>{user?.first_name} {user?.last_name}</strong><small>{user?.role.replaceAll("_", " ")}</small></div>
          <button onClick={signOut} aria-label="Sign out"><LogoutOutlined /></button>
        </div>
      </aside>
      <main className="ops-main">{children}</main>
    </div>
  );
}

