import { EditOutlined, PlusOutlined, SearchOutlined } from "@ant-design/icons";
import { Button, Form, Input, InputNumber, Modal, Select, Switch, Table, Tag, message } from "antd";
import { useEffect, useState } from "react";
import OpsLayout from "../../components/OpsLayout";
import { apiFetch, apiList, money } from "../../services/api";
import type { Category, Product } from "../../types";

export default function CatalogManager() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [editing, setEditing] = useState<Product | null | "new">(null);
  const [search, setSearch] = useState("");
  const [form] = Form.useForm();
  const load = () => Promise.all([apiList<Product>("/products/"), apiList<Category>("/categories/")]).then(([p, c]) => { setProducts(p); setCategories(c); });
  useEffect(() => { load(); }, []);
  const open = (product: Product | "new") => { setEditing(product); form.setFieldsValue(product === "new" ? { is_available: true, tax_percentage: 5, preparation_time: 10 } : product); };
  const save = async (values: Record<string, unknown>) => {
    const path = editing === "new" ? "/products/" : `/products/${editing?.id}/`;
    try { await apiFetch(path, { method: editing === "new" ? "POST" : "PATCH", body: JSON.stringify(values) }); message.success("Product saved"); setEditing(null); load(); } catch { message.error("Could not save product."); }
  };
  const toggle = (product: Product, value: boolean) => apiFetch(`/products/${product.id}/`, { method: "PATCH", body: JSON.stringify({ is_available: value }) }).then(load);
  return <OpsLayout section="admin"><header className="ops-header"><div><span className="eyebrow">CATALOG CONTROL</span><h1>Food that sells itself.</h1><p>Manage pricing, imagery and venue availability.</p></div><Button type="primary" icon={<PlusOutlined />} onClick={() => open("new")}>Add product</Button></header><section className="management-card"><header><Input prefix={<SearchOutlined />} placeholder="Search products" value={search} onChange={(event) => setSearch(event.target.value)} /><span>{products.length} products</span></header><Table rowKey="id" pagination={{ pageSize: 10 }} dataSource={products.filter((product) => product.name.toLowerCase().includes(search.toLowerCase()))} columns={[
    { title: "Product", render: (_, product: Product) => <div className="product-cell"><img src={product.image} alt="" /><span><strong>{product.name}</strong><small>{product.category_name}</small></span></div> },
    { title: "Price", render: (_, product: Product) => <span><strong>{money(product.selling_price)}</strong> <del>{money(product.base_price)}</del></span> },
    { title: "Prep", dataIndex: "preparation_time", render: (value) => `${value} min` },
    { title: "Availability", render: (_, product: Product) => <Switch checked={product.is_available} onChange={(value) => toggle(product, value)} /> },
    { title: "", render: (_, product: Product) => <Button icon={<EditOutlined />} onClick={() => open(product)}>Edit</Button> },
  ]} /></section><Modal title={editing === "new" ? "Add product" : "Edit product"} open={!!editing} onCancel={() => setEditing(null)} footer={null} destroyOnHidden><Form form={form} layout="vertical" onFinish={save}><Form.Item name="name" label="Product name" rules={[{ required: true }]}><Input /></Form.Item><Form.Item name="category" label="Category" rules={[{ required: true }]}><Select options={categories.map((category) => ({ value: category.id, label: category.name }))} /></Form.Item><Form.Item name="short_description" label="Short description" rules={[{ required: true }]}><Input /></Form.Item><Form.Item name="description" label="Full description" rules={[{ required: true }]}><Input.TextArea /></Form.Item><Form.Item name="image" label="Image URL" rules={[{ required: true }, { type: "url" }]}><Input /></Form.Item><div className="form-row"><Form.Item name="base_price" label="Base price" rules={[{ required: true }]}><InputNumber min={0} prefix="₹" /></Form.Item><Form.Item name="discount_price" label="Selling price"><InputNumber min={0} prefix="₹" /></Form.Item><Form.Item name="tax_percentage" label="Tax %"><InputNumber min={0} /></Form.Item></div><Form.Item name="preparation_time" label="Preparation time"><InputNumber min={1} suffix="min" /></Form.Item><Form.Item name="is_available" label="Available" valuePropName="checked"><Switch /></Form.Item><Button type="primary" htmlType="submit" block>Save product</Button></Form></Modal></OpsLayout>;
}

