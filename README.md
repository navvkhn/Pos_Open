# 🍽️ Superscale POS

**Multi-Tenant Restaurant POS built with Streamlit & Supabase**

Superscale POS is a **QR-based, multi-tenant Point of Sale system** designed for cafés and restaurants.
Customers order from their table using QR, kitchen prepares orders on a live screen, reception manages billing & payments, and admins get deep business insights.

---

## 🚀 Key Highlights

* 🏪 **Multi-tenant** (Each restaurant has isolated data)
* 📱 **QR-based ordering** (No app install)
* 🍳 **Live kitchen dashboard** (No login needed)
* 🧾 **Reception / cashier workflow**
* 🧠 **Advanced reports & insights**
* 🎨 **Branding per café** (logo, colors, UPI QR)
* 🔐 **Secure & scalable** using Supabase

---

## 👥 User Roles & Access

### 1️⃣ Customer (No Login)

* Opens menu by scanning QR
* Enters name & mobile
* Adds items to cart
* Gets **loyalty discount automatically**
* Places order
* Pays via UPI QR
* Downloads bill
* Can restart order anytime

---

### 2️⃣ Kitchen (No Login)

* Public kitchen URL per restaurant
* Live auto-refreshing dashboard
* Sees:

  * Order number (tenant-specific)
  * Table number
  * Customer name
  * Pending time (IST)
* Orders shown in **responsive grid**
* Marks orders as **Prepared**
* Shows **only open orders**

Perfect for tablets / TVs.

---

### 3️⃣ Reception / Cashier (Login)

* Sees **only today’s orders**
* Dashboard metrics:

  * Unpaid orders
  * Open orders
  * Prepared orders
  * Today’s revenue
* Can:

  * Add / remove items from an order
  * Add **discount % or amount**
  * Set / edit table number
  * Mark payment as paid
  * Close order
* Closed orders become **read-only**
* Unpaid orders highlighted in 🔴 red
* Mobile & dark-mode friendly UI

---

### 4️⃣ Admin (Login)

Admins manage the entire restaurant setup.

#### 🧾 Products

* Add / edit / delete products
* Category-based menu
* Enable / disable availability

#### ⚙️ Settings

* Upload café logo
* Upload UPI QR code
* Set:

  * Address
  * Contact number
  * Instagram handle
  * Brand colors (primary & accent)
* Branding reflects on:

  * Menu
  * Bill
  * Admin pages
  * Browser tab icon

#### 📊 Reports & Insights

Tenant-safe analytics only.

* Revenue & discount KPIs
* Daily revenue trends
* Orders count per day
* Discount vs non-discount orders
* **Top selling products**
* **Most visited customers**

  * Visits
  * Total spend
  * Avg bill
* CSV export:

  * Orders
  * Product sales

---

## ⭐ Loyalty & Discounts

* Configurable loyalty rules:

  * Example: 5 visits in 7 days → 10% off
* Discount shown **automatically** to customer
* **One discount per customer per day**
* Reception can override discount manually

---

## 🧾 Billing System

* Professional invoice PDF
* Includes:

  * Café logo
  * Brand colors
  * Itemized bill
  * Discount breakdown
  * Total payable
  * Address & contact
  * Instagram handle
* Downloadable by customer
* Generated using **ReportLab**

---

## 🧱 Architecture

### Frontend

* **Streamlit**
* Responsive & dark-mode safe
* Mobile-first for customer & kitchen

### Backend

* **Supabase**

  * PostgreSQL
  * Auth
  * Storage (logos / QR)
  * PostgREST API

### Database Design (Key Tables)

* `tenants`
* `users`
* `products`
* `customers`
* `orders`
* `order_items`
* `loyalty_rules`

All tables are **tenant-isolated** using `tenant_id`.

---

## 🔐 Security & Isolation

* Each restaurant has a unique `tenant_id`
* All queries filtered by `tenant_id`
* No cross-tenant data leakage
* Ready for **Row Level Security (RLS)**

---

## 🔗 Routes & URLs

| Feature        | URL                        |
| -------------- | -------------------------- |
| Customer Menu  | `/?menu=RestaurantName`    |
| Payment Page   | `/?pay=ORDER_ID`           |
| Kitchen Screen | `/?kitchen=RestaurantName` |
| Admin          | Main app (login required)  |

---

## 🛠️ How to Run Locally

```bash
git clone https://github.com/yourusername/superscale-pos.git
cd superscale-pos
pip install -r requirements.txt
streamlit run app.py
```

### Required Secrets (`.streamlit/secrets.toml`)

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your_service_key"
APP_URL = "http://localhost:8501"
```

---

## 🌍 Deployment

* Streamlit Cloud
* Render
* Railway
* Any Docker-compatible platform

---

## 📈 Future Enhancements

* Profit margin (cost price)
* Hourly heatmaps
* Sound alerts for kitchen
* Multi-branch support
* Online payments confirmation
* Staff role permissions

---

## 🧠 Built For

* Cafés
* Restaurants
* Food courts
* Cloud kitchens
* Startups building POS SaaS

---

## ❤️ Powered By

**Superscale POS**
Built with passion using Streamlit & Supabase by Naved Khan❤️

Just say the word 🚀
