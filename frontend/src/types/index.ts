export type Role = "SUPER_ADMIN" | "VENUE_MANAGER" | "KITCHEN_STAFF" | "DELIVERY_STAFF";
export type OrderStatus = "PENDING" | "CONFIRMED" | "PREPARING" | "READY" | "OUT_FOR_DELIVERY" | "DELIVERED" | "CANCELLED";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  venue: number | null;
  venue_name: string | null;
}

export interface SeatInfo {
  venue_id: number;
  venue: string;
  venue_code: string;
  screen: string;
  screen_number: number;
  row_label: string;
  seat_number: number;
  seat_code: string;
}

export interface CustomerSession {
  session_token: string;
  seat: SeatInfo;
  expires_at: string;
  status: string;
}

export interface Category {
  id: number;
  venue: number;
  name: string;
  description: string;
  image: string;
  display_order: number;
  is_active: boolean;
}

export interface Product {
  id: number;
  category: number;
  category_name: string;
  venue: number;
  name: string;
  description: string;
  short_description: string;
  image: string;
  base_price: string;
  discount_price: string | null;
  selling_price: string;
  savings: string;
  tax_percentage: string;
  is_available: boolean;
  is_featured: boolean;
  preparation_time: number;
}

export interface CartItem {
  id: number;
  product: number;
  product_detail: Product;
  quantity: number;
  unit_price: string;
  discount: string;
  tax: string;
  total: string;
}

export interface Cart {
  id: number;
  status: string;
  items: CartItem[];
  item_count: number;
  subtotal: string;
  discount: string;
  tax: string;
  delivery_fee: string;
  total: string;
}

export interface OrderItem {
  id: number;
  product_name: string;
  product_image: string;
  quantity: number;
  unit_price: string;
  total: string;
}

export interface StatusEvent {
  from_status: string;
  to_status: OrderStatus;
  changed_by_name: string;
  note: string;
  created_at: string;
}

export interface Order {
  id: number;
  public_id: string;
  order_number: string;
  venue_name: string;
  venue: number;
  screen: number;
  seat: number;
  screen_name: string;
  seat_code: string;
  row_label: string;
  seat_number: number;
  status: OrderStatus;
  payment_status: string;
  subtotal: string;
  discount: string;
  tax: string;
  delivery_fee: string;
  total: string;
  items: OrderItem[];
  status_events: StatusEvent[];
  created_at: string;
}

export interface Overview {
  revenue: string | number;
  orders: number;
  average_order_value: string | number;
  items_sold: number;
  status_counts: Partial<Record<OrderStatus, number>>;
  top_products: { product_name: string; quantity: number; revenue: string }[];
  orders_by_hour: { hour: number; orders: number; revenue: string }[];
}
