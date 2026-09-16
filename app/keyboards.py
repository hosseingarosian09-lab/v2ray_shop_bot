from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🛒 Buy Config", callback_data="buy")],
        [InlineKeyboardButton(text="📦 My Services", callback_data="services")],
        [InlineKeyboardButton(text="ℹ️ Help", callback_data="help")],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛠 Admin Panel", callback_data="admin")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def home_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Home", callback_data="home")]]
    )


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Bot Status", callback_data="admin_status")],
            [InlineKeyboardButton(text="🏠 Home", callback_data="home")],
        ]
    )
