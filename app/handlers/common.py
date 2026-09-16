from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.db import Database
from app.keyboards import home_keyboard, main_menu

router = Router()


def _is_admin(db: Database, user_id: int) -> bool:
    return db.get_admin_id() == user_id


async def _send_home(message: Message, db: Database, *, text: str | None = None) -> None:
    if message.from_user:
        db.upsert_user(
            message.from_user.id,
            message.from_user.username,
            message.from_user.first_name or "User",
        )
        is_admin = _is_admin(db, message.from_user.id)
    else:
        is_admin = False

    await message.answer(
        text or "Welcome to V2Ray Shop Bot 👋\n\nMilestone 1 is running successfully.",
        reply_markup=main_menu(is_admin),
    )


@router.message(CommandStart())
async def start_handler(message: Message, db: Database) -> None:
    await _send_home(message, db)


@router.message(Command("cancel"))
async def cancel_handler(message: Message, db: Database) -> None:
    await _send_home(message, db, text="Cancelled. Back to the main menu.")


@router.message(Command("whoami"))
async def whoami_handler(message: Message) -> None:
    if not message.from_user:
        return
    await message.answer(f"Your Telegram user ID is: <code>{message.from_user.id}</code>")


@router.callback_query(F.data == "home")
async def home_callback(callback: CallbackQuery, db: Database) -> None:
    if not callback.from_user:
        return
    db.upsert_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name or "User",
    )
    await callback.message.edit_text(
        "Main Menu",
        reply_markup=main_menu(_is_admin(db, callback.from_user.id)),
    )
    await callback.answer()


@router.callback_query(F.data == "buy")
async def buy_placeholder(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🛒 Buying plans will be implemented in Milestone 2.",
        reply_markup=home_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "services")
async def services_placeholder(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "📦 User services will be implemented in a later milestone.",
        reply_markup=home_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "ℹ️ Commands\n\n"
        "/start - main menu\n"
        "/cancel - return to main menu\n"
        "/whoami - show your Telegram user ID\n"
        "/claimadmin CODE - claim admin access once",
        reply_markup=home_keyboard(),
    )
    await callback.answer()
