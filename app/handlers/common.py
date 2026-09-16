from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
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
            message.from_user.first_name or "کاربر",
        )

    await message.answer(
        text or "👋 به فروشگاه V2Ray خوش آمدید.",
        reply_markup=main_menu(),
    )


@router.message(CommandStart())
async def start_handler(message: Message, db: Database, state: FSMContext) -> None:
    await state.clear()
    await _send_home(message, db)


@router.message(Command("cancel"))
async def cancel_handler(message: Message, db: Database, state: FSMContext) -> None:
    await state.clear()
    await _send_home(message, db, text="عملیات لغو شد و به منوی اصلی برگشتید.")


@router.message(Command("whoami"))
async def whoami_handler(message: Message) -> None:
    if not message.from_user:
        return
    await message.answer(f"شناسه تلگرام شما: <code>{message.from_user.id}</code>")


@router.callback_query(F.data == "home")
async def home_callback(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    await state.clear()
    db.upsert_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name or "کاربر",
    )
    await callback.message.edit_text(
        "🏠 <b>منوی اصلی</b>",
        reply_markup=main_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "services")
async def services_placeholder(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "📦 بخش سرویس‌های من در مرحله بعدی تکمیل می‌شود.",
        reply_markup=home_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "ℹ️ <b>راهنما</b>\n\n"
        "/start - نمایش منوی اصلی\n"
        "/cancel - لغو عملیات در حال انجام\n"
        "/whoami - نمایش شناسه تلگرام\n"
        "/admin - ورود به پنل مدیریت برای ادمین",
        reply_markup=home_keyboard(),
    )
    await callback.answer()
