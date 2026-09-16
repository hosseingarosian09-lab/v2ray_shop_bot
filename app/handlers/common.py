from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db import Database
from app.keyboards import main_menu

router = Router()


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
    await _send_home(message, db, text="عملیات فعلی متوقف شد و به منوی اصلی برگشتید.")


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
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(
            "🏠 <b>منوی اصلی</b>",
            reply_markup=main_menu(),
        )
    else:
        await callback.message.edit_text(
            "🏠 <b>منوی اصلی</b>",
            reply_markup=main_menu(),
        )
    await callback.answer()
