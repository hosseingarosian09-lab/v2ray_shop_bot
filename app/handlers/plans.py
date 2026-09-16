from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from app.db import Database
from app.keyboards import (
    admin_category_picker,
    admin_plan_actions,
    admin_plan_list_keyboard,
    admin_plans_menu,
    cancel_input_keyboard,
    categories_keyboard,
    home_keyboard,
    plan_details_keyboard,
    plans_keyboard,
)

router = Router()


class AddPlan(StatesGroup):
    traffic = State()
    price = State()


class EditPlan(StatesGroup):
    traffic = State()
    price = State()


def _is_admin(db: Database, user_id: int) -> bool:
    return db.get_admin_id() == user_id


def _parse_positive_int(value: str) -> int | None:
    translation = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    cleaned = value.translate(translation).replace(",", "").replace("٬", "").replace(" ", "").strip()
    if not cleaned.isdigit():
        return None
    number = int(cleaned)
    return number if number > 0 else None


def _plan_text(plan) -> str:
    status = "فعال ✅" if plan["is_active"] else "غیرفعال ⛔"
    return (
        f"📦 <b>{plan['traffic_gb']} گیگابایت</b>\n"
        f"🗓 مدت: {plan['category_name']}\n"
        f"💰 قیمت: {plan['price']:,} تومان\n"
        f"وضعیت: {status}"
    )


# ---------- فهرست پلن‌ها برای کاربر ----------


@router.callback_query(F.data == "buy")
async def buy_categories(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    await state.clear()
    categories = db.list_categories(active_only=True, with_active_plans=True)
    if not categories:
        await callback.message.edit_text(
            "در حال حاضر پلنی برای خرید موجود نیست.",
            reply_markup=home_keyboard(),
        )
    else:
        await callback.message.edit_text(
            "🛒 <b>مدت سرویس را انتخاب کنید</b>",
            reply_markup=categories_keyboard(categories),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("buycat:"))
async def buy_plans(callback: CallbackQuery, db: Database) -> None:
    category_id = int(callback.data.split(":", 1)[1])
    category = db.get_category(category_id)
    if not category or not category["is_active"]:
        await callback.answer("این دسته‌بندی در دسترس نیست.", show_alert=True)
        return

    plans = db.list_plans(category_id, active_only=True)
    if not plans:
        await callback.message.edit_text(
            "در این دسته‌بندی پلن فعالی وجود ندارد.",
            reply_markup=categories_keyboard(
                db.list_categories(active_only=True, with_active_plans=True)
            ),
        )
    else:
        await callback.message.edit_text(
            f"🗓 <b>{category['name']}</b>\nحجم موردنظر را انتخاب کنید:",
            reply_markup=plans_keyboard(plans, category_id),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("buyplan:"))
async def plan_details(callback: CallbackQuery, db: Database) -> None:
    plan_id = int(callback.data.split(":", 1)[1])
    plan = db.get_plan(plan_id)
    if not plan or not plan["is_active"] or not plan["category_active"]:
        await callback.answer("این پلن دیگر در دسترس نیست.", show_alert=True)
        return

    await callback.message.edit_text(
        _plan_text(plan),
        reply_markup=plan_details_keyboard(plan["id"], plan["category_id"]),
    )
    await callback.answer()


# ---------- مدیریت پلن‌ها ----------


@router.callback_query(F.data == "admin_plans")
async def admin_plans(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "📋 <b>مدیریت پلن‌ها</b>",
        reply_markup=admin_plans_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin_plan_add")
async def admin_add_choose_category(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    await state.clear()
    categories = db.list_categories(active_only=True)
    await callback.message.edit_text(
        "➕ <b>افزودن پلن</b>\nمدت سرویس را انتخاب کنید:",
        reply_markup=admin_category_picker(categories, "admin_addcat"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_addcat:"))
async def admin_add_category_selected(
    callback: CallbackQuery,
    db: Database,
    state: FSMContext,
) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    category_id = int(callback.data.split(":", 1)[1])
    category = db.get_category(category_id)
    if not category:
        await callback.answer("دسته‌بندی پیدا نشد.", show_alert=True)
        return

    await state.set_state(AddPlan.traffic)
    await state.update_data(category_id=category_id)
    await callback.message.edit_text(
        f"دسته‌بندی: <b>{category['name']}</b>\n\n"
        "حجم پلن را به گیگابایت ارسال کنید.\n"
        "مثال: <code>80</code>",
        reply_markup=cancel_input_keyboard(),
    )
    await callback.answer()


@router.message(AddPlan.traffic)
async def admin_add_traffic(message: Message, db: Database, state: FSMContext) -> None:
    if not message.from_user or not _is_admin(db, message.from_user.id):
        await state.clear()
        return
    traffic = _parse_positive_int(message.text or "")
    if traffic is None:
        await message.answer("لطفاً یک عدد صحیح و بزرگ‌تر از صفر ارسال کنید؛ مثلاً <code>80</code>.")
        return
    await state.update_data(traffic_gb=traffic)
    await state.set_state(AddPlan.price)
    await message.answer(
        "حالا قیمت را به تومان ارسال کنید.\nمثال: <code>350000</code>",
        reply_markup=cancel_input_keyboard(),
    )


@router.message(AddPlan.price)
async def admin_add_price(message: Message, db: Database, state: FSMContext) -> None:
    if not message.from_user or not _is_admin(db, message.from_user.id):
        await state.clear()
        return
    price = _parse_positive_int(message.text or "")
    if price is None:
        await message.answer("لطفاً قیمت را به‌صورت عدد صحیح و بزرگ‌تر از صفر ارسال کنید؛ مثلاً <code>350000</code>.")
        return

    data = await state.get_data()
    try:
        plan_id = db.add_plan(data["category_id"], data["traffic_gb"], price)
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=admin_plans_menu())
        await state.clear()
        return

    plan = db.get_plan(plan_id)
    await state.clear()
    await message.answer(
        "✅ پلن با موفقیت ساخته شد.\n\n" + _plan_text(plan),
        reply_markup=admin_plans_menu(),
    )


@router.callback_query(F.data == "admin_plan_edit")
async def admin_edit_choose_category(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "✏️ <b>مشاهده / ویرایش پلن‌ها</b>\nمدت سرویس را انتخاب کنید:",
        reply_markup=admin_category_picker(db.list_categories(), "admin_editcat"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_editcat:"))
async def admin_edit_category(callback: CallbackQuery, db: Database) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    category_id = int(callback.data.split(":", 1)[1])
    category = db.get_category(category_id)
    if not category:
        await callback.answer("دسته‌بندی پیدا نشد.", show_alert=True)
        return
    plans = db.list_plans(category_id)
    text = f"🗓 <b>{category['name']}</b>\nیک پلن را انتخاب کنید:"
    if not plans:
        text += "\n\nهنوز پلنی در این دسته‌بندی وجود ندارد."
    await callback.message.edit_text(
        text,
        reply_markup=admin_plan_list_keyboard(plans, category_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_plan:"))
async def admin_plan_details(callback: CallbackQuery, db: Database) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    plan_id = int(callback.data.split(":", 1)[1])
    plan = db.get_plan(plan_id)
    if not plan:
        await callback.answer("پلن پیدا نشد.", show_alert=True)
        return
    await callback.message.edit_text(
        _plan_text(plan),
        reply_markup=admin_plan_actions(plan_id, plan["category_id"], bool(plan["is_active"])),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_plan_toggle:"))
async def admin_toggle_plan(callback: CallbackQuery, db: Database) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    plan_id = int(callback.data.split(":", 1)[1])
    new_status = db.toggle_plan(plan_id)
    if new_status is None:
        await callback.answer("پلن پیدا نشد.", show_alert=True)
        return
    plan = db.get_plan(plan_id)
    await callback.message.edit_text(
        _plan_text(plan),
        reply_markup=admin_plan_actions(plan_id, plan["category_id"], bool(plan["is_active"])),
    )
    await callback.answer("پلن فعال شد." if new_status else "پلن غیرفعال شد.")


@router.callback_query(F.data.startswith("admin_plan_traffic:"))
async def admin_change_traffic(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    plan_id = int(callback.data.split(":", 1)[1])
    plan = db.get_plan(plan_id)
    if not plan:
        await callback.answer("پلن پیدا نشد.", show_alert=True)
        return
    await state.set_state(EditPlan.traffic)
    await state.update_data(plan_id=plan_id)
    await callback.message.edit_text(
        f"حجم فعلی: <b>{plan['traffic_gb']} گیگابایت</b>\n"
        "حجم جدید را ارسال کنید:",
        reply_markup=cancel_input_keyboard(),
    )
    await callback.answer()


@router.message(EditPlan.traffic)
async def admin_save_traffic(message: Message, db: Database, state: FSMContext) -> None:
    if not message.from_user or not _is_admin(db, message.from_user.id):
        await state.clear()
        return
    traffic = _parse_positive_int(message.text or "")
    if traffic is None:
        await message.answer("لطفاً یک عدد صحیح و بزرگ‌تر از صفر ارسال کنید.")
        return
    data = await state.get_data()
    try:
        db.update_plan_traffic(data["plan_id"], traffic)
    except ValueError as exc:
        await message.answer(str(exc))
        return
    plan = db.get_plan(data["plan_id"])
    await state.clear()
    await message.answer(
        "✅ حجم پلن به‌روزرسانی شد.\n\n" + _plan_text(plan),
        reply_markup=admin_plan_actions(plan["id"], plan["category_id"], bool(plan["is_active"])),
    )


@router.callback_query(F.data.startswith("admin_plan_price:"))
async def admin_change_price(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    plan_id = int(callback.data.split(":", 1)[1])
    plan = db.get_plan(plan_id)
    if not plan:
        await callback.answer("پلن پیدا نشد.", show_alert=True)
        return
    await state.set_state(EditPlan.price)
    await state.update_data(plan_id=plan_id)
    await callback.message.edit_text(
        f"قیمت فعلی: <b>{plan['price']:,} تومان</b>\n"
        "قیمت جدید را به تومان ارسال کنید:",
        reply_markup=cancel_input_keyboard(),
    )
    await callback.answer()


@router.message(EditPlan.price)
async def admin_save_price(message: Message, db: Database, state: FSMContext) -> None:
    if not message.from_user or not _is_admin(db, message.from_user.id):
        await state.clear()
        return
    price = _parse_positive_int(message.text or "")
    if price is None:
        await message.answer("لطفاً قیمت را به‌صورت عدد صحیح و بزرگ‌تر از صفر ارسال کنید.")
        return
    data = await state.get_data()
    db.update_plan_price(data["plan_id"], price)
    plan = db.get_plan(data["plan_id"])
    await state.clear()
    await message.answer(
        "✅ قیمت پلن به‌روزرسانی شد.\n\n" + _plan_text(plan),
        reply_markup=admin_plan_actions(plan["id"], plan["category_id"], bool(plan["is_active"])),
    )


@router.callback_query(F.data == "admin_plan_cancel")
async def admin_cancel_plan_input(callback: CallbackQuery, db: Database, state: FSMContext) -> None:
    if not _is_admin(db, callback.from_user.id):
        await callback.answer("دسترسی غیرمجاز", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(
        "عملیات لغو شد.\n\n📋 <b>مدیریت پلن‌ها</b>",
        reply_markup=admin_plans_menu(),
    )
    await callback.answer()
