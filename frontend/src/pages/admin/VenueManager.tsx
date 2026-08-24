import {
  DeleteOutlined,
  DownloadOutlined,
  EditOutlined,
  PlusOutlined,
  QrcodeOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { Button, Form, Input, InputNumber, Modal, Select, Table, Tag, message } from "antd";
import { useEffect, useState } from "react";
import OpsLayout from "../../components/OpsLayout";
import { useAuth } from "../../context/AuthContext";
import { apiFetch, apiList } from "../../services/api";

interface Venue {
  id: number;
  name: string;
}

interface Screen {
  id: number;
  venue: number;
  name: string;
  screen_number: number;
  venue_name: string;
  seat_count: number;
  total_rows: number;
  total_columns: number;
  status: string;
}

interface Seat {
  id: number;
  seat_code: string;
  row_label: string;
  seat_number: number;
  seat_type: string;
  status: string;
  qr_token: string;
}

interface ScreenForm {
  venue: number;
  name: string;
  screen_number: number;
  total_rows: number;
  total_columns: number;
  status: "ACTIVE" | "INACTIVE";
}

type ScreenEditForm = Pick<ScreenForm, "name" | "screen_number" | "status">;

export default function VenueManager() {
  const { user } = useAuth();
  const [screens, setScreens] = useState<Screen[]>([]);
  const [venues, setVenues] = useState<Venue[]>([]);
  const [screen, setScreen] = useState<number | null>(null);
  const [seats, setSeats] = useState<Seat[]>([]);
  const [showAddScreen, setShowAddScreen] = useState(false);
  const [editingScreen, setEditingScreen] = useState<Screen | null>(null);
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm<ScreenForm>();
  const [editForm] = Form.useForm<ScreenEditForm>();
  const [modal, modalContext] = Modal.useModal();
  const rows = Form.useWatch("total_rows", form) || 0;
  const columns = Form.useWatch("total_columns", form) || 0;

  const loadScreens = async (preferredScreen?: number) => {
    const data = await apiList<Screen>("/screens/");
    setScreens(data);
    setScreen((current) => {
      const requested = preferredScreen || current;
      return data.some((item) => item.id === requested) ? requested : data[0]?.id || null;
    });
  };

  useEffect(() => {
    Promise.all([loadScreens(), apiList<Venue>("/venues/").then(setVenues)]).catch(() => {
      message.error("Could not load venue structure.");
    });
  }, []);

  const loadSeats = () => {
    if (!screen) {
      setSeats([]);
      return Promise.resolve();
    }
    return apiList<Seat>(`/seats/?screen=${screen}`).then(setSeats);
  };

  useEffect(() => {
    loadSeats();
  }, [screen]);

  const openAddScreen = () => {
    const nextNumber = Math.max(0, ...screens.map((item) => item.screen_number)) + 1;
    form.setFieldsValue({
      venue: user?.venue || venues[0]?.id,
      name: `Screen ${nextNumber}`,
      screen_number: nextNumber,
      total_rows: 10,
      total_columns: 12,
      status: "ACTIVE",
    });
    setShowAddScreen(true);
  };

  const addScreen = async (values: ScreenForm) => {
    setSaving(true);
    try {
      const created = await apiFetch<Screen>("/screens/", {
        method: "POST",
        body: JSON.stringify(values),
      });
      await loadScreens(created.id);
      setShowAddScreen(false);
      form.resetFields();
      message.success(`${created.name} created with ${created.seat_count} seats and secure QR codes.`);
    } catch {
      message.error("Could not create the screen. Check the screen number and dimensions.");
    } finally {
      setSaving(false);
    }
  };

  const openEditScreen = (item: Screen) => {
    editForm.setFieldsValue({
      name: item.name,
      screen_number: item.screen_number,
      status: item.status as ScreenEditForm["status"],
    });
    setEditingScreen(item);
  };

  const editScreen = async (values: ScreenEditForm) => {
    if (!editingScreen) return;
    setSaving(true);
    try {
      const updated = await apiFetch<Screen>(`/screens/${editingScreen.id}/`, {
        method: "PATCH",
        body: JSON.stringify(values),
      });
      await loadScreens(updated.id);
      setEditingScreen(null);
      message.success(`${updated.name} updated.`);
    } catch {
      message.error("Could not update the screen. The screen number may already be in use.");
    } finally {
      setSaving(false);
    }
  };

  const confirmDeleteScreen = (item: Screen) => {
    modal.confirm({
      title: `Delete ${item.name}?`,
      content: (
        <span>
          This removes the screen and its {item.seat_count} seats from active venue operations. The
          records, QR references, customer sessions, and order history remain safely stored.
        </span>
      ),
      okText: "Delete screen",
      okButtonProps: { danger: true },
      cancelText: "Keep screen",
      async onOk() {
        try {
          await apiFetch(`/screens/${item.id}/`, { method: "DELETE" });
          await loadScreens();
          message.success(`${item.name} removed from active venue operations.`);
        } catch {
          message.error("Could not remove this screen.");
        }
      },
    });
  };

  const regenerate = async (seat: Seat) => {
    await apiFetch(`/seats/${seat.id}/regenerate_qr/`, { method: "POST", body: "{}" });
    message.success(`QR rotated for ${seat.seat_code}`);
    loadSeats();
  };

  const download = async (seat: Seat) => {
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
    const response = await fetch(`${apiUrl}/qr/${seat.id}/image/`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("seatbite_access")}` },
    });
    if (!response.ok) {
      message.error("Could not download this QR code.");
      return;
    }
    const blob = await response.blob();
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = `${seat.seat_code}.png`;
    link.click();
    URL.revokeObjectURL(href);
  };

  const downloadSheet = async () => {
    if (!screen) return;
    const apiUrl = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
    const response = await fetch(`${apiUrl}/qr/print-sheet/?screen=${screen}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("seatbite_access")}` },
    });
    if (!response.ok) {
      message.error("Could not generate QR sheet.");
      return;
    }
    const blob = await response.blob();
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = "seatbite-qr-sheet.pdf";
    link.click();
    URL.revokeObjectURL(href);
  };

  return (
    <OpsLayout section="admin">
      {modalContext}
      <header className="ops-header">
        <div>
          <span className="eyebrow">VENUE STRUCTURE</span>
          <h1>Every seat, addressable.</h1>
          <p>Create screens, generate seat grids, and manage secure QR codes.</p>
        </div>
        <div className="venue-actions">
          <Button disabled={!screen} icon={<DownloadOutlined />} onClick={downloadSheet}>
            Print QR sheet
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openAddScreen}>
            Add screen
          </Button>
        </div>
      </header>

      <section className="screen-strip">
        {screens.map((item) => (
          <article
            className={screen === item.id ? "active" : ""}
            key={item.id}
          >
            <button className="screen-select" onClick={() => setScreen(item.id)}>
              <span><QrcodeOutlined /></span>
              <div>
                <strong>{item.name}</strong>
                <small>{item.seat_count} seats · {item.status}</small>
              </div>
            </button>
            <div className="screen-actions">
              <Button
                type="text"
                size="small"
                aria-label={`Edit ${item.name}`}
                icon={<EditOutlined />}
                onClick={() => openEditScreen(item)}
              />
              <Button
                type="text"
                danger
                size="small"
                aria-label={`Delete ${item.name}`}
                icon={<DeleteOutlined />}
                onClick={() => confirmDeleteScreen(item)}
              />
            </div>
          </article>
        ))}
      </section>

      <section className="management-card">
        <header>
          <div>
            <span className="eyebrow">SEAT DIRECTORY</span>
            <h2>{screens.find((item) => item.id === screen)?.name || "No screens yet"}</h2>
          </div>
          <Select defaultValue="all" options={[{ value: "all", label: "All rows" }]} />
        </header>
        <Table
          rowKey="id"
          pagination={{ pageSize: 12 }}
          dataSource={seats}
          locale={{ emptyText: "Create a screen to generate its seat directory." }}
          columns={[
            { title: "Seat", render: (_, seat: Seat) => <strong>{seat.seat_code}</strong> },
            { title: "Row", dataIndex: "row_label" },
            { title: "Number", dataIndex: "seat_number" },
            { title: "Type", dataIndex: "seat_type", render: (value) => <Tag>{value}</Tag> },
            { title: "QR status", render: () => <Tag color="green">Active</Tag> },
            {
              title: "Actions",
              render: (_, seat: Seat) => (
                <div className="table-actions">
                  <Button icon={<DownloadOutlined />} onClick={() => download(seat)}>QR</Button>
                  <Button icon={<ReloadOutlined />} onClick={() => regenerate(seat)}>Rotate</Button>
                </div>
              ),
            },
          ]}
        />
      </section>

      <Modal
        title="Add cinema screen"
        open={showAddScreen}
        onCancel={() => setShowAddScreen(false)}
        footer={null}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" onFinish={addScreen}>
          {user?.role === "SUPER_ADMIN" && (
            <Form.Item name="venue" label="Venue" rules={[{ required: true }]}>
              <Select options={venues.map((venue) => ({ value: venue.id, label: venue.name }))} />
            </Form.Item>
          )}
          <div className="form-row screen-basics">
            <Form.Item name="name" label="Screen name" rules={[{ required: true }]}>
              <Input placeholder="Screen 4" />
            </Form.Item>
            <Form.Item name="screen_number" label="Screen number" rules={[{ required: true }]}>
              <InputNumber min={1} precision={0} />
            </Form.Item>
          </div>
          <div className="form-row screen-dimensions">
            <Form.Item name="total_rows" label="Rows" rules={[{ required: true }]}>
              <InputNumber min={1} max={26} precision={0} />
            </Form.Item>
            <Form.Item name="total_columns" label="Seats per row" rules={[{ required: true }]}>
              <InputNumber min={1} max={50} precision={0} />
            </Form.Item>
          </div>
          <div className="screen-form-summary">
            <QrcodeOutlined />
            <div>
              <strong>{rows * columns} seats will be generated</strong>
              <span>Each seat receives a unique secure QR token automatically.</span>
            </div>
          </div>
          <Form.Item name="status" hidden><Input /></Form.Item>
          <Button type="primary" htmlType="submit" size="large" block loading={saving}>
            Create screen and seats
          </Button>
        </Form>
      </Modal>

      <Modal
        title={`Edit ${editingScreen?.name || "screen"}`}
        open={!!editingScreen}
        onCancel={() => setEditingScreen(null)}
        footer={null}
        destroyOnHidden
      >
        <Form form={editForm} layout="vertical" onFinish={editScreen}>
          <div className="form-row screen-basics">
            <Form.Item name="name" label="Screen name" rules={[{ required: true }]}>
              <Input />
            </Form.Item>
            <Form.Item name="screen_number" label="Screen number" rules={[{ required: true }]}>
              <InputNumber min={1} precision={0} />
            </Form.Item>
          </div>
          <Form.Item name="status" label="Status" rules={[{ required: true }]}>
            <Select options={[
              { value: "ACTIVE", label: "Active" },
              { value: "INACTIVE", label: "Inactive" },
            ]} />
          </Form.Item>
          <div className="screen-layout-lock">
            <QrcodeOutlined />
            <div>
              <strong>{editingScreen?.total_rows} rows × {editingScreen?.total_columns} seats</strong>
              <span>Layout dimensions are locked to preserve issued QR codes and order history.</span>
            </div>
          </div>
          <Button type="primary" htmlType="submit" size="large" block loading={saving}>
            Save screen
          </Button>
        </Form>
      </Modal>
    </OpsLayout>
  );
}
