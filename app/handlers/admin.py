from html import escape

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import Settings
from app.db import Database
from app.keyboards import (
    admin_back_start_keyboard,
    admin_keyboard,
    admin_order_done_keyboard,
    admin_order_review_keyboard,
    admin_orders_keyboard,
)

router = Router()


def _is_admin(db: Database, user_id: int) -> bool:
    return db.get_admin_id() == user_id


def _admin_order_text(order) -> str:
    username = f"@{escape(order['username'])}" if order["username"] else "ندارد"
    return (
        f"🧾 <b>سفارش #{order['id']}</b>\n\n"
        f"👤 کاربر: {escape(order['first_name'])}\n"
        f"🔗 نام کاربری: {username}\n"
        f"🆔 شناسه: <code>{order['user_id']}</code>\n\n"
        f"🗓 مدت: {escape(order['duration_label'])}\n"
        f"📦 حجم: {order['traffic_gb']} گیگابایت\n"
        f"💰 مبلغ: {order['price']:,} تومان\n"
        f"📌 وضعیت: در انتظار بررسی ⏳"
    )


async def _show_admin_root(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    text = "🛠 <b>پنل مدیریت</b>"
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=admin_keyboard())
    else:
        await callback.message.edit_text(text, reply_markup=admin_keyboard())


async def _show_admin_orders(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    await state.clear()
    orders = db.list_pending_review_orders()
    if orders:
        text = "🧾 <b>سفارش‌های در انتظار بررسی</b>\nیک سفارش را انتخاب کنید:"
    else:
        text = "✅ در حال حاضر سفارشی در انتظار بررسی نیست."
    markup = admin_orders_keyboard(orders)
    if callback.message.photo:
        await callback.message.delete()
        await callback.message.answer(text, reply_markup=markup)
    else:
        await callback.message.edit_text(text, reply_markup=markup)


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
async def admin_command(message: Message, db: Database, state: FSMContext) -> None:
    if not message.from_user:
        return
    if not _is_admin(db, message.from_user.id):
        await message.answer("⛔ شما اجازه دسترسی به پنل مدیریت را ندارید.")
        return
    await state.clear()
    await message.answer("🛠 <b>پنل مدیریت</b>", reply_markup=admin_keyboard())


@router.callback_query(F.data == "admin_root")
async def admin_root(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    await _show_admin_root(callback, state)
    await callback.answer()


@router.callback_query(F.data == "admin_status")
async def admin_status(callback: CallbackQuery, db: Database) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    await callback.message.edit_text(
        "✅ ربات در حال اجراست.\n"
        "✅ دیتابیس متصل است.\n"
        "✅ دسترسی ادمین فعال است.",
        reply_markup=admin_back_start_keyboard("admin_root"),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_orders")
async def admin_orders(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    await _show_admin_orders(callback, db, state)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order:"))
async def admin_order_details(callback: CallbackQuery, db: Database) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])
    order = db.get_order_for_admin(order_id)
    if not order:
        await callback.answer("سفارش پیدا نشد.", show_alert=True)
        return
    if order["status"] != "pending_review" or not order["receipt_file_id"]:
        await callback.answer("این سفارش دیگر در انتظار بررسی نیست.", show_alert=True)
        return

    await callback.message.delete()
    await callback.bot.send_photo(
        chat_id=callback.message.chat.id,
        photo=order["receipt_file_id"],
        caption=_admin_order_text(order),
        reply_markup=admin_order_review_keyboard(order_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_approve:"))
async def admin_approve_order(callback: CallbackQuery, db: Database, bot: Bot) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])
    order = db.get_order_for_admin(order_id)
    if not order or order["status"] != "pending_review":
        await callback.answer("این سفارش قبلاً بررسی شده یا معتبر نیست.", show_alert=True)
        return

    service = db.approve_order(order_id)
    if not service:
        await callback.answer("تأیید سفارش انجام نشد.", show_alert=True)
        return

    await callback.message.edit_caption(
        caption=_admin_order_text(order) + "\n\n✅ <b>سفارش تأیید شد و سرویس نمونه ساخته شد.</b>",
        reply_markup=admin_order_done_keyboard(),
    )
    try:
        await bot.send_message(
            order["user_id"],
            "✅ <b>سفارش شما تأیید شد.</b>\n"
            f"سرویس نمونه #{service['id']} ساخته شد.\n"
            "از بخش «📦 سرویس‌های من» می‌توانید اطلاعات آن را ببینید.",
        )
    except TelegramAPIError:
        pass
    await callback.answer("سفارش تأیید شد.")


@router.callback_query(F.data.startswith("admin_order_reject:"))
async def admin_reject_order(callback: CallbackQuery, db: Database, bot: Bot) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return

    order_id = int(callback.data.split(":", 1)[1])
    order = db.get_order_for_admin(order_id)
    if not order or order["status"] != "pending_review":
        await callback.answer("این سفارش قبلاً بررسی شده یا معتبر نیست.", show_alert=True)
        return

    if not db.reject_order(order_id):
        await callback.answer("رد سفارش انجام نشد.", show_alert=True)
        return

    await callback.message.edit_caption(
        caption=_admin_order_text(order) + "\n\n❌ <b>سفارش رد شد.</b>",
        reply_markup=admin_order_done_keyboard(),
    )
    try:
        await bot.send_message(
            order["user_id"],
            "❌ <b>رسید سفارش شما تأیید نشد.</b>\n"
            f"سفارش #{order_id} رد شد. برای خرید می‌توانید یک سفارش جدید ثبت کنید.",
        )
    except TelegramAPIError:
        pass
    await callback.answer("سفارش رد شد.")
