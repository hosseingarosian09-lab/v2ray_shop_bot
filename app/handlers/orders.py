from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.db import Database
from app.keyboards import (
    cancel_receipt_keyboard,
    home_keyboard,
    order_details_keyboard,
    orders_keyboard,
    payment_keyboard,
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
        + "پس از پرداخت آزمایشی، تصویر رسید را برای ربات ارسال کنید."
    )


@router.callback_query(F.data.startswith("order_create:"))
async def create_order(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
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
    await state.set_state(ReceiptUpload.waiting_for_photo)
    await state.update_data(order_id=order_id)
    await callback.message.edit_text(
        _payment_text(order) + "\n\n📷 حالا تصویر رسید را ارسال کنید.",
        reply_markup=cancel_receipt_keyboard(order_id),
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
        text += "\n\nبرای تکمیل سفارش، رسید پرداخت را ارسال کنید."
    elif order["status"] == "pending_review":
        text += "\n\nرسید شما ثبت شده و در انتظار بررسی است."

    await callback.message.edit_text(
        text,
        reply_markup=order_details_keyboard(order_id, order["status"]),
    )
    await callback.answer()


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
        reply_markup=cancel_receipt_keyboard(order_id),
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
async def receipt_requires_photo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    order_id = data.get("order_id")
    await message.answer(
        "لطفاً رسید را به‌صورت <b>عکس</b> ارسال کنید.",
        reply_markup=cancel_receipt_keyboard(order_id) if order_id else None,
    )
