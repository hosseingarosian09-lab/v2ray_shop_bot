from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.db import Database
from app.keyboards import admin_keyboard, home_keyboard, main_menu

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
            await message.answer("You are already the admin.")
        else:
            await message.answer("Admin has already been configured.")
        return

    code = (command.args or "").strip()
    if not settings.admin_setup_code or code != settings.admin_setup_code:
        await message.answer("Invalid setup code.")
        return

    if db.claim_admin(message.from_user.id):
        await message.answer(
            "✅ Admin access claimed successfully.",
            reply_markup=main_menu(True),
        )
    else:
        await message.answer("Admin has already been configured.")


@router.message(Command("admin"))
async def admin_command(message: Message, db: Database) -> None:
    if not message.from_user:
        return
    if db.get_admin_id() != message.from_user.id:
        await message.answer("⛔ You are not authorized to use the admin panel.")
        return
    await message.answer("🛠 Admin Panel", reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin")
async def admin_callback(callback: CallbackQuery, db: Database) -> None:
    if db.get_admin_id() != callback.from_user.id:
        await callback.answer("Unauthorized", show_alert=True)
        return
    await callback.message.edit_text("🛠 Admin Panel", reply_markup=admin_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_status")
async def admin_status(callback: CallbackQuery, db: Database) -> None:
    if db.get_admin_id() != callback.from_user.id:
        await callback.answer("Unauthorized", show_alert=True)
        return
    await callback.message.edit_text(
        "✅ Bot is running.\n✅ Database is connected.\n✅ Admin authorization works.",
        reply_markup=home_keyboard(),
    )
    await callback.answer()
