from aiogram.types import CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="buy")],
            [InlineKeyboardButton(text="🧾 سفارش‌های من", callback_data="my_orders")],
            [InlineKeyboardButton(text="📦 سرویس‌های من", callback_data="services")],
        ]
    )


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")]]
    )


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 مدیریت پلن‌ها", callback_data="admin_plans")],
            [InlineKeyboardButton(text="🧾 سفارش‌های در انتظار بررسی", callback_data="admin_orders")],
            [InlineKeyboardButton(text="✅ وضعیت ربات", callback_data="admin_status")],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root_notice")],
        ]
    )


def admin_back_start_keyboard(back_data: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data=back_data)],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root")],
        ]
    )


def categories_keyboard(categories) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"🗓 {category['name']}",
                callback_data=f"buycat:{category['id']}",
            )
        ]
        for category in categories
    ]
    rows.append([InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def plans_keyboard(plans, category_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"{plan['traffic_gb']} گیگابایت — {plan['price']:,} تومان",
                callback_data=f"buyplan:{plan['id']}",
            )
        ]
        for plan in plans
    ]
    rows.extend(
        [
            [InlineKeyboardButton(text="⬅️ بازگشت به مدت‌ها", callback_data="buy")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def plan_details_keyboard(plan_id: int, category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 خرید این پلن", callback_data=f"order_create:{plan_id}")],
            [InlineKeyboardButton(text="⬅️ بازگشت به پلن‌ها", callback_data=f"buycat:{category_id}")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )


def payment_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📷 ارسال رسید", callback_data=f"order_receipt:{order_id}")],
            [InlineKeyboardButton(text="❌ لغو سفارش", callback_data=f"order_cancel:{order_id}")],
            [InlineKeyboardButton(text="🧾 سفارش‌های من", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )


def cancel_order_confirm_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ بله، سفارش لغو شود", callback_data=f"order_cancel_confirm:{order_id}")],
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data=f"order_view:{order_id}")],
        ]
    )


def after_order_deleted_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="buy")],
            [InlineKeyboardButton(text="🧾 سفارش‌های من", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )


def empty_orders_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="buy")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )


def orders_keyboard(orders) -> InlineKeyboardMarkup:
    status_icons = {
        "pending_payment": "💳",
        "pending_review": "⏳",
        "approved": "✅",
        "rejected": "❌",
    }
    rows = [
        [
            InlineKeyboardButton(
                text=(
                    f"{status_icons.get(order['status'], '🧾')} "
                    f"#{order['id']} — {order['traffic_gb']} گیگ — {order['price']:,} تومان"
                ),
                callback_data=f"order_view:{order['id']}",
            )
        ]
        for order in orders
    ]
    rows.append([InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def order_details_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    rows = []
    if status == "pending_payment":
        rows.append([InlineKeyboardButton(text="📷 ارسال رسید", callback_data=f"order_receipt:{order_id}")])
        rows.append([InlineKeyboardButton(text="❌ لغو سفارش", callback_data=f"order_cancel:{order_id}")])
    elif status == "pending_review":
        rows.append([InlineKeyboardButton(text="🔄 جایگزینی رسید", callback_data=f"order_receipt:{order_id}")])
    rows.extend(
        [
            [InlineKeyboardButton(text="⬅️ سفارش‌های من", callback_data="my_orders")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_receipt_keyboard(order_id: int, *, can_cancel_order: bool) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="⬅️ انصراف از ارسال رسید", callback_data=f"order_view:{order_id}")]]
    if can_cancel_order:
        rows.append([InlineKeyboardButton(text="❌ لغو سفارش", callback_data=f"order_cancel:{order_id}")])
    rows.append([InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def empty_services_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="buy")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )


def services_keyboard(services) -> InlineKeyboardMarkup:
    status_icons = {
        "active": "✅",
        "inactive": "⛔",
        "expired": "⌛",
    }
    rows = [
        [
            InlineKeyboardButton(
                text=(
                    f"{status_icons.get(service['status'], '📦')} "
                    f"سرویس #{service['id']} — {service['traffic_gb']} گیگ — {service['duration_label']}"
                ),
                callback_data=f"service_view:{service['id']}",
            )
        ]
        for service in services
    ]
    rows.append([InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def service_details_keyboard(service) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📋 کپی کانفیگ",
                    copy_text=CopyTextButton(text=service["config_uri"]),
                )
            ],
            [
                InlineKeyboardButton(
                    text="📋 کپی لینک اشتراک",
                    copy_text=CopyTextButton(text=service["subscription_url"]),
                )
            ],
            [InlineKeyboardButton(text="⬅️ سرویس‌های من", callback_data="services")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )


def admin_plans_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ افزودن پلن", callback_data="admin_plan_add")],
            [InlineKeyboardButton(text="✏️ مشاهده / ویرایش پلن‌ها", callback_data="admin_plan_edit")],
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_root")],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root")],
        ]
    )


def admin_category_picker(categories, prefix: str) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"🗓 {category['name']}",
                callback_data=f"{prefix}:{category['id']}",
            )
        ]
        for category in categories
    ]
    rows.extend(
        [
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_plans")],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_plan_list_keyboard(plans, category_id: int) -> InlineKeyboardMarkup:
    rows = []
    for plan in plans:
        status = "✅" if plan["is_active"] else "⛔"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{status} {plan['traffic_gb']} گیگابایت — {plan['price']:,} تومان",
                    callback_data=f"admin_plan:{plan['id']}",
                )
            ]
        )
    rows.extend(
        [
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_plan_edit")],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_plan_actions(plan_id: int, category_id: int, is_active: bool) -> InlineKeyboardMarkup:
    toggle_text = "⛔ غیرفعال کردن" if is_active else "✅ فعال کردن"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 تغییر حجم", callback_data=f"admin_plan_traffic:{plan_id}")],
            [InlineKeyboardButton(text="💰 تغییر قیمت", callback_data=f"admin_plan_price:{plan_id}")],
            [InlineKeyboardButton(text=toggle_text, callback_data=f"admin_plan_toggle:{plan_id}")],
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data=f"admin_editcat:{category_id}")],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root")],
        ]
    )


def cancel_input_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_plan_cancel")],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root")],
        ]
    )


def admin_orders_keyboard(orders) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=f"⏳ #{order['id']} — {order['traffic_gb']} گیگ — {order['price']:,} تومان",
                callback_data=f"admin_order:{order['id']}",
            )
        ]
        for order in orders
    ]
    rows.extend(
        [
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_root")],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root")],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_order_review_keyboard(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ تأیید سفارش", callback_data=f"admin_order_approve:{order_id}")],
            [InlineKeyboardButton(text="❌ رد سفارش", callback_data=f"admin_order_reject:{order_id}")],
            [InlineKeyboardButton(text="⬅️ بازگشت", callback_data="admin_orders")],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root")],
        ]
    )


def admin_order_done_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ بازگشت به سفارش‌ها", callback_data="admin_orders")],
            [InlineKeyboardButton(text="🔄 شروع از اول", callback_data="admin_root")],
        ]
    )
