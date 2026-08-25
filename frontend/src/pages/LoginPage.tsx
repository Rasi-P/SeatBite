import { ArrowLeftOutlined, ArrowRightOutlined, LockOutlined, MailOutlined } from "@ant-design/icons";
import { Button, Form, Input, message } from "antd";
import { Link, useNavigate } from "react-router";
import BrandMark from "../components/BrandMark";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [form] = Form.useForm();
  const submit = async (values: { username: string; password: string }) => {
    try {
      const user = await login(values.username, values.password);
      navigate(user.role === "SUPER_ADMIN" || user.role === "VENUE_MANAGER" ? "/admin" : "/staff");
    } catch {
      message.error("Login failed. Check your username and password.");
    }
  };

  return (
    <main className="login-page">
      <section className="login-art">
        <Link to="/"><ArrowLeftOutlined /> Back to home</Link>
        <div><span className="eyebrow">SEATBITE OPERATIONS</span><h1>Run venue service<br />with clear control.</h1><p>Manage venues, screens, seats, catalog, orders, and delivery from one place.</p></div>
        <div className="login-quote"><b>Admin</b><span>sign in with your real staff account</span></div>
      </section>
      <section className="login-panel">
        <BrandMark />
        <div className="login-form-wrap">
          <span className="eyebrow">STAFF ACCESS</span>
          <h2>Welcome back</h2>
          <p>Enter your credentials to continue.</p>
          <Form form={form} layout="vertical" onFinish={submit}>
            <Form.Item name="username" label="Username" rules={[{ required: true }]}><Input size="large" prefix={<MailOutlined />} /></Form.Item>
            <Form.Item name="password" label="Password" rules={[{ required: true }]}><Input.Password size="large" prefix={<LockOutlined />} /></Form.Item>
            <Button type="primary" htmlType="submit" size="large" block>Enter dashboard <ArrowRightOutlined /></Button>
          </Form>
        </div>
      </section>
    </main>
  );
}
