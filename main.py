import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from datetime import datetime, timedelta
import asyncio

API_TOKEN = "8575675658:AAHzXNMkt1cmRjGrMkz6zwcxHWvcr95Mp94"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()

# ===== Клавіатури =====
keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Перевести байти в МБ та ГБ", callback_data="bytes")],
    [InlineKeyboardButton(text="💳 Тарифна підписка", callback_data="tariff")],
    [InlineKeyboardButton(text="🔻 Розрахувати знижку", callback_data="discount")]
])

# Обычная клавиатура внизу экрана
main_menu_reply_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🏠 Головне меню")]],
    resize_keyboard=True
)

back_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔙 Назад", callback_data="back")]
])

# ===== Состояния =====
waiting_for_bytes = set()
waiting_for_price = set()
waiting_for_discount = {}
waiting_for_tariff_end_date = set()
waiting_for_tariff_packages = set()
tariff_data = {}

# ===== Функция сброса всех состояний =====
def clear_user_states(user_id):
    """Очищает все состояния пользователя"""
    waiting_for_bytes.discard(user_id)
    waiting_for_price.discard(user_id)
    waiting_for_discount.pop(user_id, None)
    waiting_for_tariff_end_date.discard(user_id)
    waiting_for_tariff_packages.discard(user_id)
    tariff_data.pop(user_id, None)

# ===== /start =====
@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Привіт! Чим можу допомогти?",
        reply_markup=keyboard
    )

# ===== /updates =====
@router.message(Command("updates"))
async def updates(message: Message):
    updates_text = """
🔄 <b>Оновлення бота</b>

<b>Версія 2.0</b> (30.01.2026)
• Кнопка "Головне меню" тепер знаходиться внизу екрана
• Виправлено баг зі скиданням пам'яті при переході між функціями
• Додано команду /updates для перегляду оновлень

<b>Версія 1.0</b>
• Конвертація байтів у МБ та ГБ
• Розрахунок тарифної підписки
• Калькулятор знижок
"""
    await message.answer(updates_text, parse_mode="HTML", reply_markup=main_menu_reply_kb)


# ===== Байти =====
@router.callback_query(F.data == "bytes")
async def bytes_callback(call: CallbackQuery):
    user_id = call.from_user.id
    
    # Сброс всех состояний
    clear_user_states(user_id)
    
    waiting_for_bytes.add(user_id)
    await call.message.answer(
        "Введіть кількість байтів:",
        reply_markup=back_kb
    )
    await call.answer()

# ===== Скидка =====
@router.callback_query(F.data == "discount")
async def discount_callback(call: CallbackQuery):
    user_id = call.from_user.id
    
    # Сброс всех состояний
    clear_user_states(user_id)
    
    waiting_for_price.add(user_id)
    await call.message.answer(
        "Введіть ціну у грн:",
        reply_markup=back_kb
    )
    await call.answer()

# ===== Тарифная подписка =====
@router.callback_query(F.data == "tariff")
async def tariff_callback(call: CallbackQuery):
    user_id = call.from_user.id
    
    # Сброс всех состояний
    clear_user_states(user_id)
    
    waiting_for_tariff_end_date.add(user_id)
    await call.message.answer(
        "Введіть дату, до якої оплачено поточний пакет (ДД.ММ.РРРР)\nНаприклад: 30.01.2026",
        reply_markup=back_kb
    )
    await call.answer()

# ===== Головне меню =====
@router.message(F.text == "🏠 Головне меню")
async def go_main_menu(message: Message):
    user_id = message.from_user.id
    
    clear_user_states(user_id)

    await message.answer(
        "🏠 Повернулися в головне меню. Чим можу допомогти?",
        reply_markup=keyboard
    )

# ===== Кнопка "Назад" =====
@router.callback_query(F.data == "back")
async def go_back(call: CallbackQuery):
    user_id = call.from_user.id

    if user_id in waiting_for_tariff_packages:
        waiting_for_tariff_packages.remove(user_id)
        waiting_for_tariff_end_date.add(user_id)
        await call.message.answer(
            "🔙 Повернулися на попередній крок.\nВведіть дату, до якої оплачено поточний пакет (ДД.ММ.РРРР):\nНаприклад: 30.01.2026",
            reply_markup=back_kb
        )
    elif user_id in waiting_for_tariff_end_date:
        # Возвращаемся в главное меню
        clear_user_states(user_id)
        await call.message.answer(
            "🏠 Повернулися в головне меню. Чим можу допомогти?",
            reply_markup=keyboard
        )
    elif user_id in waiting_for_discount:
        waiting_for_discount.pop(user_id)
        waiting_for_price.add(user_id)
        await call.message.answer(
            "🔙 Повернулися на попередній крок.\nВведіть ціну у грн:",
            reply_markup=back_kb
        )
    elif user_id in waiting_for_price:
        # Возвращаемся в главное меню
        clear_user_states(user_id)
        await call.message.answer(
            "🏠 Повернулися в головне меню. Чим можу допомогти?",
            reply_markup=keyboard
        )
    elif user_id in waiting_for_bytes:
        # Возвращаемся в главное меню
        clear_user_states(user_id)
        await call.message.answer(
            "🏠 Повернулися в головне меню. Чим можу допомогти?",
            reply_markup=keyboard
        )

    await call.answer()

# ===== Обработка ввода =====
@router.message()
async def handle_input(message: Message):
    user_id = message.from_user.id
    text = message.text.strip().replace(",", ".")

    # ===== Тариф: дата окончания пакета =====
    if user_id in waiting_for_tariff_end_date:
        try:
            end_date = datetime.strptime(text, "%d.%m.%Y")
        except ValueError:
            await message.answer(
                "❌ Дата введена некорректно.\nВведіть дату у форматі ДД.ММ.РРРР\nНаприклад: 30.01.2026",
                reply_markup=back_kb
            )
            return

        tariff_data[user_id] = {"end_date": end_date}
        waiting_for_tariff_end_date.remove(user_id)

        await message.answer(
            f"✅ Дата закінчення пакета прийнята: {end_date.strftime('%d.%m.%Y')}\n"
            f"Скільки запасних пакетів у вас є?",
            reply_markup=back_kb
        )
        waiting_for_tariff_packages.add(user_id)
        return

    # ===== Тариф: количество пакетов =====
    if user_id in waiting_for_tariff_packages:
        if not text.isdigit():
            await message.answer(
                "❌ Введіть коректну кількість пакетів (ціле число >= 0).",
                reply_markup=back_kb
            )
            return

        packages = int(text)
        tariff_data[user_id]["packages"] = packages
        waiting_for_tariff_packages.remove(user_id)

        end_date = tariff_data[user_id]["end_date"]
        total_days = packages * 28
        final_end_date = end_date + timedelta(days=total_days)

        await message.answer(
            f"✅ Кількість запасних пакетів: {packages}\n"
            f"Поточний пакет дійсний до: {end_date.strftime('%d.%m.%Y')}\n"
            f"Якщо використати всі запасні пакети, дата закінчення стане: {final_end_date.strftime('%d.%m.%Y')}",
            reply_markup=main_menu_reply_kb
        )
        tariff_data.pop(user_id, None)
        return

    # ===== Байты =====
    if user_id in waiting_for_bytes:
        if not text.isdigit():
            await message.answer(
                "❌ Байти введені некоректно. Введіть ціле число.",
                reply_markup=main_menu_reply_kb
            )
            return

        bytes_value = int(text)
        mb = bytes_value / 1024 / 1024
        gb = bytes_value / 1024 / 1024 / 1024

        await message.answer(
            f"✅ Результат:\n📦 Байти: {bytes_value}\n📊 МБ: {mb:.2f}\n💾 ГБ: {gb:.2f}",
            reply_markup=main_menu_reply_kb
        )

        waiting_for_bytes.remove(user_id)
        return

    # ===== Цена =====
    if user_id in waiting_for_price:
        try:
            price = float(text)
            if price <= 0:
                raise ValueError
        except ValueError:
            await message.answer(
                "❌ Ціна введена некоректно. Введіть суму у грн.",
                reply_markup=main_menu_reply_kb
            )
            return

        waiting_for_price.remove(user_id)
        waiting_for_discount[user_id] = price
        await message.answer(
            "Введіть відсоток знижки (0–100):",
            reply_markup=back_kb
        )
        return

    # ===== Процент скидки =====
    if user_id in waiting_for_discount:
        try:
            percent = float(text)
            if percent < 0 or percent > 100:
                raise ValueError
        except ValueError:
            await message.answer(
                "❌ Відсоток знижки введено некорректно (0–100).",
                reply_markup=back_kb
            )
            return

        price = waiting_for_discount.pop(user_id)
        discount_sum = price * percent / 100
        final_price = price - discount_sum

        await message.answer(
            f"💰 Результат:\n"
            f"Ціна: {price:.2f} грн\n"
            f"Знижка: {percent:.2f}%\n"
            f"Економія: {discount_sum:.2f} грн\n"
            f"До оплати: {final_price:.2f} грн",
            reply_markup=main_menu_reply_kb
        )

# ===== Запуск =====
async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())