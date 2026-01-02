import flet as ft
import sqlite3
from datetime import datetime

# ==========================================
# 🎨 1. الألوان والتصميم
# ==========================================
BG_COLOR = "#ECEFF1"
CARD_COLOR = "#FFFFFF"
TEXT_COLOR = "#37474F"
ACCENT_COLOR = "#546E7A"
SUCCESS_COLOR = "#66BB6A"
DANGER_COLOR = "#EF5350"
WARNING_COLOR = "#FFA726"

# إصلاح مشكلة الظل والأقواس (تم استخدام كود هيكسا للشفافية)
SHADOW_3D = ft.BoxShadow(
    spread_radius=1,
    blur_radius=15,
    color="#26000000",
    offset=ft.Offset(4, 4)
)

# ==========================================
# 🗄️ 2. قاعدة البيانات
# ==========================================
def init_db():
    conn = sqlite3.connect("shop_v8.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products 
                 (barcode TEXT PRIMARY KEY, name TEXT, price REAL, cost REAL, stock INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS customers 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, phone TEXT, debt REAL DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sales 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, total REAL, profit REAL, type TEXT, customer_id INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT, role TEXT)''')
    
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin', '1234', 'admin')")
    c.execute("INSERT OR IGNORE INTO customers (name, phone, debt) VALUES ('عميل عام', '0000', 0)")
    conn.commit()
    conn.close()

def run_query(query, args=(), fetch=False, fetch_all=False):
    conn = sqlite3.connect("shop_v8.db")
    c = conn.cursor()
    c.execute(query, args)
    res = None
    if fetch: res = c.fetchone()
    if fetch_all: res = c.fetchall()
    conn.commit()
    conn.close()
    return res

# ==========================================
# 📱 3. التطبيق الرئيسي
# ==========================================
def main(page: ft.Page):
    page.title = "Smart Shop V8"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.rtl = True
    page.bgcolor = BG_COLOR
    page.padding = 15
    page.scroll = "auto"

    init_db()

    state = {
        "user": None,
        "cart": [],
        "customers_list": []
    }

    # --- أدوات الواجهة المساعدة ---
    def create_card(content, height=None, bgcolor=CARD_COLOR):
        return ft.Container(
            content=content,
            bgcolor=bgcolor,
            padding=20,
            border_radius=20,
            shadow=SHADOW_3D,
            height=height
        )

    def create_stat_card(title, value, icon, color):
        return ft.Container(
            content=ft.Column([
                ft.Icon(icon, size=40, color="white"),
                ft.Text(title, color="white", size=16),
                ft.Text(value, color="white", size=24, weight="bold")
            ], alignment="center", horizontal_alignment="center"),
            bgcolor=color,
            padding=20,
            border_radius=20,
            shadow=SHADOW_3D,
            width=160, height=140
        )

    def create_input(label, icon, is_password=False, width=None, controller=None):
        return ft.TextField(
            label=label, password=is_password, width=width, icon=icon,
            border_color=ACCENT_COLOR, text_style=ft.TextStyle(color=TEXT_COLOR),
            ref=controller, text_align="right"
        )

    # --- 1. شاشة الدخول ---
    def login_view():
        user_ref = ft.Ref[ft.TextField]()
        pass_ref = ft.Ref[ft.TextField]()

        def login_action(e):
            u = run_query("SELECT * FROM users WHERE username=? AND password=?", 
                          (user_ref.current.value, pass_ref.current.value), fetch=True)
            if u:
                state["user"] = u[0]
                page.clean()
                app_dashboard()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("خطأ في البيانات"))
                page.snack_bar.open = True
                page.update()

        page.add(
            ft.Container(
                content=create_card(
                    ft.Column([
                        ft.Icon(ft.icons.STORE, size=80, color=ACCENT_COLOR),
                        ft.Text("تسجيل الدخول", size=24, weight="bold"),
                        create_input("User", ft.icons.PERSON, controller=user_ref),
                        create_input("Pass", ft.icons.LOCK, True, controller=pass_ref),
                        ft.ElevatedButton("دخول", on_click=login_action, bgcolor=ACCENT_COLOR, color="white", width=200)
                    ], horizontal_alignment="center", spacing=20)
                ),
                alignment=ft.alignment.center, margin=ft.margin.only(top=50)
            )
        )

    # --- 2. لوحة التحكم الرئيسية ---
    def app_dashboard():
        
        # === أ. تبويب الإحصائيات ===
        stat_sales = ft.Text("0.000", size=20, weight="bold", color="white")
        stat_profit = ft.Text("0.000", size=20, weight="bold", color="white")
        stat_debt = ft.Text("0.000", size=20, weight="bold", color="white")
        low_stock_list = ft.ListView(height=150, spacing=5)

        def refresh_stats(e=None):
            # 1. المبيعات والأرباح
            res = run_query("SELECT SUM(total), SUM(profit) FROM sales", fetch=True)
            sales = res[0] if res[0] else 0.0
            profit = res[1] if res[1] else 0.0
            stat_sales.value = f"{sales:.3f} د.ت"
            stat_profit.value = f"{profit:.3f} د.ت"
            
            # 2. الديون
            res_debt = run_query("SELECT SUM(debt) FROM customers", fetch=True)
            debt = res_debt[0] if res_debt[0] else 0.0
            stat_debt.value = f"{debt:.3f} د.ت"

            # 3. نواقص المخزون
            low_stock_list.controls.clear()
            low_items = run_query("SELECT name, stock FROM products WHERE stock < 5", fetch_all=True)
            if low_items:
                for item in low_items:
                    low_stock_list.controls.append(
                        ft.Container(
                            content=ft.Row([ft.Text(item[0]), ft.Text(f"باقي: {item[1]}", color="red", weight="bold")], alignment="spaceBetween"),
                            bgcolor="#FFEBEE", padding=5, border_radius=5
                        )
                    )
            else:
                low_stock_list.controls.append(ft.Text("المخزون ممتاز ✅", color="green"))
            
            page.update()

        dash_content = ft.Column([
            ft.Text("ملخص النشاط", size=22, weight="bold", color=TEXT_COLOR),
            ft.Row([
                create_stat_card("المبيعات", stat_sales.value, ft.icons.MONETIZATION_ON, SUCCESS_COLOR),
                create_stat_card("الأرباح", stat_profit.value, ft.icons.TRENDING_UP, ACCENT_COLOR),
                create_stat_card("الديون", stat_debt.value, ft.icons.MONEY_OFF, DANGER_COLOR),
            ], alignment="center", wrap=True),
            
            ft.Divider(),
            ft.Text("⚠️ تنبيهات المخزون (أقل من 5 قطع)", weight="bold", color=DANGER_COLOR),
            ft.Container(content=low_stock_list, bgcolor="white", height=200, border_radius=10, border=ft.border.all(1, "grey")),
            ft.ElevatedButton("تحديث البيانات 🔄", on_click=refresh_stats, bgcolor=ACCENT_COLOR, color="white")
        ], scroll="auto")

        # ربط التحديث
        dash_content.controls[1].controls[0].content.controls[2] = stat_sales
        dash_content.controls[1].controls[1].content.controls[2] = stat_profit
        dash_content.controls[1].controls[2].content.controls[2] = stat_debt


        # === ب. تبويب نقطة البيع ===
        pos_bar_ref = ft.Ref[ft.TextField]()
        pos_qty_ref = ft.Ref[ft.TextField]()
        cart_list = ft.ListView(spacing=5, height=200)
        total_txt = ft.Text("0.000", size=22, weight="bold", color=ACCENT_COLOR)
        cust_dd = ft.Dropdown(label="العميل", width=200, options=[])

        def update_cart_ui():
            cart_list.controls.clear()
            tot = 0
            for item in state['cart']:
                tot += item['price'] * item['qty']
                cart_list.controls.append(
                    ft.Container(
                        content=ft.Row([ft.Text(item['name']), ft.Text(f"x{item['qty']}"), ft.Text(f"{item['price']*item['qty']:.3f}")], alignment="spaceBetween"),
                        bgcolor=BG_COLOR, padding=5, border_radius=5
                    )
                )
            total_txt.value = f"{tot:.3f} د.ت"
            page.update()

        def add_item_pos(e):
            code = pos_bar_ref.current.value
            p = run_query("SELECT * FROM products WHERE barcode=?", (code,), fetch=True)
            if p:
                if p[4] <= 0:
                    page.snack_bar = ft.SnackBar(ft.Text("❌ نفد المخزون!"), bgcolor="red")
                    page.snack_bar.open = True
                    page.update()
                    return

                try: q = int(pos_qty_ref.current.value)
                except: q = 1
                state['cart'].append({"barcode": p[0], "name": p[1], "price": p[2], "cost": p[3], "qty": q})
                pos_bar_ref.current.value = ""
                pos_bar_ref.current.focus()
                update_cart_ui()
            else:
                page.snack_bar = ft.SnackBar(ft.Text("منتج غير موجود"))
                page.snack_bar.open = True
                page.update()

        def pay_action(pay_type):
            if not state['cart']: return
            tot = sum([i['price']*i['qty'] for i in state['cart']])
            prof = tot - sum([i['cost']*i['qty'] for i in state['cart']])
            cust_id = int(cust_dd.value) if cust_dd.value else 1
            
            run_query("INSERT INTO sales (date, total, profit, type, customer_id) VALUES (?,?,?,?,?)",
                      (datetime.now().strftime("%Y-%m-%d"), tot, prof, pay_type, cust_id))
            
            for item in state['cart']:
                run_query("UPDATE products SET stock = stock - ? WHERE barcode=?", (item['qty'], item['barcode']))

            if pay_type == "كريدي":
                run_query("UPDATE customers SET debt = debt + ? WHERE id=?", (tot, cust_id))

            state['cart'] = []
            update_cart_ui()
            refresh_stats()
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ تم البيع ({pay_type})"), bgcolor="green")
            page.snack_bar.open = True
            page.update()

        pos_content = ft.Column([
            ft.Row([
                ft.Container(
                    content=ft.Row([
                        create_input("باركود", ft.icons.QR_CODE, width=180, controller=pos_bar_ref),
                        ft.IconButton(ft.icons.CAMERA_ALT, bgcolor=ACCENT_COLOR, icon_color="white", on_click=lambda e: pos_bar_ref.current.focus())
                    ])
                ),
                create_input("ع", ft.icons.NUMBERS, width=70, controller=pos_qty_ref),
                ft.IconButton(ft.icons.ADD_CIRCLE, icon_size=40, icon_color=SUCCESS_COLOR, on_click=add_item_pos)
            ]),
            cust_dd,
            ft.Container(content=cart_list, bgcolor="white", height=200, border_radius=10, border=ft.border.all(1, "grey")),
            ft.Row([ft.Text("المجموع:"), total_txt], alignment="spaceBetween"),
            ft.Row([
                ft.ElevatedButton("كاش", on_click=lambda e: pay_action("كاش"), bgcolor=SUCCESS_COLOR, color="white", expand=True),
                ft.ElevatedButton("دين", on_click=lambda e: pay_action("كريدي"), bgcolor=DANGER_COLOR, color="white", expand=True)
            ])
        ])

        # === ج. تبويب المخزون ===
        inv_bar = ft.Ref[ft.TextField]()
        inv_name = ft.Ref[ft.TextField]()
        inv_price = ft.Ref[ft.TextField]()
        inv_cost = ft.Ref[ft.TextField]()
        inv_qty = ft.Ref[ft.TextField]()

        def save_prod(e):
            try:
                run_query("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?)",
                          (inv_bar.current.value, inv_name.current.value, 
                           float(inv_price.current.value), float(inv_cost.current.value), int(inv_qty.current.value)))
                page.snack_bar = ft.SnackBar(ft.Text("✅ تم الحفظ"))
                page.snack_bar.open = True
                inv_bar.current.value = ""; inv_name.current.value = ""; inv_qty.current.value = "10"
                page.update()
            except: pass

        inv_content = ft.Column([
            ft.Text("إدارة المخزون", weight="bold"),
            ft.Row([create_input("باركود", ft.icons.QR_CODE, width=200, controller=inv_bar), ft.IconButton(ft.icons.CAMERA_ALT, bgcolor=ACCENT_COLOR, icon_color="white", on_click=lambda e: inv_bar.current.focus())]),
            create_input("اسم المنتج", ft.icons.LABEL, controller=inv_name),
            ft.Row([create_input("بيع", ft.icons.MONEY, width=130, controller=inv_price), create_input("شراء", ft.icons.MONEY_OFF, width=130, controller=inv_cost)]),
            create_input("الكمية", ft.icons.WAREHOUSE, width=150, controller=inv_qty),
            ft.ElevatedButton("حفظ", on_click=save_prod, bgcolor=ACCENT_COLOR, color="white", width=400)
        ])

        # === د. تبويب العملاء ===
        cust_name = ft.Ref[ft.TextField]()
        cust_phone = ft.Ref[ft.TextField]()
        
        def add_cust(e):
            run_query("INSERT INTO customers (name, phone) VALUES (?,?)", (cust_name.current.value, cust_phone.current.value))
            load_customers()
            page.snack_bar = ft.SnackBar(ft.Text("تمت الإضافة")); page.snack_bar.open = True; page.update()

        def load_customers():
            custs = run_query("SELECT id, name FROM customers", fetch_all=True)
            cust_dd.options = [ft.dropdown.Option(str(c[0]), c[1]) for c in custs]
            cust_dd.value = "1"
            page.update()

        cust_content = ft.Column([
            ft.Text("عميل جديد", weight="bold"),
            ft.Row([create_input("اسم", ft.icons.PERSON, width=150, controller=cust_name), create_input("هاتف", ft.icons.PHONE, width=150, controller=cust_phone)]),
            ft.ElevatedButton("إضافة", on_click=add_cust, bgcolor=ACCENT_COLOR, color="white")
        ])

        # --- تجميع التبويبات ---
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="الرئيسية", icon=ft.icons.DASHBOARD, content=ft.Container(content=dash_content, padding=10, height=600)),
                ft.Tab(text="البيع", icon=ft.icons.POINT_OF_SALE, content=ft.Container(content=pos_content, padding=10, height=600)),
                ft.Tab(text="المخزون", icon=ft.icons.INVENTORY, content=ft.Container(content=inv_content, padding=10, height=600)),
                ft.Tab(text="العملاء", icon=ft.icons.PEOPLE, content=ft.Container(content=cust_content, padding=10, height=600)),
            ],
            expand=False
        )

        load_customers()
        refresh_stats()

        page.add(
            ft.Row([ft.Text("نظام V8.1", size=20, weight="bold"), ft.IconButton(ft.icons.LOGOUT, icon_color=DANGER_COLOR, on_click=lambda e: page.window_close())], alignment="spaceBetween"),
            create_card(tabs, height=750)
        )

    login_view()

ft.app(target=main)
