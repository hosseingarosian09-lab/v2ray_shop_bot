from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.db import Database
from app.keyboards import (
    cancel_order_confirm_keyboard,
    cancel_receipt_keyboard,
    home_keyboard,
    order_details_keyboard,
    orders_keyboard,
    payment_keyboard,
    service_details_keyboard,
    services_keyboard,
)

router = Router()

DEMO_CARD_NUMBER = "0000-0000-0000-0000"
DEMO_ACCOUNT_NAME = "فروشگاه نمونه V2Ray"


class ReceiptUpload(StatesGroup):
    waiting_for_photo = State()


def _status_text(status: str) -> str:
    return {
        "pending_payment": "در انتظار پرداخت 💳",
        "pending_review": "در انتظار بررسی رسید ⏳",
        "approved": "تأیید شده ✅",
        "rejected": "رد شده ❌",
        "cancelled": "لغو شده 🚫",
    }.get(status, "نامشخص")


def _order_text(order) -> str:
    return (
        f"🧾 <b>سفارش #{order['id']}</b>\n\n"
        f"🗓 مدت: {order['duration_label']}\n"
        f"📦 حجم: {order['traffic_gb']} گیگابایت\n"
        f"💰 مبلغ: {order['price']:,} تومان\n"
        f"📌 وضعیت: {_status_text(order['status'])}"
    )


def _payment_text(order) -> str:
    return (
        _order_text(order)
        + "\n\n"
        + "💳 <b>اطلاعات پرداخت آزمایشی</b>\n"
        + f"شماره کارت: <code>{DEMO_CARD_NUMBER}</code>\n"
        + f"به نام: {DEMO_ACCOUNT_NAME}\n\n"
        + "این پروژه نمونه است و اطلاعات بالا واقعی نیست.\n"
        + "بعد از پرداخت آزمایشی روی «ارسال رسید» بزنید."
    )


def _service_text(service) -> str:
    status = {
        "active": "فعال ✅",
        "inactive": "غیرفعال ⛔",
        "expired": "منقضی شده ⌛",
    }.get(service["status"], "نامشخص")
    return (
        f"📦 <b>سرویس #{service['id']}</b>\n\n"
        f"🗓 مدت: {escape(service['duration_label'])}\n"
        f"📊 حجم: {service['traffic_gb']} گیگابایت\n"
        f"📌 وضعیت: {status}\n\n"
        f"🔗 <b>Subscription</b>\n<code>{escape(service['subscription_url'])}</code>\n\n"
        f"⚙️ <b>Config نمونه</b>\n<code>{escape(service['config_uri'])}</code>\n\n"
        "⚠️ این سرویس فقط برای نمایش پروژه است و واقعی نیست."
    )


@router.callback_query(F.data.startswith("order_create:"))
async def create_order(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    await state.clear()
    plan_id = int(callback.data.split(":", 1)[1])
    db.upsert_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name or "کاربر",
    )
    try:
        order_id = db.create_order_from_plan(callback.from_user.id, plan_id)
    except ValueError as exc:
        await callback.answer(str(exc), show_alert=True)
        return

    order = db.get_order_for_user(order_id, callback.from_user.id)
    await callback.message.edit_text(
        _payment_text(order),
        reply_markup=payment_keyboard(order_id),
    )
    await callback.answer("سفارش ثبت شد.")


@router.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    await state.clear()
    orders = db.list_orders_for_user(callback.from_user.id)
    if not orders:
        await callback.message.edit_text(
            "🧾 هنوز سفارشی ثبت نکرده‌اید.",
            reply_markup=home_keyboard(),
        )
    else:
        await callback.message.edit_text(
            "🧾 <b>سفارش‌های من</b>\nیک سفارش را انتخاب کنید:",
            reply_markup=orders_keyboard(orders),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("order_view:"))
async def view_order(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    await state.clear()
    order_id = int(callback.data.split(":", 1)[1])
    order = db.get_order_for_user(order_id, callback.from_user.id)
    if not order:
        await callback.answer("سفارش پیدا نشد.", show_alert=True)
        return

    text = _order_text(order)
    if order["status"] == "pending_payment":
        text += "\n\nبرای تکمیل سفارش، پرداخت آزمایشی را انجام دهید و رسید بفرستید."
    elif order["status"] == "pending_review":
        text += "\n\nرسید شما ثبت شده و در انتظار بررسی ادمین است."
    elif order["status"] == "approved":
        text += "\n\nسفارش تأیید شده و سرویس ساخته شده است."
    elif order["status"] == "rejected":
        text += "\n\nرسید این سفارش تأیید نشده است. برای خرید یک سفارش جدید ثبت کنید."
    elif order["status"] == "cancelled":
        text += "\n\nاین سفارش قبل از پرداخت توسط شما لغو شده است."

    await callback.message.edit_text(
        text,
        reply_markup=order_details_keyboard(order_id, order["status"]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_cancel:"))
async def confirm_cancel_order(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    order = db.get_order_for_user(order_id, callback.from_user.id)
    if not order:
        await callback.answer("سفارش پیدا نشد.", show_alert=True)
        return
    if order["status"] != "pending_payment":
        await callback.answer("فقط سفارش پرداخت‌نشده قابل لغو است.", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        _order_text(order) + "\n\n❓ مطمئن هستید که می‌خواهید این سفارش را لغو کنید؟",
        reply_markup=cancel_order_confirm_keyboard(order_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("order_cancel_confirm:"))
async def cancel_order(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    await state.clear()
    if not db.cancel_order(order_id, callback.from_user.id):
        await callback.answer("این سفارش دیگر قابل لغو نیست.", show_alert=True)
        return

    order = db.get_order_for_user(order_id, callback.from_user.id)
    await callback.message.edit_text(
        "✅ سفارش با موفقیت لغو شد.\n\n" + _order_text(order),
        reply_markup=order_details_keyboard(order_id, order["status"]),
    )
    await callback.answer("سفارش لغو شد.")


@router.callback_query(F.data.startswith("order_receipt:"))
async def start_receipt_upload(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    order_id = int(callback.data.split(":", 1)[1])
    order = db.get_order_for_user(order_id, callback.from_user.id)
    if not order:
        await callback.answer("سفارش پیدا نشد.", show_alert=True)
        return
    if order["status"] not in {"pending_payment", "pending_review"}:
        await callback.answer("برای این سفارش امکان ارسال رسید وجود ندارد.", show_alert=True)
        return

    await state.set_state(ReceiptUpload.waiting_for_photo)
    await state.update_data(order_id=order_id)
    await callback.message.edit_text(
        _payment_text(order) + "\n\n📷 تصویر رسید را همین حالا ارسال کنید.",
        reply_markup=cancel_receipt_keyboard(
            order_id,
            can_cancel_order=order["status"] == "pending_payment",
        ),
    )
    await callback.answer()


@router.message(ReceiptUpload.waiting_for_photo, F.photo)
async def save_receipt(message: Message, db: Database, state: FSMContext) -> None:
    if not message.from_user:
        return
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await state.clear()
        await message.answer("سفارش فعال پیدا نشد. از «سفارش‌های من» دوباره وارد شوید.")
        return

    file_id = message.photo[-1].file_id
    saved = db.save_order_receipt(order_id, message.from_user.id, file_id)
    await state.clear()
    if not saved:
        await message.answer(
            "این سفارش دیگر امکان دریافت رسید ندارد.",
            reply_markup=home_keyboard(),
        )
        return

    order = db.get_order_for_user(order_id, message.from_user.id)
    await message.answer(
        "✅ رسید با موفقیت ثبت شد.\n"
        "وضعیت سفارش روی «در انتظار بررسی» قرار گرفت.\n\n"
        + _order_text(order),
        reply_markup=order_details_keyboard(order_id, order["status"]),
    )


@router.message(ReceiptUpload.waiting_for_photo)
async def receipt_requires_photo(message: Message, db: Database, state: FSMContext) -> None:
    if not message.from_user:
        return
    data = await state.get_data()
    order_id = data.get("order_id")
    if not order_id:
        await message.answer("سفارش فعال پیدا نشد.")
        return
    order = db.get_order_for_user(order_id, message.from_user.id)
    await message.answer(
        "لطفاً رسید را به‌صورت <b>عکس</b> ارسال کنید.",
        reply_markup=cancel_receipt_keyboard(
            order_id,
            can_cancel_order=bool(order and order["status"] == "pending_payment"),
        ),
    )


@router.callback_query(F.data == "services")
async def my_services(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    await state.clear()
    services = db.list_services_for_user(callback.from_user.id)
    if not services:
        await callback.message.edit_text(
            "📦 هنوز سرویس فعالی برای شما ساخته نشده است.",
            reply_markup=home_keyboard(),
        )
    else:
        await callback.message.edit_text(
            "📦 <b>سرویس‌های من</b>\nیک سرویس را انتخاب کنید:",
            reply_markup=services_keyboard(services),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("service_view:"))
async def view_service(callback: CallbackQuery, db: Database) -> None:
    service_id = int(callback.data.split(":", 1)[1])
    service = db.get_service_for_user(service_id, callback.from_user.id)
    if not service:
        await callback.answer("سرویس پیدا نشد.", show_alert=True)
        return
    await callback.message.edit_text(
        _service_text(service),
        reply_markup=service_details_keyboard(),
    )
    await callback.answer()
