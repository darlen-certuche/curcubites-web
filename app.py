import json
import os
import base64
from pathlib import Path
from urllib.parse import quote

import streamlit as st


BASE_DIR = Path(__file__).parent
PRODUCTS_PATH = BASE_DIR / "data" / "products.json"
DEFAULT_EMAIL = "ventas@curcubites.com"


st.set_page_config(
    page_title="Curcubites | Chips de plátano horneadas",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def money(value: int) -> str:
    return f"${value:,.0f}".replace(",", ".")


@st.cache_data
def load_products() -> list[dict]:
    with PRODUCTS_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def get_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return os.getenv(name, default)


def ensure_cart() -> None:
    if "cart" not in st.session_state:
        st.session_state.cart = {}


def add_to_cart(product_id: str, qty: int = 1) -> None:
    ensure_cart()
    st.session_state.cart[product_id] = st.session_state.cart.get(product_id, 0) + qty


def remove_from_cart(product_id: str) -> None:
    ensure_cart()
    st.session_state.cart.pop(product_id, None)


def update_quantity(product_id: str, qty: int) -> None:
    ensure_cart()
    if qty <= 0:
        remove_from_cart(product_id)
    else:
        st.session_state.cart[product_id] = qty


def cart_items(products: list[dict]) -> list[dict]:
    ensure_cart()
    by_id = {product["id"]: product for product in products}
    return [
        {**by_id[product_id], "qty": qty, "subtotal": int(by_id[product_id]["price"]) * qty}
        for product_id, qty in st.session_state.cart.items()
        if product_id in by_id
    ]


def cart_total(items: list[dict]) -> int:
    return sum(item["subtotal"] for item in items)


def order_message(items: list[dict], name: str, phone: str, city: str, address: str, notes: str) -> str:
    lines = [
        "Hola, quiero hacer un pedido de Curcubites:",
        "",
        *[f"- {item['qty']} x {item['name']} = {money(item['subtotal'])}" for item in items],
        "",
        f"Total: {money(cart_total(items))}",
        "",
        f"Nombre: {name}",
        f"WhatsApp: {phone}",
        f"Ciudad: {city}",
        f"Dirección: {address}",
    ]
    if notes:
        lines.append(f"Notas: {notes}")
    return "\n".join(lines)


def whatsapp_url(message: str) -> str:
    number = get_secret("WHATSAPP_NUMBER", "573008901210").strip().replace("+", "")
    base = f"https://wa.me/{number}"
    return f"{base}?text={quote(message)}"


def mailto_url(message: str) -> str:
    email = get_secret("ORDER_EMAIL", DEFAULT_EMAIL)
    return f"mailto:{email}?subject={quote('Pedido Curcubites')}&body={quote(message)}"


@st.cache_data
def image_data_uri(path_str: str) -> str:
    path = Path(path_str)
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def _logo_svg(size: int) -> str:
    """
    Inline SVG logo. NO filter on text — filter ref failure makes text invisible.
    Gradients only for ring + wave. Solid #F5A01A for text (reliable).
    ViewBox 300×300. Ring r=145 outer, r=135 inner disc.
    Text font-size 44 ≈ 220px wide → ~25px inset each side from disc edge.
    Wave x=78..224 → ~30px inset from disc edge.
    Unique ID suffix = size avoids gradient collision when logo appears twice.
    """
    u = size
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300"'
        f' width="{size}" height="{size}" aria-label="Logo Curcubites" role="img"'
        f' class="notranslate" translate="no">'
        f'<defs>'
        f'<linearGradient id="lgg{u}" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="#F5C042"/>'
        f'<stop offset="50%" stop-color="#F5A01A"/>'
        f'<stop offset="100%" stop-color="#E8900A"/>'
        f'</linearGradient>'
        f'<linearGradient id="lgw1{u}" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="#4CAF50"/>'
        f'<stop offset="45%" stop-color="#8BC34A"/>'
        f'<stop offset="100%" stop-color="#2E7D32"/>'
        f'</linearGradient>'
        f'<linearGradient id="lgw2{u}" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%" stop-color="#388E3C"/>'
        f'<stop offset="55%" stop-color="#66BB6A"/>'
        f'<stop offset="100%" stop-color="#43A047"/>'
        f'</linearGradient>'
        f'</defs>'
        f'<circle cx="150" cy="150" r="145" fill="url(#lgg{u})"/>'
        f'<circle cx="150" cy="150" r="135" fill="#FFFFFF"/>'
        f'<text x="150" y="168"'
        f' font-family="Georgia,serif"'
        f' font-size="44" font-weight="700" font-style="italic"'
        f' fill="#F5A01A" text-anchor="middle" class="notranslate" translate="no">Curcubites</text>'
        f'<path d="M78 194 C108 182,132 190,150 187 C170 184,196 176,224 183"'
        f' stroke="url(#lgw1{u})" stroke-width="5" fill="none"'
        f' stroke-linecap="round"/>'
        f'<path d="M82 202 C112 190,134 198,150 195 C170 192,196 184,222 191"'
        f' stroke="url(#lgw2{u})" stroke-width="2.8" fill="none"'
        f' stroke-linecap="round" opacity="0.68"/>'
        f'</svg>'
    )


def _cart_btn_uri() -> str:
    """Cart SVG encoded as base64 data URI for safe use as CSS background-image."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24"'
        ' fill="none" stroke="#FFF6E6" stroke-width="2.2"'
        ' stroke-linecap="round" stroke-linejoin="round">'
        '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>'
        '<path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>'
        '</svg>'
    )
    return f"data:image/svg+xml;base64,{base64.b64encode(svg.encode()).decode()}"



def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,700;0,800;0,900;1,400&family=Playfair+Display:wght@700;800;900&display=swap');

        :root {
          --ink: #151A12;
          --olive: #0F1A0C;
          --green: #245C2A;
          --green-2: #3A7A41;
          --leaf: #E7F1DF;
          --cream: #FFF6E6;
          --cream-2: #F4EAD6;
          --paper: #FFFFFF;
          --turmeric: #D99A22;
          --terracotta: #A85232;
          --line: #E2D5BB;
          --muted: #50564C;
        }

        html { scroll-behavior: smooth; overscroll-behavior: contain; }
        .stApp { background: var(--cream); color: var(--ink); }
        html, body, [class*="css"] { font-family: 'DM Sans', system-ui, sans-serif; }

        /* ── Hide ALL Streamlit chrome: header, toolbar, footer, deploy badge,
              "Created by" viewer badge, status widget ── */
        #MainMenu,
        header,
        footer,
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"],
        [data-testid="stDeployButton"],
        .stDeployButton,
        .viewerBadge_container__1QSob,
        .viewerBadge_link__qRIco,
        [class*="viewerBadge"],
        [class*="watermark"],
        [class*="ProfileBadge"] {
          display: none !important;
          visibility: hidden !important;
          height: 0 !important;
          width: 0 !important;
          opacity: 0 !important;
          pointer-events: none !important;
        }
        [data-testid="stSidebar"] { display: none; }
        [data-testid="stMainBlockContainer"] {
          max-width: 1140px;
          padding: 1rem 1.35rem 3.2rem !important;
        }

        .topbar {
          position: sticky;
          top: 0;
          z-index: 20;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          background: rgba(255, 246, 230, 0.92);
          backdrop-filter: blur(14px);
          border: 1px solid var(--line);
          border-radius: 8px;
          padding: 0.78rem 0.95rem;
          margin-bottom: 1.2rem;
        }
        .brand-lockup { display: flex; align-items: center; gap: 0.72rem; }
        .brand-logo { display: block; flex-shrink: 0; line-height: 0; }
        .brand-name { font-weight: 900; letter-spacing: 0; line-height: 1; }
        .brand-sub { font-size: 0.72rem; color: var(--muted); margin-top: 0.12rem; }
        .navlinks { display: flex; align-items: center; gap: 0.45rem; flex-wrap: wrap; justify-content: flex-end; }
        .navlinks a {
          color: var(--ink) !important; text-decoration: none !important;
          font-size: 0.84rem; font-weight: 800;
          padding: 0.48rem 0.72rem; border-radius: 999px;
          min-height: 44px;
          display: inline-flex;
          align-items: center;
          touch-action: manipulation;
          transition: background 180ms ease, color 180ms ease, transform 180ms ease;
        }
        .navlinks a:hover { background: var(--leaf); transform: translateY(-1px); }
        .navlinks a:focus-visible,
        .social-rail a:focus-visible,
        .btn-main:focus-visible,
        .btn-soft:focus-visible {
          outline: 3px solid var(--turmeric);
          outline-offset: 3px;
        }
        .nav-cta { background: var(--green) !important; color: var(--cream) !important; }

        /* ── social rail ── */
        .social-rail {
          position: fixed; right: 1rem; top: 35%; z-index: 30;
          display: flex; flex-direction: column; gap: 0.55rem;
        }
        .social-rail a {
          width: 46px; height: 46px; border-radius: 50%;
          display: grid; place-items: center;
          background: var(--paper); border: 1px solid var(--line);
          color: var(--ink) !important; text-decoration: none !important;
          font-size: 0.72rem; font-weight: 900;
          box-shadow: 0 12px 32px rgba(15, 26, 12, 0.12);
          touch-action: manipulation; position: relative;
          transition: background 180ms ease, color 180ms ease, transform 180ms ease;
        }
        .social-rail a:hover { background: var(--green); color: var(--cream) !important; transform: translateX(-2px); }

        /* ── cart rail button — fixed, stacked below social-rail ── */
        .cart-rail {
          position: fixed;
          right: 1rem;
          /* sits below the 4 social rail buttons: top 35% + 4*(46px+0.55rem gap) ≈ + 230px */
          top: calc(35% + 230px);
          z-index: 30;
        }
        .cart-rail a {
          width: 46px; height: 46px; border-radius: 50%;
          display: grid; place-items: center;
          background: var(--olive); border: 2px solid var(--olive);
          color: var(--cream) !important; text-decoration: none !important;
          box-shadow: 0 12px 32px rgba(15, 26, 12, 0.28);
          touch-action: manipulation; position: relative;
          transition: background 180ms ease, transform 180ms ease;
        }
        .cart-rail a:hover { background: var(--green); border-color: var(--green); transform: translateX(-2px); }
        .cart-badge {
          position: absolute;
          top: -4px; right: -4px;
          min-width: 20px; height: 20px;
          background: var(--terracotta);
          color: #fff;
          font-size: .65rem; font-weight: 900;
          border-radius: 999px;
          display: grid; place-items: center;
          line-height: 1; padding: 0 .3rem;
          border: 2px solid var(--paper);
          pointer-events: none;
          animation: pop-in 200ms ease;
        }
        @keyframes pop-in {
          from { transform: scale(0); opacity: 0; }
          to   { transform: scale(1); opacity: 1; }
        }

        .hero {
          position: relative;
          overflow: hidden;
          min-height: 58dvh;
          border-radius: 8px;
          background:
            radial-gradient(circle at 82% 18%, rgba(217,154,34,.28), transparent 34%),
            linear-gradient(135deg, #0F1A0C 0%, #152411 58%, #245C2A 100%);
          background-size: cover;
          background-position: center;
          padding: clamp(1.6rem, 4vw, 3.2rem);
          display: grid;
          grid-template-columns: 1.02fr 0.98fr;
          gap: clamp(1.4rem, 4vw, 4rem);
          align-items: center;
        }
        .hero::after {
          content: "";
          position: absolute;
          left: -6%; bottom: -10%;
          width: 48%; height: 34%;
          background: var(--turmeric);
          transform: rotate(-5deg);
          opacity: .92;
          clip-path: polygon(0 35%, 100% 0, 90% 100%, 0 100%);
        }
        .hero-copy, .hero-visual { position: relative; z-index: 2; }
        .eyebrow {
          display: inline-flex; align-items: center; gap: .45rem;
          color: rgba(255,246,230,.9);
          border: 1px solid rgba(255,246,230,.25);
          background: rgba(255,255,255,.08);
          border-radius: 999px;
          padding: .38rem .9rem;
          font-size: .74rem;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 1.8px;
          margin-bottom: 1.2rem;
        }
        .hero h1 {
          font-family: 'Playfair Display', Georgia, serif;
          font-size: clamp(2.8rem, 7vw, 5.4rem);
          line-height: .94;
          color: var(--cream);
          margin: 0 0 1.1rem;
          letter-spacing: 0;
        }
        .hero p {
          color: rgba(255,246,230,.82);
          font-size: clamp(1rem, 2vw, 1.18rem);
          line-height: 1.7;
          max-width: 39rem;
          margin: 0 0 1.5rem;
        }
        .hero-actions { display: flex; gap: .8rem; flex-wrap: wrap; align-items: center; }
        .btn-main, .btn-soft {
          display: inline-flex; align-items: center; justify-content: center;
          min-height: 3rem;
          padding: .72rem 1.25rem;
          border-radius: 999px;
          text-decoration: none !important;
          font-weight: 900;
          font-size: .92rem;
          touch-action: manipulation;
          transition: transform 180ms ease, background 180ms ease, color 180ms ease;
        }
        .btn-main { background: var(--turmeric); color: var(--olive) !important; }
        .btn-soft { border: 1px solid rgba(255,246,230,.32); color: var(--cream) !important; background: rgba(255,255,255,.08); }
        .btn-main:hover, .btn-soft:hover { transform: translateY(-2px); }
        .hero-card-img {
          background: rgba(255,246,230,.92);
          border: 1px solid rgba(255,246,230,.45);
          border-radius: 8px;
          padding: .7rem;
          box-shadow: 0 30px 80px rgba(0,0,0,.32);
          transform: rotate(2deg);
          max-width: 380px;
          margin-left: auto;
        }
        .hero-card-img img {
          border-radius: 6px;
          display: block;
          width: 100%;
          aspect-ratio: 4 / 4.7;
          object-fit: cover;
        }

        .trust-strip {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          border: 1px solid var(--line);
          border-top: 0;
          background: var(--paper);
          border-radius: 0 0 8px 8px;
          margin-bottom: 1.4rem;
        }
        .trust-item { padding: 1rem; border-right: 1px solid var(--line); }
        .trust-item:last-child { border-right: 0; }
        .trust-item strong { display: block; font-size: .95rem; }
        .trust-item span { display: block; color: var(--muted); font-size: .78rem; margin-top: .15rem; }

        .section-band {
          margin: 1.45rem 0;
          padding: clamp(1.35rem, 3vw, 2.4rem);
          border-radius: 8px;
          background: var(--paper);
          border: 1px solid var(--line);
        }
        .section-band.alt { background: var(--cream-2); }
        .section-head { display: flex; justify-content: space-between; gap: 1rem; align-items: end; margin-bottom: 1.6rem; }
        .section-kicker {
          color: var(--green);
          font-size: .72rem;
          font-weight: 900;
          letter-spacing: 2px;
          text-transform: uppercase;
          margin-bottom: .45rem;
        }
        .section-title {
          font-family: 'Playfair Display', Georgia, serif;
          color: var(--ink);
          font-size: clamp(2.3rem, 5vw, 4.2rem);
          line-height: 1;
          margin: 0;
        }
        .section-copy { color: var(--muted); max-width: 34rem; line-height: 1.65; margin: .7rem 0 0; }

        .product-shell {
          display: grid;
          grid-template-columns: minmax(220px, .62fr) minmax(320px, 1fr);
          gap: clamp(1rem, 3vw, 2rem);
          align-items: center;
          background: var(--paper);
          border: 1px solid var(--line);
          border-radius: 8px;
          padding: clamp(1rem, 2.5vw, 1.6rem);
        }
        .product-photo img {
          border-radius: 8px;
          box-shadow: 0 14px 34px rgba(21,26,18,.14);
          aspect-ratio: 1 / 1;
          object-fit: cover;
          width: 100%;
          max-height: 330px;
        }
        .flavor-tag {
          display: inline-block;
          color: var(--cream);
          border-radius: 999px;
          padding: .38rem .9rem;
          font-size: .7rem;
          font-weight: 900;
          letter-spacing: 2px;
          text-transform: uppercase;
          margin-bottom: .9rem;
        }
        .product-title {
          font-family: 'Playfair Display', Georgia, serif;
          font-size: clamp(2rem, 4vw, 3.15rem);
          line-height: 1;
          margin: 0 0 .55rem;
        }
        .product-sub { color: var(--terracotta); font-weight: 800; font-style: italic; margin-bottom: .75rem; }
        .product-desc { color: var(--muted); line-height: 1.55; margin-bottom: .8rem; }
        .ingredient-pill {
          display: inline-block;
          background: var(--leaf);
          color: var(--green);
          font-weight: 900;
          border-radius: 999px;
          padding: .45rem .8rem;
          font-size: .8rem;
          margin-bottom: 1rem;
        }
        .price { font-family: 'Playfair Display', Georgia, serif; font-weight: 900; font-size: clamp(2.6rem, 6vw, 4.1rem); line-height: .9; }
        .price-note { color: var(--muted); font-size: .82rem; margin-bottom: 1rem; }

        div[data-baseweb="tab-list"] { gap: .55rem; border: 0 !important; margin-bottom: 1.6rem; }
        button[data-baseweb="tab"] {
          border: 1px solid var(--line) !important;
          background: var(--paper) !important;
          border-radius: 999px !important;
          padding: .52rem 1.1rem !important;
          font-weight: 900 !important;
          color: var(--ink) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] { background: var(--olive) !important; color: var(--cream) !important; }
        div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] { display: none !important; }

        [data-testid="stNumberInput"] [data-baseweb="input"],
        [data-testid="stTextInput"] [data-baseweb="input"],
        [data-testid="stTextArea"] [data-baseweb="textarea"] {
          border: 1px solid var(--line) !important;
          border-radius: 8px !important;
          background: #fff !important;
        }
        [data-testid="stNumberInput"] input,
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea { color: var(--ink) !important; background: #fff !important; }
        div[data-testid="stButton"] > button {
          border-radius: 999px;
          border: 1px solid var(--green);
          background: var(--green);
          color: var(--cream);
          min-height: 3rem;
          font-weight: 900;
          touch-action: manipulation;
        }
        div[data-testid="stButton"] > button:hover { background: var(--olive); border-color: var(--olive); color: var(--cream); }
        div[data-testid="stButton"] > button:focus-visible {
          outline: 3px solid var(--turmeric) !important;
          outline-offset: 3px !important;
        }
        div[data-testid="stLinkButton"] > a { border-radius: 999px; font-weight: 900; }

        .editorial-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
        }
        .editorial-card {
          min-height: 190px;
          border-radius: 8px;
          padding: 1.35rem;
          background: var(--cream);
          border: 1px solid var(--line);
          position: relative;
          overflow: hidden;
        }
        .editorial-card::after {
          content: "";
          position: absolute;
          width: 160px; height: 80px;
          right: -32px; bottom: 20px;
          background: var(--turmeric);
          clip-path: polygon(0 20%, 100% 0, 85% 100%, 10% 80%);
          opacity: .75;
        }
        .editorial-card.dark { background: var(--olive); color: var(--cream); border-color: var(--olive); }
        .editorial-card h3 { font-family: 'Playfair Display', Georgia, serif; font-size: 1.7rem; line-height: 1; margin: 0 0 .7rem; position: relative; z-index: 2; }
        .editorial-card p { color: var(--muted); line-height: 1.6; font-size: .92rem; position: relative; z-index: 2; }
        .editorial-card.dark p { color: rgba(255,246,230,.74); }

        .blog-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
        .blog-card {
          background: var(--paper);
          border: 1px solid var(--line);
          border-radius: 8px;
          padding: 1.25rem;
        }
        .blog-card span { color: var(--green); font-size: .7rem; font-weight: 900; letter-spacing: 1.6px; text-transform: uppercase; }
        .blog-card h3 { margin: .5rem 0; font-size: 1.12rem; }
        .blog-card p { color: var(--muted); font-size: .9rem; line-height: 1.55; }
        .blog-card a {
          color: var(--green) !important;
          font-weight: 900;
          text-decoration: none !important;
        }

        .problem-grid,
        .funnel-grid,
        .payment-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1rem;
        }
        .problem-card,
        .funnel-card,
        .payment-card {
          border: 1px solid var(--line);
          border-radius: 8px;
          background: var(--paper);
          padding: 1.25rem;
        }
        .problem-card.problem { border-top: 6px solid var(--terracotta); }
        .problem-card.process { border-top: 6px solid var(--turmeric); }
        .problem-card.solution { border-top: 6px solid var(--green); }
        .problem-card span,
        .funnel-card span {
          display: inline-flex;
          width: 34px;
          height: 34px;
          border-radius: 999px;
          align-items: center;
          justify-content: center;
          background: var(--leaf);
          color: var(--green);
          font-weight: 900;
          margin-bottom: .8rem;
        }
        .problem-card h3,
        .funnel-card h3,
        .payment-card h3 { margin: 0 0 .45rem; }
        .problem-card p,
        .funnel-card p,
        .payment-card p { color: var(--muted); line-height: 1.55; font-size: .92rem; margin: 0; }

        .cart-card, .checkout-card {
          background: var(--paper);
          border: 1px solid var(--line);
          border-radius: 8px;
          padding: 1.1rem;
        }
        .cart-card { position: sticky; top: 92px; }
        .cart-row {
          display: flex;
          justify-content: space-between;
          gap: .8rem;
          border-bottom: 1px solid var(--line);
          padding: .75rem 0;
        }
        .cart-row:last-child { border-bottom: 0; }
        .notice {
          background: var(--leaf);
          color: var(--green);
          border-radius: 8px;
          padding: .85rem 1rem;
          font-weight: 800;
          margin: 1rem 0;
        }
        .payment-card.featured {
          background: var(--olive);
          color: var(--cream);
          border-color: var(--olive);
        }
        .payment-card.featured p { color: rgba(255,246,230,.72); }
        .mock-badge {
          display: inline-block;
          border-radius: 999px;
          background: var(--leaf);
          color: var(--green);
          padding: .28rem .7rem;
          font-size: .72rem;
          font-weight: 900;
          margin-bottom: .7rem;
        }
        .footer {
          margin-top: 3rem;
          background: var(--olive);
          color: var(--cream);
          border-radius: 8px;
          padding: 2rem;
          display: flex;
          justify-content: space-between;
          gap: 1rem;
          flex-wrap: wrap;
        }
        .footer a { color: var(--turmeric) !important; text-decoration: none !important; font-weight: 900; }

        /* ── hero brand intro ── */
        .hero-brand-intro {
          display: flex; align-items: center; gap: .65rem; margin-bottom: 1.5rem;
        }
        .hero-logo-mark {
          width: 46px; height: 46px; border-radius: 50%; flex-shrink: 0;
          background: rgba(255,255,255,.1); border: 1px solid rgba(255,255,255,.2);
          display: grid; place-items: center;
          font-family: 'Playfair Display', Georgia, serif; font-weight: 900;
          font-size: 1.25rem; color: var(--cream);
        }
        .hero-brand-name-text {
          font-weight: 900; font-size: .95rem; color: var(--cream); line-height: 1;
        }
        .hero-brand-sub-text {
          font-size: .73rem; color: rgba(255,246,230,.5); margin-top: .12rem;
        }

        /* ── product-info — flex column, children DON'T stretch full width ── */
        .product-info {
          display: flex; flex-direction: column; align-items: flex-start;
        }
        /* compact product shell */
        .product-shell {
          padding: clamp(.8rem, 2vw, 1.2rem) !important;
          gap: clamp(.75rem, 2vw, 1.5rem) !important;
        }
        .product-photo img {
          max-height: 280px !important;
        }
        .product-title { font-size: clamp(1.6rem, 3vw, 2.4rem) !important; margin-bottom: .3rem !important; }
        .price { font-size: clamp(2rem, 4vw, 3rem) !important; }
        .product-sub { margin-bottom: .45rem !important; }
        .product-desc { margin-bottom: .55rem !important; font-size: .9rem !important; }
        .ingredient-pill { margin-bottom: .65rem !important; padding: .35rem .75rem !important; }
        .price-note { margin-bottom: .5rem !important; }

        /* product tabs — compact spacing */
        div[data-baseweb="tab-list"] { margin-bottom: .85rem !important; }

        /* ── cursor pointer everywhere interactive ── */
        button, [role="button"], a, label[for],
        div[data-testid="stButton"] > button,
        div[data-testid="stLinkButton"] > a,
        button[data-baseweb="tab"],
        div[data-baseweb="tab-list"] button { cursor: pointer !important; }

        /* ── smooth transitions on interactive elements ── */
        a, button { transition: background 180ms ease, color 180ms ease, opacity 180ms ease, transform 180ms ease; }

        /* ── qty input: center number text ── */
        [data-testid="stNumberInput"] input { text-align: center !important; }

        /* ── product controls row below shell ── */
        .product-controls-row {
          display: flex; align-items: center; gap: .65rem; margin-top: .6rem;
        }

        /* ── team section ── */
        .team-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 1.2rem;
        }
        .team-card {
          background: var(--paper);
          border: 1px solid var(--line);
          border-radius: 12px;
          padding: 1.6rem 1.35rem 1.4rem;
          text-align: center;
        }
        .team-avatar {
          width: 56px; height: 56px; border-radius: 50%;
          display: grid; place-items: center; margin: 0 auto 1rem;
          font-family: 'Playfair Display', Georgia, serif;
          font-weight: 900; font-size: 1.3rem; color: var(--cream);
        }
        .team-name {
          font-weight: 900; font-size: 1.05rem; margin: 0 0 .22rem;
          font-family: 'Playfair Display', Georgia, serif;
          color: var(--ink);
        }
        .team-role {
          font-size: .78rem; font-weight: 700; color: var(--green);
          text-transform: uppercase; letter-spacing: 1px; margin-bottom: .85rem;
        }
        .team-skills {
          display: flex; flex-wrap: wrap; gap: .4rem; justify-content: center;
        }
        .team-skill-tag {
          background: var(--leaf); color: var(--green);
          border-radius: 999px; padding: .22rem .65rem;
          font-size: .74rem; font-weight: 700;
        }

        @media (max-width: 900px) {
          [data-testid="stMainBlockContainer"] { padding: .7rem .8rem 3rem !important; }
          .topbar { position: relative; align-items: flex-start; }
          .navlinks { justify-content: flex-start; }
          .hero, .product-shell { grid-template-columns: 1fr; min-height: auto; }
          .trust-strip, .editorial-grid, .blog-grid, .problem-grid, .funnel-grid, .payment-grid { grid-template-columns: 1fr; }
          .trust-item { border-right: 0; border-bottom: 1px solid var(--line); }
          .social-rail { position: static; flex-direction: row; margin: .8rem 0 .5rem; }
          .cart-rail { position: static; margin: 0 0 1rem; }
          .section-head { display: block; }
          .cart-card { position: static; }
          .hero-card-img { margin: 0; max-width: 100%; }
          .product-photo img { max-height: 280px; }
        }

        @media (max-width: 1180px) {
          .social-rail {
            right: .45rem;
            top: auto;
            bottom: .8rem;
            flex-direction: row;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          html { scroll-behavior: auto; }
          *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
          }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )




def render_nav(cart_count: int = 0) -> None:
    badge_html = (
        f'<span class="cart-badge">{cart_count}</span>'
        if cart_count > 0
        else ""
    )
    # Cart icon as CSS background-image (base64 data URI) — SVG inside <a> gets
    # stripped by Streamlit's renderer; using background-image is reliable.
    cart_icon_uri = _cart_btn_uri()
    st.markdown(
        f"""
        <nav class="topbar">
          <div class="brand-lockup notranslate" translate="no">
            <span class="brand-logo">{_logo_svg(44)}</span>
            <div>
              <div class="brand-name notranslate" translate="no">Curcubites</div>
              <div class="brand-sub">Chips de plátano horneadas</div>
            </div>
          </div>
          <div class="navlinks">
            <a href="#inicio">Inicio</a>
            <a href="#productos">Productos</a>
            <a href="#carrito">Carrito</a>
            <a href="#blog">Blog</a>
            <a href="#productos" class="nav-cta">Pedir</a>
          </div>
        </nav>
        <aside class="social-rail notranslate" translate="no" aria-label="Redes sociales y blog">
          <a href="https://www.instagram.com/curcubites_snack/" target="_blank" rel="noopener"
             title="Instagram" aria-label="Instagram de Curcubites" class="notranslate" translate="no">IG</a>
          <a href="https://www.tiktok.com/search?q=curcubites_snack" target="_blank" rel="noopener"
             title="TikTok" aria-label="TikTok de Curcubites" class="notranslate" translate="no">TK</a>
          <a href="#blog" title="Blog" aria-label="Blog Curcubites" class="notranslate" translate="no">BL</a>
          <a href="https://wa.me/573008901210?text=Hola%2C+quiero+pedir+Curcubites" target="_blank" rel="noopener"
             title="WhatsApp" aria-label="Contactar por WhatsApp" class="notranslate" translate="no">WA</a>
        </aside>
        <div class="cart-rail" aria-label="Carrito de compras">
          <a href="#carrito"
             title="Ir al carrito"
             aria-label="Carrito: {cart_count} producto{'s' if cart_count != 1 else ''}"
             style="background-image:url('{cart_icon_uri}');
                    background-size:55%;background-repeat:no-repeat;background-position:center">{badge_html}</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    img1 = BASE_DIR / "imgenes_finales" / "55d95c75-98ae-4418-a4df-c4689f51441c.jpeg"
    img2 = BASE_DIR / "imgenes_finales" / "c0661bdd-e0ce-42bf-93d8-ee2a60dd867c.jpeg"
    img_path = img1 if img1.exists() else img2
    img_uri = image_data_uri(str(img_path)) if img_path.exists() else ""
    img_tag = (
        f'<img src="{img_uri}" alt="Curcubites — chips de plátano horneadas con cúrcuma" loading="eager">'
        if img_uri
        else ""
    )
    st.markdown(
        f"""
        <section id="inicio" class="hero">
          <div class="hero-copy">
            <div class="hero-brand-intro notranslate" translate="no">
              {_logo_svg(56)}
              <div>
                <div class="hero-brand-name-text notranslate" translate="no">Curcubites</div>
                <div class="hero-brand-sub-text">Chips de plátano · Colombia</div>
              </div>
            </div>
            <div class="eyebrow">Horneadas · Sin freír · Con cúrcuma</div>
            <h1>Crujiente<br>real.</h1>
            <p>
              Plátano horneado con cúrcuma y pimienta negra.
              Sin fritura. Sin excusas. El snack que no para de pedir.
            </p>
            <div class="hero-actions">
              <a class="btn-main" href="#productos">Ver sabores</a>
              <a class="btn-soft" href="#productos">Pedir ahora</a>
            </div>
          </div>
          <div class="hero-visual">
            <div class="hero-card-img">{img_tag}</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_trust_strip() -> None:
    st.markdown(
        """
        <div class="trust-strip">
          <div class="trust-item"><strong>Horneadas</strong><span>No fritas.</span></div>
          <div class="trust-item"><strong>Ingredientes claros</strong><span>Plátano, cúrcuma y pimienta.</span></div>
          <div class="trust-item"><strong>Pedido por WhatsApp</strong><span>Confirmamos y coordinamos entrega.</span></div>
          <div class="trust-item"><strong>Marca local</strong><span>Diseñada para Colombia.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_problem_solution() -> None:
    st.markdown(
        """
        <section class="section-band alt">
          <div class="section-head">
            <div>
              <div class="section-kicker">Necesidad · problema · solución</div>
              <h2 class="section-title">Crujiente sin volver a lo de siempre.</h2>
            </div>
            <p class="section-copy">
              La estrategia de marca parte de una tensión simple: queremos algo rico y práctico,
              pero no siempre queremos caer en frituras o snacks sin historia.
            </p>
          </div>
          <div class="problem-grid">
            <article class="problem-card problem">
              <span>1</span>
              <h3>Necesidad</h3>
              <p>Un antojo rápido, fácil de llevar y con buen sabor para la U, oficina, gym o planes al aire libre.</p>
            </article>
            <article class="problem-card process">
              <span>2</span>
              <h3>Problema</h3>
              <p>La mayoría de opciones crujientes se sienten pesadas, grasosas o poco alineadas con un estilo de vida consciente.</p>
            </article>
            <article class="problem-card solution">
              <span>3</span>
              <h3>Solución</h3>
              <p>Curcubites: plátano horneado con cúrcuma y pimienta negra. Crujido real, ingredientes claros y pedido simple.</p>
            </article>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_products(products: list[dict]) -> None:
    st.markdown(
        """
        <div id="productos" style="padding:.5rem 0 .75rem">
          <div class="section-kicker">Nuestros sabores</div>
          <h2 class="section-title" style="margin:.2rem 0 .35rem">Elige el sabor que va contigo.</h2>
          <p style="color:var(--muted);font-size:.94rem;margin:0">
            Original, Picante o Dulce &mdash; 13 g por bolsa, pedido por WhatsApp.
          </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    labels = [p["name"].replace("Curcubites ", "") for p in products]
    tabs = st.tabs(labels)
    for tab, p in zip(tabs, products):
        with tab:
            img_path = BASE_DIR / p["image"]
            img_uri = image_data_uri(str(img_path)) if img_path.exists() else ""
            img_tag = (
                f'<img src="{img_uri}" alt="{p["name"]}" loading="lazy">'
                if img_uri
                else f'<div style="aspect-ratio:1;background:var(--cream-2);border-radius:8px"></div>'
            )
            badge = p.get("badge_color", "#245C2A")
            # Entire product card is pure HTML so CSS grid-template-columns applies
            st.markdown(
                f"""
                <div class="product-shell">
                  <div class="product-photo">{img_tag}</div>
                  <div class="product-info">
                    <span class="flavor-tag" style="background:{badge}">{p['flavor_tag']}</span>
                    <h3 class="product-title">{p['name']}</h3>
                    <div class="product-sub">{p['tagline']}</div>
                    <p class="product-desc">{p['description']}</p>
                    <span class="ingredient-pill">{p['ingredients']}</span>
                    <div class="price">{money(int(p['price']))}</div>
                    <div class="price-note">por bolsa · 13 g · Confirmación por WhatsApp</div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            # Interactive controls BELOW the card (Streamlit widgets can't live inside HTML)
            qty_col, btn_col = st.columns([1, 2.5])
            qty = qty_col.number_input(
                "Unidades",
                min_value=1,
                max_value=24,
                value=1,
                step=1,
                key=f"qty_{p['id']}",
                label_visibility="collapsed",
            )
            if btn_col.button(
                f"Agregar {int(qty)} al carrito — {money(int(p['price']) * int(qty))}",
                key=f"add_{p['id']}",
                use_container_width=True,
            ):
                add_to_cart(p["id"], int(qty))
                st.toast(f"{p['name']} agregado")
                st.rerun()


def render_story() -> None:
    st.markdown(
        """
        <section class="section-band alt" style="text-align:center">
          <div style="max-width:620px;margin:0 auto;padding:1rem 0">
            <div class="section-kicker">Nuestra historia</div>
            <h2 class="section-title" style="margin-bottom:.85rem">
              "Nació de un antojo.<br>Quedó de un hábito."
            </h2>
            <p style="color:var(--muted);font-size:1rem;line-height:1.72">
              Curcubites empezó con una pregunta simple: ¿por qué el snack sabroso tiene que ser
              ultra-procesado? Plátano, cúrcuma y pimienta negra.
              Tres ingredientes reales, un resultado crujiente. Sin fritura, sin excusas.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_brand_story() -> None:
    st.markdown(
        """
        <section id="marca" class="section-band alt">
          <div class="section-head">
            <div>
              <div class="section-kicker">Marca con intención</div>
              <h2 class="section-title">Coherencia de marca, compra simple y contenido que sostiene.</h2>
            </div>
            <p class="section-copy">
              La estrategia cruza las 4C: coherencia en promesa, consistencia visual,
              continuidad de contenidos y complementariedad entre web, Instagram, TikTok y WhatsApp.
            </p>
          </div>
          <div class="editorial-grid">
            <article class="editorial-card dark">
              <h3>Coherencia</h3>
              <p>Misma promesa en web, empaque y redes: plátano horneado con cúrcuma y pimienta negra.</p>
            </article>
            <article class="editorial-card">
              <h3>Consistencia</h3>
              <p>Verde natural, dorado cúrcuma y tono fresco para que la marca se reconozca rápido.</p>
            </article>
            <article class="editorial-card">
              <h3>Complementariedad</h3>
              <p>La web vende, Instagram educa, TikTok atrae y WhatsApp cierra la conversación.</p>
            </article>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_moments() -> None:
    st.markdown(
        """
        <section class="section-band">
          <div class="section-head">
            <div>
              <div class="section-kicker">Momentos Curcubites</div>
              <h2 class="section-title">Para cuando el cuerpo pide crujiente.</h2>
            </div>
            <p class="section-copy">
              Oficina, universidad, post-entreno o plan en casa. Curcubites entra donde antes entraba
              cualquier paquete de fritura, pero con una historia más limpia.
            </p>
          </div>
          <div class="editorial-grid">
            <article class="editorial-card"><h3>Después de entrenar</h3><p>Algo rápido, con sabor y sin sentir que dañaste la rutina.</p></article>
            <article class="editorial-card dark"><h3>Entre reuniones</h3><p>Un snack práctico para tener a la mano sin terminar con grasa en los dedos.</p></article>
            <article class="editorial-card"><h3>Plan de tarde</h3><p>Para compartir, probar sabores y convertir el antojo en conversación.</p></article>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_blog() -> None:
    st.markdown(
        """
        <section id="blog" class="section-band alt">
          <div class="section-head">
            <div>
              <div class="section-kicker">Blog Curcubites</div>
              <h2 class="section-title">Contenido que abre apetito.</h2>
            </div>
            <p class="section-copy">
              Ideas cortas para redes, educación de producto y cultura snack.
              Esto ayuda a que la marca parezca activa, no solo una página de ventas.
            </p>
          </div>
          <div class="blog-grid">
            <article class="blog-card">
              <span>Ingredientes</span>
              <h3>Por qué usamos cúrcuma y pimienta negra</h3>
              <p>Una dupla de sabor intenso, color dorado y personalidad propia en cada mordisco.</p>
              <a href="https://www.instagram.com/curcubites_snack/" target="_blank" rel="noopener">Ver contenido</a>
            </article>
            <article class="blog-card">
              <span>Estilo de vida</span>
              <h3>Snacks para llevar a la U, oficina o gimnasio</h3>
              <p>Pequeños rituales para resolver el antojo sin complicarse la vida.</p>
              <a href="https://www.instagram.com/curcubites_snack/" target="_blank" rel="noopener">Ir a Instagram</a>
            </article>
            <article class="blog-card">
              <span>Marca</span>
              <h3>Cómo se diseñó la identidad de Curcubites</h3>
              <p>Color, empaque y tono pensados para vender desde la primera mirada.</p>
              <a href="#marca">Leer enfoque</a>
            </article>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_checkout(products: list[dict]) -> None:
    items = cart_items(products)
    st.markdown(
        """
        <section id="carrito" class="section-band">
          <div class="section-head">
            <div>
              <div class="section-kicker">Finaliza tu pedido</div>
              <h2 class="section-title">Carrito y entrega.</h2>
            </div>
            <p class="section-copy">
              Sin pago online. Generamos el mensaje y lo confirmas directamente por WhatsApp.
            </p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    cart_col, form_col = st.columns([0.85, 1.15], gap="large")

    # ── CART ──────────────────────────────────────────────────────────────────
    with cart_col:
        st.markdown('<div class="cart-card">', unsafe_allow_html=True)
        st.markdown("#### Tu carrito")
        if not items:
            st.info("Aún no tienes productos. Elige un sabor arriba.")
        else:
            for item in items:
                # Item row: name + subtotal
                st.markdown(
                    f"""
                    <div class="cart-row">
                      <div>
                        <strong>{item['name']}</strong><br>
                        <span style="font-size:.82rem;color:var(--muted)">{money(item['price'])} × {item['qty']}</span>
                      </div>
                      <strong>{money(item['subtotal'])}</strong>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                # Quantity + remove on same row
                q_col, r_col = st.columns([1, 1])
                qty = q_col.number_input(
                    "Unidades",
                    min_value=0,
                    max_value=99,
                    value=int(item["qty"]),
                    step=1,
                    key=f"cart_qty_{item['id']}",
                    label_visibility="collapsed",
                )
                update_quantity(item["id"], int(qty))
                if r_col.button(
                    "✕ Quitar",
                    key=f"remove_{item['id']}",
                    use_container_width=True,
                ):
                    remove_from_cart(item["id"])
                    st.rerun()

            total = cart_total(cart_items(products))
            st.divider()
            st.markdown(
                f"""
                <div style="display:flex;justify-content:space-between;align-items:center;
                            font-size:1.15rem;font-weight:900;padding:.25rem 0">
                  <span>Total</span>
                  <span>{money(total)}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="notice">💬 Confirmas por WhatsApp — sin pago online</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── FORM ──────────────────────────────────────────────────────────────────
    with form_col:
        st.markdown('<div class="checkout-card">', unsafe_allow_html=True)
        st.markdown("#### Datos de entrega")
        if not items:
            st.caption("Agrega productos al carrito para activar el formulario.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        with st.form("checkout_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Nombre completo *")
            phone = c2.text_input("WhatsApp *", placeholder="+57 300 000 0000")
            city = c1.text_input("Ciudad *")
            address = c2.text_input("Dirección *")
            notes = st.text_area(
                "Notas",
                placeholder="Barrio, horario preferido, referencias de entrega…",
            )
            submitted = st.form_submit_button(
                "Preparar pedido →",
                use_container_width=True,
            )

        if submitted:
            missing = [
                label
                for label, value in {
                    "nombre": name,
                    "WhatsApp": phone,
                    "ciudad": city,
                    "dirección": address,
                }.items()
                if not value.strip()
            ]
            if missing:
                st.error("Faltan: " + ", ".join(missing))
            else:
                st.session_state.order_message = order_message(
                    items, name, phone, city, address, notes
                )

        message = st.session_state.get("order_message")
        if message:
            st.success("✓ Pedido listo. Envíalo para confirmar.")
            st.code(message, language="text")
            w_col, m_col = st.columns(2)
            w_col.link_button(
                "📲 Enviar por WhatsApp",
                whatsapp_url(message),
                use_container_width=True,
            )
            m_col.link_button(
                "✉️ Enviar por correo",
                mailto_url(message),
                use_container_width=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def render_team() -> None:
    team = [
        {
            "initials": "SC",
            "name": "Stefannya Cujar",
            "role": "Cofundadora · Marca y Producto",
            "color": "#245C2A",
            "skills": ["Identidad de marca", "Desarrollo de producto", "Estrategia DTC"],
        },
        {
            "initials": "DC",
            "name": "Darlen Certuche",
            "role": "Cofundadora · Operaciones",
            "color": "#C4871A",
            "skills": ["Gestión operativa", "Producción artesanal", "Logística local"],
        },
        {
            "initials": "PR",
            "name": "Paola Rivera",
            "role": "Cofundadora · Marketing",
            "color": "#A85232",
            "skills": ["Redes sociales", "Contenido de marca", "Comunidad y crecimiento"],
        },
    ]
    cards = "".join(
        f"""
        <article class="team-card">
          <div class="team-avatar" style="background:{m['color']}">{m['initials']}</div>
          <p class="team-name">{m['name']}</p>
          <p class="team-role">{m['role']}</p>
          <div class="team-skills">
            {''.join(f'<span class="team-skill-tag">{s}</span>' for s in m['skills'])}
          </div>
        </article>
        """
        for m in team
    )
    st.markdown(
        f"""
        <section class="section-band">
          <div class="section-head">
            <div>
              <div class="section-kicker">El equipo</div>
              <h2 class="section-title">Las personas detrás del crujido.</h2>
            </div>
            <p class="section-copy">
              Un equipo pequeño con roles claros y una convicción común:
              el snack bueno no tiene que ser complicado.
            </p>
          </div>
          <div class="team-grid">{cards}</div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        f"""
        <footer class="footer">
          <div>
            <h3 style="margin:0;font-family:'Playfair Display',Georgia,serif;font-size:2rem">Curcubites</h3>
            <p style="margin:.35rem 0 0;color:rgba(255,246,230,.72)">Chips de plátano horneadas · Colombia</p>
          </div>
          <div>
            <a href="mailto:{DEFAULT_EMAIL}">{DEFAULT_EMAIL}</a><br>
            <span style="color:rgba(255,246,230,.62);font-size:.86rem">Instagram · TikTok · Blog · WhatsApp</span>
          </div>
        </footer>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    ensure_cart()
    inject_styles()
    products = load_products()

    # Cart count from session state (no products lookup needed here)
    cart_count = sum(st.session_state.get("cart", {}).values())

    render_nav(cart_count=cart_count)
    render_hero()
    render_trust_strip()
    render_products(products)
    render_story()
    render_checkout(products)
    render_moments()
    render_blog()
    render_team()
    render_footer()


if __name__ == "__main__":
    main()
