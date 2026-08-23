import { Navigate, Route, Routes } from "react-router";
import { Spin } from "antd";
import { lazy, Suspense } from "react";
import { useAuth } from "./context/AuthContext";

const LandingPage = lazy(() => import("./pages/LandingPage"));
const LoginPage = lazy(() => import("./pages/LoginPage"));
const CustomerEntryPage = lazy(() => import("./pages/customer/CustomerEntryPage"));
const CustomerMenuPage = lazy(() => import("./pages/customer/CustomerMenuPage"));
const CheckoutPage = lazy(() => import("./pages/customer/CheckoutPage"));
const TrackingPage = lazy(() => import("./pages/customer/TrackingPage"));
const OpsDashboard = lazy(() => import("./pages/staff/OpsDashboard"));
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));
const CatalogManager = lazy(() => import("./pages/admin/CatalogManager"));
const VenueManager = lazy(() => import("./pages/admin/VenueManager"));

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="full-loader"><Spin size="large" /></div>;
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Suspense fallback={<div className="full-loader"><Spin size="large" /></div>}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/customer/qr/:token" element={<CustomerEntryPage />} />
        <Route path="/customer/menu" element={<CustomerMenuPage />} />
        <Route path="/customer/checkout" element={<CheckoutPage />} />
        <Route path="/customer/order/:orderId" element={<TrackingPage />} />
        <Route path="/staff" element={<Protected><OpsDashboard /></Protected>} />
        <Route path="/admin" element={<Protected><AdminDashboard /></Protected>} />
        <Route path="/admin/catalog" element={<Protected><CatalogManager /></Protected>} />
        <Route path="/admin/venue" element={<Protected><VenueManager /></Protected>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
