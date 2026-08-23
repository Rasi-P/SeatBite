import { ArrowRightOutlined, ClockCircleOutlined, FireFilled, MinusOutlined, PlusOutlined, ShoppingOutlined } from "@ant-design/icons";
import { Button, Drawer, Input, Skeleton, message } from "antd";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import BrandMark from "../../components/BrandMark";
import { apiFetch, apiList, money } from "../../services/api";
import type { Cart, Category, CustomerSession, Product } from "../../types";

export default function CustomerMenuPage() {
  const navigate = useNavigate();
  const [session, setSession] = useState<CustomerSession | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<Cart | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<number | "all">("all");
  const [selected, setSelected] = useState<Product | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [search, setSearch] = useState("");

  useEffect(() => {
    apiFetch<CustomerSession>("/sessions/current/", { customer: true }).then((value) => {
      setSession(value);
      Promise.all([
        apiList<Category>(`/categories/?venue=${value.seat.venue_code}`, { customer: true }),
        apiList<Product>(`/products/?venue=${value.seat.venue_code}`, { customer: true }),
        apiFetch<Cart>("/cart/current/", { customer: true }),
      ]).then(([categoryData, productData, cartData]) => {
        setCategories(categoryData); setProducts(productData); setCart(cartData);
      });
    }).catch(() => navigate("/"));
  }, [navigate]);

  const add = async (product: Product, amount = 1) => {
    const existing = cart?.items.find((item) => item.product === product.id)?.quantity || 0;
    try {
      const updated = await apiFetch<Cart>("/cart/items/", {
        method: "POST", customer: true,
        body: JSON.stringify({ product_id: product.id, quantity: existing + amount }),
      });
      setCart(updated); setSelected(null); setQuantity(1); message.success(`${product.name} added`);
    } catch { message.error("Could not add this item."); }
  };

  const filtered = products.filter((product) =>
    (selectedCategory === "all" || product.category === selectedCategory) &&
    product.name.toLowerCase().includes(search.toLowerCase())
  );

  if (!session) return <main className="customer-shell"><Skeleton active paragraph={{ rows: 10 }} /></main>;
  return (
    <main className="customer-shell">
      <header className="customer-header">
        <BrandMark compact />
        <div><strong>{session.seat.venue}</strong><span>{session.seat.screen} · Row {session.seat.row_label} · Seat {session.seat.seat_number}</span></div>
        <button className="cart-circle" onClick={() => navigate("/customer/checkout")}><ShoppingOutlined /><i>{cart?.item_count || 0}</i></button>
      </header>
      <section className="food-hero">
        <div><span className="eyebrow">DELIVERED IN 10–15 MIN</span><h1>Movie night<br />tastes <em>better.</em></h1><p>Stay in your seat. We’ll handle the snacks.</p></div>
        <div className="hero-popcorn"><img src="https://images.unsplash.com/photo-1578849278619-e73505e9610f?auto=format&fit=crop&w=800&q=90" alt="Caramel popcorn" /><span><FireFilled /> Most loved</span></div>
      </section>
      <section className="offers-strip"><b>10% OFF</b><span>Movie Night offer on orders above ₹399</span><small>AUTO-APPLIED</small></section>
      <section className="menu-content">
        <div className="menu-title"><div><span className="eyebrow">CURATED FOR YOUR SHOW</span><h2>What are you craving?</h2></div><Input.Search placeholder="Search snacks" value={search} onChange={(event) => setSearch(event.target.value)} /></div>
        <div className="category-tabs">
          <button className={selectedCategory === "all" ? "active" : ""} onClick={() => setSelectedCategory("all")}>All bites</button>
          {categories.map((category) => <button key={category.id} className={selectedCategory === category.id ? "active" : ""} onClick={() => setSelectedCategory(category.id)}>{category.name}</button>)}
        </div>
        <div className="product-grid">
          {filtered.map((product, index) => (
            <article className="product-card reveal" style={{ animationDelay: `${Math.min(index, 5) * 60}ms` }} key={product.id} onClick={() => { setSelected(product); setQuantity(1); }}>
              <div className="product-image"><img src={product.image} alt={product.name} loading="lazy" />{product.is_featured && <span>HOUSE PICK</span>}<button onClick={(event) => { event.stopPropagation(); add(product); }}><PlusOutlined /> Add</button></div>
              <div className="product-copy"><small>{product.category_name}</small><h3>{product.name}</h3><p>{product.short_description}</p><div><strong>{money(product.selling_price)}</strong>{Number(product.savings) > 0 && <del>{money(product.base_price)}</del>}<span><ClockCircleOutlined /> {product.preparation_time} min</span></div></div>
            </article>
          ))}
        </div>
      </section>
      {cart && cart.item_count > 0 && <div className="sticky-cart"><div><span>{cart.item_count} {cart.item_count === 1 ? "item" : "items"}</span><strong>{money(cart.total)}</strong></div><Button type="primary" onClick={() => navigate("/customer/checkout")}>View cart <ArrowRightOutlined /></Button></div>}
      <Drawer className="product-drawer" placement="bottom" height="auto" open={!!selected} onClose={() => setSelected(null)} closable={false}>
        {selected && <div className="product-detail"><img src={selected.image} alt={selected.name} /><div className="detail-copy"><span className="eyebrow">{selected.category_name}</span><h2>{selected.name}</h2><p>{selected.description}</p><div className="detail-price"><strong>{money(selected.selling_price)}</strong><del>{money(selected.base_price)}</del><span>Save {money(selected.savings)}</span></div><div className="detail-action"><div className="quantity"><button onClick={() => setQuantity(Math.max(1, quantity - 1))}><MinusOutlined /></button><b>{quantity}</b><button onClick={() => setQuantity(Math.min(20, quantity + 1))}><PlusOutlined /></button></div><Button type="primary" size="large" onClick={() => add(selected, quantity)}>Add · {money(Number(selected.selling_price) * quantity)}</Button></div></div></div>}
      </Drawer>
    </main>
  );
}

