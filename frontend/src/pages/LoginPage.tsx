import { ArrowLeftOutlined, ArrowRightOutlined, LockOutlined, MailOutlined } from "@ant-design/icons";
import { Button, Form, Input, Segmented, message } from "antd";
import { Link, useNavigate, useSearchParams } from "react-router";
import BrandMark from "../components/BrandMark";
import { DEMO_LOGIN_ENABLED } from "../config";
import { useAuth } from "../context/AuthContext";

const accounts = {
  admin: { username: "admin", label: "Admin" },
  manager: { username: "manager", label: "Manager" },
  kitchen: { username: "kitchen", label: "Kitchen" },
  delivery: { username: "delivery", label: "Delivery" },
} as const;

export default function LoginPage() {
  const [params] = useSearchParams();
  const initial = (params.get("role") as keyof typeof accounts) || "manager";
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form] = Form.useForm();

  const selectRole = (value: string | number) => form.setFieldValue("username", accounts[value as keyof typeof accounts].username);
  const submit = async (values: { username: string; password: string }) => {
    try {
      const user = await login(values.username, values.password);
      navigate(user.role === "SUPER_ADMIN" || user.role === "VENUE_MANAGER" ? "/admin" : "/staff");
    } catch {
      message.error("Login failed. Check your username and password.");
    }
  };

  const initialValues = DEMO_LOGIN_ENABLED
    ? { username: accounts[initial].username, password: "SeatBite@123" }
    : { username: "", password: "" };

  return (
    <main className="login-page">
      <section className="login-art">
        <Link to="/"><ArrowLeftOutlined /> Back to demo</Link>
        <div><span className="eyebrow">CINEMAX CALICUT</span><h1>The whole venue,<br />in one frame.</h1><p>Orders move from kitchen to seat with a clear operational handoff.</p></div>
        <div className="login-quote"><b>126</b><span>orders served today</span></div>
      </section>
      <section className="login-panel">
        <BrandMark />
        <div className="login-form-wrap">
          <span className="eyebrow">STAFF ACCESS</span>
          <h2>Welcome back</h2>
          <p>{DEMO_LOGIN_ENABLED ? "Choose a demo role or enter your credentials." : "Enter your credentials to continue."}</p>
          {DEMO_LOGIN_ENABLED ? (
            <Segmented block defaultValue={initial} options={Object.entries(accounts).map(([value, item]) => ({ value, label: item.label }))} onChange={selectRole} />
          ) : null}
          <Form form={form} layout="vertical" initialValues={initialValues} onFinish={submit}>
            <Form.Item name="username" label="Username" rules={[{ required: true }]}><Input size="large" prefix={<MailOutlined />} /></Form.Item>
            <Form.Item name="password" label="Password" rules={[{ required: true }]}><Input.Password size="large" prefix={<LockOutlined />} /></Form.Item>
            <Button type="primary" htmlType="submit" size="large" block>Enter dashboard <ArrowRightOutlined /></Button>
          </Form>
          {DEMO_LOGIN_ENABLED ? <small className="demo-note">Demo password: <code>SeatBite@123</code></small> : null}
        </div>
      </section>
    </main>
  );
}
