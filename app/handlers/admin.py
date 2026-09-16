from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.db import Database
from app.keyboards import admin_keyboard, home_keyboard

router = Router()


@router.message(Command("claimadmin"))
async def claim_admin(
    message: Message,
    command: CommandObject,
    db: Database,
    settings: Settings,
) -> None:
    if not message.from_user:
        return

    current_admin = db.get_admin_id()
    if current_admin is not None:
        if current_admin == message.from_user.id:
            await message.answer("شما از قبل ادمین ربات هستید.")
        else:
            await message.answer("ادمین ربات از قبل تنظیم شده است.")
        return

    code = (command.args or "").strip()
    if not settings.admin_setup_code or code != settings.admin_setup_code:
        await message.answer("کد فعال‌سازی ادمین صحیح نیست.")
        return

    if db.claim_admin(message.from_user.id):
        await message.answer("✅ دسترسی ادمین با موفقیت فعال شد.\nبرای ورود از /admin استفاده کنید.")
    else:
        await message.answer("ادمین ربات از قبل تنظیم شده است.")


@router.message(Command("admin"))
async def admin_command(message: Message, db: Database) -> None:
    if not message.from_user:
        return
    if db.get_admin_id() != message.from_user.id:
        await message.answer("⛔ شما اجازه دسترسی به پنل مدیریت را ندارید.")
        return
    await message.answer("🛠 <b>پنل مدیریت</b>", reply_markup=admin_keyboard())


@router.callback_query(lambda callback: callback.data == "admin_status")
async def admin_status(callback: CallbackQuery, db: Database) -> None:
    if db.get_admin_id() != callback.from_user.id:
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    await callback.message.edit_text(
        "✅ ربات در حال اجراست.\n"
        "✅ دیتابیس متصل است.\n"
        "✅ دسترسی ادمین فعال است.",
        reply_markup=home_keyboard(),
    )
    await callback.answer()
