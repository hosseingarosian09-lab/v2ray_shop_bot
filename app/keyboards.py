from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    # ورود به پنل ادمین فقط با دستور /admin انجام می‌شود.
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="buy")],
            [InlineKeyboardButton(text="📦 سرویس‌های من", callback_data="services")],
            [InlineKeyboardButton(text="ℹ️ راهنما", callback_data="help")],
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
            [InlineKeyboardButton(text="✅ وضعیت ربات", callback_data="admin_status")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
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


def plan_details_keyboard(category_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛒 خرید این پلن",
                    callback_data="order_coming_soon",
                )
            ],
            [InlineKeyboardButton(text="⬅️ بازگشت به پلن‌ها", callback_data=f"buycat:{category_id}")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )


def admin_plans_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ افزودن پلن", callback_data="admin_plan_add")],
            [InlineKeyboardButton(text="✏️ مشاهده / ویرایش پلن‌ها", callback_data="admin_plan_edit")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
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
    rows.append([InlineKeyboardButton(text="⬅️ مدیریت پلن‌ها", callback_data="admin_plans")])
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
            [InlineKeyboardButton(text="⬅️ دسته‌بندی‌ها", callback_data="admin_plan_edit")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
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
            [InlineKeyboardButton(text="⬅️ بازگشت به پلن‌ها", callback_data=f"admin_editcat:{category_id}")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )


def cancel_input_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ انصراف", callback_data="admin_plan_cancel")],
            [InlineKeyboardButton(text="🏠 منوی اصلی", callback_data="home")],
        ]
    )
