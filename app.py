
import os
import re
import hmac
import secrets
import html
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware




# =========================================================
# SHOPFLOW CONFIGURATION
# =========================================================

APP_NAME = "ShopFlow"
ADMIN_PASSWORD = "11223344"
SESSION_SECRET = os.getenv("SESSION_SECRET", "")

app = FastAPI(title="ShopFlow Electronics Store")

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET or "shopflow-local-development-secret-change-before-deployment",
    same_site="lax",
    https_only=os.getenv("COOKIE_HTTPS_ONLY", "false").lower() == "true",
    max_age=60 * 60 * 24 * 7,
)



# Demo data and orders are stored in memory for local/demo use.
# Note: in-memory data resets when the process restarts and is not reliable on Vercel.

DEMO_PRODUCTS = [
    {
        "id": "p1",
        "name": "NovaBook Pro 15",
        "category": "Laptops",
        "price": 189999,
        "stock": 8,
        "description": "A powerful everyday laptop for work, learning and creativity.",
        "image_url": "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=900",
    },
    {
        "id": "p2",
        "name": "Galaxy X Smartphone",
        "category": "Phones",
        "price": 124999,
        "stock": 12,
        "description": "A modern smartphone with a premium-inspired design.",
        "image_url": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=900",
    },
    {
        "id": "p3",
        "name": "Sonic Wireless Headphones",
        "category": "Audio",
        "price": 8999,
        "stock": 20,
        "description": "Wireless headphones for music, study and everyday listening.",
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900",
    },
    {
        "id": "p4",
        "name": "AirLite Earbuds",
        "category": "Audio",
        "price": 5499,
        "stock": 25,
        "description": "Compact everyday audio with a clean, modern design.",
        "image_url": "https://images.unsplash.com/photo-1606220945770-b5b6c2c55bf1?w=900",
    },
    {
        "id": "p5",
        "name": "UltraView Monitor",
        "category": "Accessories",
        "price": 42999,
        "stock": 6,
        "description": "A stylish monitor for productive work and entertainment.",
        "image_url": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=900",
    },
    {
        "id": "p6",
        "name": "SmartFit Watch",
        "category": "Accessories",
        "price": 12999,
        "stock": 15,
        "description": "A contemporary smartwatch-inspired everyday accessory.",
        "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=900",
    },
    {
        "id": "p7",
        "name": "NovaBook Air 14",
        "category": "Laptops",
        "price": 149999,
        "stock": 5,
        "description": "A lightweight laptop for everyday productivity.",
        "image_url": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=900",
    },
    {
        "id": "p8",
        "name": "PowerCharge Hub",
        "category": "Accessories",
        "price": 3999,
        "stock": 30,
        "description": "A compact charging accessory for your desk setup.",
        "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=900",
    },
]

memory_products = [dict(p) for p in DEMO_PRODUCTS]
memory_orders = []


# =========================================================
# HELPERS
# =========================================================

def esc(value):
    return html.escape(str(value if value is not None else ""), quote=True)


def money(value):
    try:
        amount = Decimal(str(value))
        return "PKR " + f"{amount:,.0f}"
    except (InvalidOperation, ValueError):
        return "PKR 0"


def get_products():
    return memory_products


def get_product(product_id):
    return next(
        (p for p in memory_products if str(p["id"]) == str(product_id)),
        None,
    )


def save_product(product):
    product = dict(product)
    product["id"] = secrets.token_hex(8)
    memory_products.insert(0, product)
    return product


def delete_product(product_id):
    memory_products[:] = [
        p for p in memory_products if str(p["id"]) != str(product_id)
    ]


def save_order(order):
    memory_orders.insert(0, dict(order))
    return order


def get_orders():
    return memory_orders


def find_order(order_number, email):
    return next(
        (
            order for order in memory_orders
            if str(order.get("order_number", "")).lower() == order_number.lower()
            and str(order.get("customer_email", "")).lower() == email.lower()
        ),
        None,
    )


def update_order_status(order_number, status):
    for order in memory_orders:
        if order.get("order_number") == order_number:
            order["status"] = status
            return True
    return False


def is_admin(request):
    return request.session.get("shopflow_admin") is True


def cart_data(request):
    return request.session.get("cart", {})


def cart_count(request):
    return sum(int(q) for q in cart_data(request).values())


def cart_contents(request):
    cart = cart_data(request)
    items = []
    total = Decimal("0")

    for product_id, quantity in cart.items():
        product = get_product(product_id)
        if not product:
            continue

        try:
            quantity = max(1, min(99, int(quantity)))
            price = Decimal(str(product["price"]))
        except (ValueError, InvalidOperation, TypeError, KeyError):
            continue

        subtotal = price * quantity
        total += subtotal

        items.append({
            "id": str(product["id"]),
            "name": product["name"],
            "price": float(price),
            "quantity": quantity,
            "subtotal": float(subtotal),
            "image_url": product.get("image_url", ""),
        })

    return items, total


def set_cart(request, cart):
    request.session["cart"] = cart


def page(title, content, request=None):
    count = cart_count(request) if request else 0
    nav = """
    <header class="nav">
      <a class="brand" href="/">Shop<span>Flow</span><b>.</b></a>
      <nav>
        <a href="/">Home</a>
        <a href="/track">Track Order</a>
        <a href="/cart" class="cart-link">Cart <span class="count">COUNT</span></a>
        <a href="/admin" class="admin-link">Admin Panel ↗</a>
      </nav>
    </header>
    """.replace("COUNT", str(count))

    return HTMLResponse(f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#ffffff">
<title>{esc(title)} | ShopFlow</title>
<style>
:root {{
 --blue:#38bdf8;--dark:#e5eefb;--muted:#9aabc2;--line:#253449;
 --bg:#080d18;--white:#101827;--green:#34d399;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--dark);
 font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
a{{color:inherit;text-decoration:none}}
button,input,select,textarea{{font:inherit}}
button,.btn{{cursor:pointer}}
.nav{{height:76px;background:#0d1422;border-bottom:1px solid var(--line);
 display:flex;align-items:center;justify-content:space-between;padding:0 max(5%,calc((100% - 1200px)/2));gap:20px}}
.brand{{font-size:26px;font-weight:900;letter-spacing:-1.2px;white-space:nowrap}}
.brand span{{color:var(--blue)}}.brand b{{color:#8fb2ff}}
.nav nav{{display:flex;align-items:center;gap:24px;font-size:14px;font-weight:650}}
.nav nav a:hover{{color:var(--blue)}}
.cart-link{{display:flex;gap:7px;align-items:center}}
.count{{background:#132e45;color:var(--blue);padding:4px 8px;border-radius:8px}}
.admin-link{{background:#101828;color:#fff;padding:11px 15px;border-radius:10px}}
.admin-link:hover{{color:#fff!important;background:#26344d}}
.wrap{{max-width:1200px;width:90%;margin:auto}}
.hero{{margin:35px auto 30px;border-radius:25px;overflow:hidden;
 background:linear-gradient(115deg,#101e46,#1d4ed8 67%,#5487ff);
 color:#fff;padding:65px 7%;display:grid;grid-template-columns:1.3fr .7fr;align-items:center;gap:25px}}
.eyebrow{{font-size:12px;letter-spacing:2px;font-weight:800;text-transform:uppercase;color:#c9d9ff}}
.hero h1{{font-size:clamp(38px,5.2vw,65px);letter-spacing:-2.7px;line-height:1.06;margin:16px 0}}
.hero p{{line-height:1.8;color:#e0e9ff;max-width:520px}}
.hero-art{{font-size:135px;text-align:center;filter:drop-shadow(0 15px 20px #07133470)}}
.btn{{border:0;border-radius:11px;background:var(--blue);color:#fff;padding:13px 18px;
 font-weight:750;display:inline-flex;justify-content:center;align-items:center;gap:7px}}
.btn:hover{{background:#1d4ed8}}
.btn.dark{{background:#101828}}.btn.light{{background:#132e45;color:#7dd3fc}}
.btn.danger{{background:#dc2626}}.btn.small{{padding:8px 11px;font-size:12px}}
.section-head{{display:flex;justify-content:space-between;align-items:end;gap:15px;margin:35px 0 20px}}
.section-head h2{{font-size:28px;letter-spacing:-1px;margin:5px 0}}
.muted{{color:var(--muted)}}.small-text{{font-size:13px}}
.searchbar{{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}}
.field{{width:100%;padding:12px 14px;border:1px solid #dfe4ec;border-radius:10px;background:#0b1321;outline:none}}
.field:focus{{border-color:var(--blue);box-shadow:0 0 0 3px #38bdf825}}
.search{{flex:1;min-width:200px}}
select.field{{cursor:pointer}}
.categories{{display:flex;gap:9px;flex-wrap:wrap;margin-bottom:22px}}
.chip{{padding:9px 15px;border:1px solid var(--line);border-radius:999px;background:#fff;
 color:#475467;font-weight:650;font-size:13px}}
.chip.active,.chip:hover{{background:#132e45;color:var(--blue);border-color:#cddaff}}
.grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:20px;margin:20px 0 60px}}
.product{{background:#101827;border:1px solid var(--line);border-radius:17px;overflow:hidden;transition:.2s}}
.product:hover{{transform:translateY(-4px);box-shadow:0 12px 35px #00000040}}
.product-image{{height:205px;background:#111f32;display:flex;align-items:center;justify-content:center;overflow:hidden}}
.product-image img{{width:100%;height:100%;object-fit:cover;transition:transform .3s}}
.product:hover img{{transform:scale(1.04)}}
.product-body{{padding:17px}}
.tag{{font-size:11px;text-transform:uppercase;letter-spacing:1px;font-weight:800;color:var(--blue)}}
.product h3{{font-size:16px;margin:9px 0;line-height:1.4}}
.desc{{font-size:13px;line-height:1.6;color:var(--muted);min-height:40px}}
.price{{font-size:19px;font-weight:850;margin:15px 0}}
.product-actions{{display:flex;gap:8px}}
.product-actions .btn{{flex:1;padding:10px 7px;font-size:12px}}
.card{{background:#101827;border:1px solid var(--line);border-radius:17px;padding:25px;margin:25px 0}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:25px}}
.form-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
.form-group{{display:flex;flex-direction:column;gap:7px;margin-bottom:14px}}
.form-group label{{font-size:13px;font-weight:750}}
.full{{grid-column:1/-1}}
.table-wrap{{overflow-x:auto}}
table{{border-collapse:collapse;width:100%;font-size:13px}}
th,td{{padding:13px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}
th{{background:#172338;color:#9aabc2;font-size:11px;text-transform:uppercase;letter-spacing:.6px}}
.notice{{border-radius:12px;padding:14px 16px;margin:16px 0;background:#102a3d;color:#bae6fd;line-height:1.6}}
.error{{background:#3a1b28;color:#fecdd3}}
.success{{background:#10352d;color:#a7f3d0}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin:22px 0}}
.stat{{background:#101827;border:1px solid var(--line);border-radius:15px;padding:20px}}
.stat span{{font-size:12px;color:var(--muted)}}.stat strong{{display:block;font-size:24px;margin-top:10px}}
.admin-heading{{display:flex;align-items:center;justify-content:space-between;gap:15px;flex-wrap:wrap;margin:35px 0}}
.status{{display:inline-block;border-radius:99px;padding:5px 9px;background:#132e45;color:#7dd3fc;font-size:11px;font-weight:800}}
footer{{background:#0d1422;border-top:1px solid var(--line);padding:28px 5%;color:var(--muted);font-size:13px}}
footer .foot-inner{{max-width:1200px;margin:auto;display:flex;justify-content:space-between;gap:15px;flex-wrap:wrap}}
.empty{{background:#101827;border:1px dashed #33445e;border-radius:16px;padding:50px 20px;text-align:center;margin:25px 0}}
.empty .emoji{{font-size:50px}}
hr{{border:0;border-top:1px solid var(--line);margin:20px 0}}
@media(max-width:900px){{.grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}.hero{{grid-template-columns:1fr;padding:40px 7%}}.hero-art{{display:none}}}}
@media(max-width:600px){{
 .nav{{height:auto;min-height:70px;padding:15px 5%;align-items:flex-start;flex-wrap:wrap}}
 .nav nav{{gap:11px;flex-wrap:wrap;font-size:12px}}
 .admin-link{{padding:8px 10px}}
 .grid{{gap:11px}}.product-image{{height:145px}}.product-body{{padding:12px}}
 .product h3{{font-size:14px}}.desc{{font-size:12px}}.price{{font-size:16px}}
 .product-actions{{flex-direction:column}}.hero h1{{letter-spacing:-1.5px}}
 .two-col,.form-grid{{grid-template-columns:1fr}}.full{{grid-column:auto}}
 .stats{{grid-template-columns:1fr}}.section-head{{align-items:start;flex-direction:column}}
}}

/* Dark electronics theme overrides */
.nav {{ background:#0d1422 !important; border-color:#253449 !important; }}
.nav nav a:hover {{ color:#7dd3fc !important; }}
.brand span, .tag, .eyebrow {{ color:#38bdf8; }}
.count {{ background:#132e45 !important; color:#7dd3fc !important; }}
.admin-link {{ background:#1c2b40 !important; color:#f1f5f9 !important; }}
body {{ background:#080d18 !important; color:#e5eefb !important; }}
.product, .card, .stat, .empty {{ background:#101827 !important; border-color:#253449 !important; color:#e5eefb; }}
.product-image {{ background:#111f32 !important; }}
.field {{ background:#0b1321 !important; color:#e5eefb !important; border-color:#2d3d53 !important; }}
.field::placeholder {{ color:#71839e; }}
.chip {{ background:#101827 !important; color:#bdcce0 !important; border-color:#253449 !important; }}
.chip.active, .chip:hover {{ background:#132e45 !important; color:#7dd3fc !important; border-color:#24506b !important; }}
th {{ background:#172338 !important; color:#9aabc2 !important; }}
td, th {{ border-color:#253449 !important; }}
.notice {{ background:#102a3d !important; color:#bae6fd !important; }}
.notice.error {{ background:#3a1b28 !important; color:#fecdd3 !important; }}
.notice.success {{ background:#10352d !important; color:#a7f3d0 !important; }}
.status {{ background:#132e45 !important; color:#7dd3fc !important; }}
footer {{ background:#0d1422 !important; border-color:#253449 !important; color:#9aabc2 !important; }}
hr {{ border-color:#253449 !important; }}
.btn.light {{ background:#132e45 !important; color:#7dd3fc !important; }}
.btn.dark {{ background:#26364d !important; color:#f1f5f9 !important; }}

</style>
</head>
<body>
{nav}
{content}
<footer><div class="foot-inner">
 <div><strong style="color:#2563eb">ShopFlow.</strong> Technology made simple.</div>
 <div>Electronics storefront · Built with Python & FastAPI</div>
</div></footer>
</body></html>""")


def require_admin(request):
    if not is_admin(request):
        return RedirectResponse("/admin", status_code=303)
    return None


# =========================================================
# HOME / PRODUCT CATALOG
# =========================================================

@app.get("/", response_class=HTMLResponse)
def home(request: Request, q: str = "", category: str = "All"):
    products = get_products()
    categories = ["All"] + sorted(
        {str(p.get("category", "Other")) for p in products}
    )

    q_lower = q.strip().lower()
    filtered = [
        p for p in products
        if (
            category == "All"
            or p.get("category", "Other") == category
        )
        and (
            not q_lower
            or q_lower in str(p.get("name", "")).lower()
            or q_lower in str(p.get("category", "")).lower()
            or q_lower in str(p.get("description", "")).lower()
        )
    ]

    category_buttons = "".join(
        f'<a class="chip {"active" if c == category else ""}" '
        f'href="/?category={esc(c)}&q={esc(q)}">{esc(c)}</a>'
        for c in categories
    )

    product_cards = ""
    for p in filtered:
        pid = esc(p.get("id"))
        image = esc(p.get("image_url", ""))
        product_cards += f"""
        <article class="product">
          <a class="product-image" href="/product/{pid}">
            <img src="{image}" alt="{esc(p.get('name'))}"
                 loading="lazy"
                 onerror="this.style.display='none';this.parentElement.style.fontSize='65px';this.parentElement.textContent='📦'">
          </a>
          <div class="product-body">
            <span class="tag">{esc(p.get('category'))}</span>
            <h3><a href="/product/{pid}">{esc(p.get('name'))}</a></h3>
            <div class="desc">{esc(p.get('description'))}</div>
            <div class="price">{money(p.get('price', 0))}</div>
            <div class="product-actions">
              <a class="btn light" href="/product/{pid}">Details</a>
              <form action="/cart/add/{pid}" method="post" style="flex:1">
                <button class="btn" style="width:100%" type="submit">Add to Cart +</button>
              </form>
            </div>
          </div>
        </article>
        """

    if not filtered:
        product_cards = """
        <div class="empty" style="grid-column:1/-1">
          <div class="emoji">🔎</div><h3>No products found</h3>
          <p class="muted">Try another search or category.</p>
          <a class="btn" href="/">View all products</a>
        </div>
        """

    content = f"""
    <main class="wrap">
      <section class="hero">
        <div>
          <div class="eyebrow">Your next tech upgrade starts here</div>
          <h1>Technology.<br>Made <span style="color:#9fbdff">simple.</span></h1>
          <p>Discover laptops, smartphones, audio gear and accessories
          selected for your everyday setup.</p>
          <a href="#products" class="btn" style="background:white;color:#1747b7">
            Explore the collection ↗
          </a>
        </div>
        <div class="hero-art">💻</div>
      </section>

      <section id="products">
        <div class="section-head">
          <div><div class="eyebrow" style="color:#2563eb">THE COLLECTION</div>
          <h2>Find your next favorite.</h2>
          <div class="muted small-text">{len(filtered)} products to explore</div></div>
        </div>
        <form action="/" method="get" class="searchbar">
          <input class="field search" name="q" value="{esc(q)}"
                 placeholder="Search laptops, phones, headphones...">
          <select class="field" name="category" style="width:auto;min-width:155px">
            {''.join(f'<option value="{esc(c)}" {"selected" if c == category else ""}>{esc(c)}</option>' for c in categories)}
          </select>
          <button class="btn">Search products</button>
        </form>
        <div class="categories">{category_buttons}</div>
        <div class="grid">{product_cards}</div>
      </section>
    </main>
    """
    return page("Electronics & Gadgets", content, request)


@app.get("/product/{product_id}", response_class=HTMLResponse)
def product_detail(request: Request, product_id: str):
    p = get_product(product_id)
    if not p:
        return page("Product not found", """
        <main class="wrap"><div class="empty"><h2>Product not found</h2>
        <a class="btn" href="/">Back to shop</a></div></main>
        """, request)

    content = f"""
    <main class="wrap">
      <div style="margin:30px 0"><a href="/" class="muted">← Back to shop</a></div>
      <div class="card two-col">
        <div class="product-image" style="height:360px;border-radius:13px">
          <img src="{esc(p.get('image_url',''))}" alt="{esc(p.get('name'))}"
          onerror="this.style.display='none';this.parentElement.textContent='📦';this.parentElement.style.fontSize='100px'">
        </div>
        <div style="padding:15px 5px">
          <span class="tag">{esc(p.get('category'))}</span>
          <h1 style="font-size:35px;letter-spacing:-1.5px">{esc(p.get('name'))}</h1>
          <div class="price" style="font-size:28px">{money(p.get('price',0))}</div>
          <p class="muted" style="line-height:1.9">{esc(p.get('description'))}</p>
          <p class="small-text muted">Availability: {int(p.get('stock',0))} in stock</p>
          <form action="/cart/add/{esc(p.get('id'))}" method="post">
            <button class="btn" type="submit">Add to cart →</button>
          </form>
        </div>
      </div>
    </main>
    """
    return page(p["name"], content, request)


# =========================================================
# CART
# =========================================================

@app.post("/cart/add/{product_id}")
def add_to_cart(request: Request, product_id: str):
    product = get_product(product_id)
    if not product:
        return RedirectResponse("/", status_code=303)

    try:
        if int(product.get("stock", 0)) <= 0:
            return RedirectResponse("/cart", status_code=303)
    except (ValueError, TypeError):
        return RedirectResponse("/", status_code=303)

    cart = cart_data(request).copy()
    cart[product_id] = min(99, int(cart.get(product_id, 0)) + 1)
    set_cart(request, cart)
    return RedirectResponse("/cart", status_code=303)


@app.post("/cart/update")
def update_cart(request: Request, product_id: str = Form(...), quantity: int = Form(...)):
    cart = cart_data(request).copy()
    product = get_product(product_id)

    if not product or quantity <= 0:
        cart.pop(product_id, None)
    else:
        cart[product_id] = min(99, quantity)

    set_cart(request, cart)
    return RedirectResponse("/cart", status_code=303)


@app.get("/cart", response_class=HTMLResponse)
def view_cart(request: Request):
    items, total = cart_contents(request)

    if not items:
        content = """
        <main class="wrap"><div class="empty">
          <div class="emoji">🛍️</div><h1>Your cart is waiting</h1>
          <p class="muted">Explore the collection and add something you love.</p>
          <a class="btn" href="/">Explore products →</a>
        </div></main>
        """
        return page("Your Cart", content, request)

    rows = ""
    for item in items:
        rows += f"""
        <tr>
          <td><strong>{esc(item['name'])}</strong><br>
          <span class="muted">{money(item['price'])} each</span></td>
          <td>
            <form action="/cart/update" method="post" style="display:flex;gap:5px">
              <input type="hidden" name="product_id" value="{esc(item['id'])}">
              <input class="field" type="number" name="quantity" min="0" max="99"
                value="{item['quantity']}" style="width:78px;padding:8px">
              <button class="btn light small">Update</button>
            </form>
          </td>
          <td><strong>{money(item['subtotal'])}</strong></td>
        </tr>
        """

    content = f"""
    <main class="wrap">
      <div class="section-head"><div><div class="eyebrow" style="color:#2563eb">YOUR SELECTION</div>
      <h2>Shopping cart</h2></div><a href="/" class="btn light">Continue shopping</a></div>
      <div class="card table-wrap"><table>
        <thead><tr><th>Product</th><th>Quantity</th><th>Subtotal</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
      <div style="display:flex;justify-content:flex-end;margin-top:25px">
        <div style="width:100%;max-width:340px">
          <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:850">
            <span>Total</span><span>{money(total)}</span>
          </div>
          <p class="muted small-text">Shipping charges, if any, will be confirmed separately.</p>
          <a href="/checkout" class="btn" style="width:100%;margin-top:12px">Proceed to Checkout →</a>
        </div>
      </div></div>
    </main>
    """
    return page("Shopping Cart", content, request)


# =========================================================
# CHECKOUT
# =========================================================

@app.get("/checkout", response_class=HTMLResponse)
def checkout_page(request: Request):
    items, total = cart_contents(request)

    if not items:
        return RedirectResponse("/cart", status_code=303)

    content = f"""
    <main class="wrap">
      <div class="section-head"><div><div class="eyebrow" style="color:#2563eb">ALMOST THERE</div>
      <h2>Checkout</h2><p class="muted">Enter your details to place your order.</p></div></div>
      <div class="two-col">
        <form class="card" action="/checkout" method="post">
          <h3>Customer details</h3>
          <div class="form-group"><label>Full name</label>
            <input class="field" name="customer_name" required maxlength="100"></div>
          <div class="form-grid">
            <div class="form-group"><label>Email address</label>
              <input class="field" type="email" name="customer_email" required maxlength="254"></div>
            <div class="form-group"><label>Phone number</label>
              <input class="field" name="customer_phone" required maxlength="30"></div>
            <div class="form-group full"><label>Delivery address</label>
              <textarea class="field" name="address" rows="3" required maxlength="500"></textarea></div>
          </div>
          <div class="notice">Demo checkout: payment is not collected online. Confirm payment and delivery arrangements with the store.</div>
          <button class="btn" style="width:100%">Place Order · {money(total)}</button>
        </form>
        <div class="card">
          <h3>Order summary</h3>
          {''.join(f'<p>{esc(i["name"])} × {i["quantity"]}<br><strong>{money(i["subtotal"])}</strong></p>' for i in items)}
          <hr><div style="display:flex;justify-content:space-between;font-size:19px;font-weight:850">
            <span>Total</span><span>{money(total)}</span></div>
        </div>
      </div>
    </main>
    """
    return page("Checkout", content, request)


@app.post("/checkout", response_class=HTMLResponse)
def checkout(
    request: Request,
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    customer_phone: str = Form(...),
    address: str = Form(...),
):
    items, total = cart_contents(request)

    customer_name = customer_name.strip()
    customer_email = customer_email.strip().lower()
    customer_phone = customer_phone.strip()
    address = address.strip()

    if not items:
        return RedirectResponse("/cart", status_code=303)

    if (
        not customer_name or len(customer_name) > 100
        or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", customer_email)
        or len(customer_email) > 254
        or not customer_phone or len(customer_phone) > 30
        or not address or len(address) > 500
    ):
        return page("Invalid details", """
        <main class="wrap"><div class="notice error">Please check your name, email, phone and address.</div>
        <a class="btn" href="/checkout">Return to checkout</a></main>
        """, request)

    # Recheck stock and current prices before accepting the order.
    fresh_items = []
    total = Decimal("0")

    for item in items:
        p = get_product(item["id"])
        if not p:
            return page("Unavailable", """
            <main class="wrap"><div class="notice error">A product is no longer available. Please review your cart.</div>
            <a class="btn" href="/cart">Return to cart</a></main>
            """, request)

        quantity = int(item["quantity"])
        stock = int(p.get("stock", 0))

        if stock < quantity:
            return page("Insufficient stock", f"""
            <main class="wrap"><div class="notice error">
            Not enough stock for {esc(p['name'])}. Available: {stock}.
            </div><a class="btn" href="/cart">Review cart</a></main>
            """, request)

        price = Decimal(str(p["price"]))
        subtotal = price * quantity
        total += subtotal

        fresh_items.append({
            "product_id": str(p["id"]),
            "name": str(p["name"]),
            "price": float(price),
            "quantity": quantity,
            "subtotal": float(subtotal),
        })

    order_number = "SF-" + secrets.token_hex(4).upper()

    order = {
        "order_number": order_number,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        "address": address,
        "items": fresh_items,
        "total": float(total),
        "status": "New",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        saved = save_order(order)
        if not saved:
            raise RuntimeError("Order was not saved")
    except Exception:
        return page("Order not saved", """
        <main class="wrap"><div class="notice error">
        We could not save your order. Please try again later. No payment has been taken.
        </div><a class="btn" href="/checkout">Try again</a></main>
        """, request)

    # Reduce inventory after the order has been recorded.
    for item in fresh_items:
        product = get_product(item["product_id"])
        if product:
            product["stock"] = max(0, int(product.get("stock", 0)) - int(item["quantity"]))

    # Clear cart after successful order creation.
    set_cart(request, {})

    content = f"""
    <main class="wrap"><div class="empty">
      <div class="emoji">✓</div>
      <div class="eyebrow" style="color:#07845c">ORDER RECEIVED</div>
      <h1>Thank you, {esc(customer_name)}!</h1>
      <p class="muted">Your order has been recorded.</p>
      <div class="card" style="max-width:460px;margin:25px auto;text-align:left">
        <p class="muted small-text">YOUR ORDER NUMBER</p>
        <h2 style="color:#2563eb;letter-spacing:1px">{esc(order_number)}</h2>
        <hr>
        <div style="display:flex;justify-content:space-between">
          <span>Total</span><strong>{money(total)}</strong></div>
        <div style="display:flex;justify-content:space-between;margin-top:12px">
          <span>Status</span><span class="status">New</span></div>
      </div>
      <p class="muted small-text">Save your order number. Track your order using this number and your checkout email.</p>
      <a class="btn" href="/track">Track your order →</a>
      <a class="btn light" href="/" style="margin-left:8px">Continue shopping</a>
    </div></main>
    """
    return page("Order Confirmation", content, request)


# =========================================================
# ORDER TRACKING
# =========================================================

@app.get("/track", response_class=HTMLResponse)
def track_page(request: Request, number: str = "", email: str = ""):
    result_html = ""

    if number and email:
        try:
            order = find_order(number.strip(), email.strip())
        except Exception:
            order = None

        if order:
            items = order.get("items") or []
            if isinstance(items, str):
                import json
                try:
                    items = json.loads(items)
                except Exception:
                    items = []

            item_rows = "".join(
                f"<li>{esc(i.get('name','Product'))} × {esc(i.get('quantity',1))}</li>"
                for i in items
            )

            result_html = f"""
            <div class="card">
              <div class="eyebrow" style="color:#2563eb">ORDER FOUND</div>
              <h2>{esc(order.get('order_number'))}</h2>
              <p>Status: <span class="status">{esc(order.get('status','New'))}</span></p>
              <p>Total: <strong>{money(order.get('total',0))}</strong></p>
              <p class="muted small-text">Placed: {esc(order.get('created_at',''))}</p>
              <h3>Items</h3><ul>{item_rows}</ul>
            </div>
            """
        else:
            result_html = """
            <div class="notice error">We couldn't find an order matching those details.
            Check the order number and the email used at checkout.</div>
            """

    content = f"""
    <main class="wrap" style="max-width:780px">
      <div class="section-head"><div><div class="eyebrow" style="color:#2563eb">ORDER UPDATES</div>
      <h2>Track your order.</h2><p class="muted">Use your order number and checkout email to view the latest status.</p></div></div>
      <form class="card" method="get" action="/track">
        <div class="form-group"><label>Order number</label>
          <input class="field" name="number" value="{esc(number)}" placeholder="e.g. SF-A1B2C3D4" required></div>
        <div class="form-group"><label>Checkout email</label>
          <input class="field" type="email" name="email" value="{esc(email)}" placeholder="you@example.com" required></div>
        <button class="btn" style="width:100%">Find my order →</button>
      </form>
      {result_html}
    </main>
    """
    return page("Track Order", content, request)


# =========================================================
# ADMIN LOGIN AND DASHBOARD
# =========================================================

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, error: str = ""):
    if is_admin(request):
        return admin_dashboard(request)

    warning = ""
    if not ADMIN_PASSWORD:
        warning = """
        <div class="notice error">
        Admin login is disabled until you configure the ADMIN_PASSWORD environment variable.
        Do not use a public demo password in production.
        </div>
        """
    elif error:
        warning = '<div class="notice error">Incorrect password. Please try again.</div>'

    content = f"""
    <main class="wrap" style="max-width:530px">
      <div class="section-head"><div><div class="eyebrow" style="color:#2563eb">RESTRICTED ACCESS</div>
      <h2>Admin Panel</h2><p class="muted">Sign in to manage your ShopFlow store.</p></div></div>
      {warning}
      <form class="card" method="post" action="/admin/login">
        <div class="form-group"><label>Admin password</label>
          <input class="field" type="password" name="password" required autocomplete="current-password"
          placeholder="Enter your admin password"></div>
        <button class="btn" style="width:100%" {"disabled" if not ADMIN_PASSWORD else ""}>
          Unlock Admin Panel →
        </button>
        <p class="muted small-text" style="margin-top:15px">Authorized store administrators only.</p>
      </form>
      <a href="/" class="muted small-text">← Return to storefront</a>
    </main>
    """
    return page("Admin Login", content, request)


@app.post("/admin/login")
def admin_login(request: Request, password: str = Form(...)):
    if not ADMIN_PASSWORD:
        return RedirectResponse("/admin", status_code=303)

    if hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode()):
        request.session["shopflow_admin"] = True
        return RedirectResponse("/admin/dashboard", status_code=303)

    return RedirectResponse("/admin?error=1", status_code=303)


@app.post("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/admin/dashboard", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    if not is_admin(request):
        return RedirectResponse("/admin", status_code=303)

    try:
        products = get_products()
        orders = get_orders()
    except Exception:
        return page("Admin Error", """
        <main class="wrap"><div class="notice error">Could not load store data. Please try again.</div></main>
        """, request)

    revenue = sum(
        float(o.get("total", 0))
        for o in orders
        if str(o.get("status", "")).lower() != "cancelled"
    )

    order_rows = ""
    for o in orders:
        order_no = esc(o.get("order_number", ""))
        status = str(o.get("status", "New"))
        order_rows += f"""
        <tr>
          <td><strong>{order_no}</strong><br><span class="muted">{esc(o.get('customer_name',''))}</span></td>
          <td>{esc(o.get('customer_email',''))}<br>{esc(o.get('customer_phone',''))}</td>
          <td><strong>{money(o.get('total',0))}</strong></td>
          <td>
            <form action="/admin/order-status" method="post" style="display:flex;gap:5px;min-width:190px">
              <input type="hidden" name="order_number" value="{order_no}">
              <select class="field" name="status" style="padding:7px">
                {''.join(f'<option value="{s}" {"selected" if s == status else ""}>{s}</option>' for s in ["New","Processing","Shipped","Completed","Cancelled"])}
              </select>
              <button class="btn small">Save</button>
            </form>
          </td>
        </tr>
        """

    product_rows = ""
    for p in products:
        product_rows += f"""
        <tr>
          <td><strong>{esc(p.get('name'))}</strong><br><span class="muted">{esc(p.get('category'))}</span></td>
          <td>{money(p.get('price',0))}</td>
          <td>{esc(p.get('stock',0))}</td>
          <td>
            <form action="/admin/product-delete" method="post"
              onsubmit="return confirm('Delete this product?')">
              <input type="hidden" name="product_id" value="{esc(p.get('id'))}">
              <button class="btn danger small">Delete</button>
            </form>
          </td>
        </tr>
        """

    content = f"""
    <main class="wrap">
      <div class="admin-heading">
        <div><div class="eyebrow" style="color:#2563eb">STORE CONTROL CENTER</div>
        <h1 style="font-size:34px;letter-spacing:-1px;margin:7px 0">Admin Dashboard</h1>
        <p class="muted">Manage your catalog and incoming orders.</p></div>
        <form action="/admin/logout" method="post"><button class="btn dark">Sign out ↗</button></form>
      </div>

      <div class="stats">
        <div class="stat"><span>Total products</span><strong>{len(products)}</strong></div>
        <div class="stat"><span>Total orders</span><strong>{len(orders)}</strong></div>
        <div class="stat"><span>Recorded revenue</span><strong style="font-size:20px">{money(revenue)}</strong></div>
      </div>

      <section class="card">
        <h2>Add a product</h2>
        <p class="muted small-text">Use a direct image URL. Prices are in Pakistani rupees.</p>
        <form action="/admin/product-add" method="post">
          <div class="form-grid">
            <div class="form-group"><label>Product name</label><input class="field" name="name" required maxlength="120"></div>
            <div class="form-group"><label>Category</label>
              <select class="field" name="category">
                <option>Laptops</option><option>Phones</option><option>Audio</option>
                <option>Accessories</option><option>Gaming</option><option>Other</option>
              </select></div>
            <div class="form-group"><label>Price (PKR)</label><input class="field" name="price" type="number" min="1" max="100000000" step="1" required></div>
            <div class="form-group"><label>Stock quantity</label><input class="field" name="stock" type="number" min="0" max="100000" value="10" required></div>
            <div class="form-group full"><label>Image URL</label><input class="field" type="url" name="image_url" maxlength="1000" placeholder="https://example.com/product.jpg"></div>
            <div class="form-group full"><label>Description</label><textarea class="field" name="description" rows="3" required maxlength="1000"></textarea></div>
          </div>
          <button class="btn">+ Add Product</button>
        </form>
      </section>

      <section class="card">
        <h2>Product inventory</h2>
        <div class="table-wrap"><table>
          <thead><tr><th>Product</th><th>Price</th><th>Stock</th><th>Action</th></tr></thead>
          <tbody>{product_rows or '<tr><td colspan="4">No products yet.</td></tr>'}</tbody>
        </table></div>
      </section>

      <section class="card">
        <h2>Incoming orders</h2>
        <p class="muted small-text">Update order status as you process each purchase.</p>
        <div class="table-wrap"><table>
          <thead><tr><th>Order / Customer</th><th>Contact</th><th>Total</th><th>Status</th></tr></thead>
          <tbody>{order_rows or '<tr><td colspan="4">No orders yet.</td></tr>'}</tbody>
        </table></div>
      </section>
    </main>
    """
    return page("Admin Dashboard", content, request)


@app.post("/admin/product-add")
def admin_add_product(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    price: int = Form(...),
    stock: int = Form(...),
    image_url: str = Form(""),
    description: str = Form(...),
):
    if not is_admin(request):
        return RedirectResponse("/admin", status_code=303)

    name = name.strip()
    description = description.strip()
    image_url = image_url.strip()
    allowed_categories = {
        "Laptops", "Phones", "Audio", "Accessories", "Gaming", "Other"
    }

    if (
        not name or len(name) > 120
        or not description or len(description) > 1000
        or category not in allowed_categories
        or price < 1 or price > 100_000_000
        or stock < 0 or stock > 100_000
        or (image_url and not image_url.startswith(("https://", "http://")))
    ):
        return RedirectResponse("/admin/dashboard", status_code=303)

    try:
        save_product({
            "name": name,
            "category": category,
            "price": price,
            "stock": stock,
            "description": description,
            "image_url": image_url,
        })
    except Exception:
        return HTMLResponse(
            "Could not save the product. Please try again.",
            status_code=500,
        )

    return RedirectResponse("/admin/dashboard", status_code=303)


@app.post("/admin/product-delete")
def admin_delete_product(request: Request, product_id: str = Form(...)):
    if not is_admin(request):
        return RedirectResponse("/admin", status_code=303)

    try:
        delete_product(product_id)
    except Exception:
        return HTMLResponse("Could not delete product.", status_code=500)

    return RedirectResponse("/admin/dashboard", status_code=303)


@app.post("/admin/order-status")
def admin_order_status(
    request: Request,
    order_number: str = Form(...),
    status: str = Form(...),
):
    if not is_admin(request):
        return RedirectResponse("/admin", status_code=303)

    allowed = {"New", "Processing", "Shipped", "Completed", "Cancelled"}
    if status not in allowed:
        return RedirectResponse("/admin/dashboard", status_code=303)

    try:
        update_order_status(order_number, status)
    except Exception:
        return HTMLResponse("Could not update the order status.", status_code=500)

    return RedirectResponse("/admin/dashboard", status_code=303)


@app.get("/health")
def health():
    return {
        "app": APP_NAME,
        "status": "running",
        "storage": "in-memory demo storage",
    }
