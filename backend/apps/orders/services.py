from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import AuditLog, User
from apps.catalog.models import Offer
from .models import Cart, CartItem, Order, OrderItem, OrderStatusEvent

MONEY = Decimal("0.01")
TRANSITIONS = {
    Order.Status.PENDING: {Order.Status.CONFIRMED, Order.Status.CANCELLED},
    Order.Status.CONFIRMED: {Order.Status.PREPARING},
    Order.Status.PREPARING: {Order.Status.READY},
    Order.Status.READY: {Order.Status.OUT_FOR_DELIVERY},
    Order.Status.OUT_FOR_DELIVERY: {Order.Status.DELIVERED},
}
ROLE_TARGETS = {
    User.Role.KITCHEN_STAFF: {Order.Status.PREPARING, Order.Status.READY},
    User.Role.DELIVERY_STAFF: {Order.Status.OUT_FOR_DELIVERY, Order.Status.DELIVERED},
    User.Role.VENUE_MANAGER: set(Order.Status.values),
    User.Role.SUPER_ADMIN: set(Order.Status.values),
}
TIMESTAMP_FIELDS = {
    Order.Status.CONFIRMED: "confirmed_at",
    Order.Status.PREPARING: "preparing_at",
    Order.Status.READY: "ready_at",
    Order.Status.OUT_FOR_DELIVERY: "out_for_delivery_at",
    Order.Status.DELIVERED: "delivered_at",
    Order.Status.CANCELLED: "cancelled_at",
}


def money(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def recalculate_cart(cart):
    # Mutations can make DRF's prefetched relation stale within the same request.
    getattr(cart, "_prefetched_objects_cache", {}).pop("items", None)
    items = list(CartItem.objects.filter(cart=cart))
    selling_subtotal = sum((item.unit_price * item.quantity for item in items), Decimal("0"))
    product_discount = sum((item.discount for item in items), Decimal("0"))
    subtotal = selling_subtotal + product_discount
    tax = sum((item.tax for item in items), Decimal("0"))
    now = timezone.now()
    offer = Offer.objects.filter(
        venue=cart.session.seat.screen.venue,
        is_active=True,
        start_at__lte=now,
        end_at__gte=now,
        minimum_order_amount__lte=selling_subtotal,
    ).exclude(offer_type=Offer.OfferType.COMBO).order_by("-discount_value").first()
    offer_discount = Decimal("0")
    if offer:
        if offer.offer_type == Offer.OfferType.PERCENTAGE:
            offer_discount = money(selling_subtotal * offer.discount_value / 100)
        else:
            offer_discount = min(offer.discount_value, selling_subtotal)
    cart.subtotal = money(subtotal)
    cart.discount = money(product_discount + offer_discount)
    cart.tax = money(tax)
    cart.delivery_fee = Decimal("0")
    cart.total = max(money(cart.subtotal - cart.discount + cart.tax), Decimal("0"))
    cart.save(update_fields=["subtotal", "discount", "tax", "delivery_fee", "total", "updated_at"])
    getattr(cart, "_prefetched_objects_cache", {}).pop("items", None)
    return cart


def set_cart_item(cart, product, quantity):
    if quantity < 1 or quantity > 20:
        raise ValueError("Quantity must be between 1 and 20.")
    if not product.is_available or product.category.venue_id != cart.session.seat.screen.venue_id:
        raise ValueError("Product is unavailable for this venue.")
    unit_price = product.selling_price
    line_subtotal = unit_price * quantity
    base_subtotal = product.base_price * quantity
    discount = money(base_subtotal - line_subtotal)
    tax = money(line_subtotal * product.tax_percentage / 100)
    CartItem.objects.update_or_create(
        cart=cart,
        product=product,
        defaults={
            "quantity": quantity,
            "unit_price": unit_price,
            "discount": discount,
            "tax": tax,
            "total": money(line_subtotal + tax),
        },
    )
    return recalculate_cart(cart)


def next_order_number():
    prefix = timezone.localdate().strftime("SB-%Y%m%d")
    last = Order.objects.filter(order_number__startswith=prefix).order_by("-order_number").first()
    sequence = int(last.order_number.rsplit("-", 1)[-1]) + 1 if last else 1001
    return f"{prefix}-{sequence:04d}"


@transaction.atomic
def checkout(cart):
    cart = Cart.objects.select_for_update().prefetch_related("items__product").get(pk=cart.pk)
    recalculate_cart(cart)
    if cart.status != Cart.Status.ACTIVE or not cart.items.exists():
        raise ValueError("The cart is empty or no longer active.")
    seat = cart.session.seat
    order = Order.objects.create(
        order_number=next_order_number(), venue=seat.screen.venue, screen=seat.screen, seat=seat,
        customer_session=cart.session, status=Order.Status.PENDING, subtotal=cart.subtotal,
        discount=cart.discount, tax=cart.tax, delivery_fee=cart.delivery_fee, total=cart.total,
    )
    OrderItem.objects.bulk_create([
        OrderItem(
            order=order, product=item.product, product_name=item.product.name,
            product_image=item.product.image, quantity=item.quantity, unit_price=item.unit_price,
            discount=item.discount, tax=item.tax, total=item.total,
        ) for item in cart.items.all()
    ])
    OrderStatusEvent.objects.create(order=order, to_status=Order.Status.PENDING, note="Checkout created")
    cart.status = Cart.Status.CHECKED_OUT
    cart.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def transition_order(order, target, user=None, note=""):
    order = Order.objects.select_for_update().get(pk=order.pk)
    allowed = TRANSITIONS.get(order.status, set())
    if target not in allowed:
        raise ValueError(f"Cannot move an order from {order.status} to {target}.")
    if user and target not in ROLE_TARGETS.get(user.role, set()):
        raise PermissionError(f"The {user.get_role_display()} role cannot set {target}.")
    previous = order.status
    order.status = target
    fields = ["status"]
    timestamp_field = TIMESTAMP_FIELDS.get(target)
    if timestamp_field:
        setattr(order, timestamp_field, timezone.now())
        fields.append(timestamp_field)
    order.save(update_fields=fields)
    OrderStatusEvent.objects.create(
        order=order, from_status=previous, to_status=target, changed_by=user, note=note
    )
    AuditLog.objects.create(
        user=user, action=f"ORDER_{target}", entity_type="Order", entity_id=str(order.public_id),
        metadata={"order_number": order.order_number, "from": previous, "to": target},
    )
    return order
