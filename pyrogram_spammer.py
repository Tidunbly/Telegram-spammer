# Библиотеки нужные для работы скрипта
from pyrogram import Client
from pyrogram.errors import FloodWait
import asyncio
from aiogram import Bot, Dispatcher, executor
from config2 import *
from keyboards_for_spammer import *
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext

# API_ID из https://my.telegram.org/apps
api_id = '23759722'

# API_HASH из https://my.telegram.org/apps
api_hash = 'd6fb8ad6ed58115492961333e1d92906'

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Запуск клиетна. Первый запуск на устройстве потребует ввести номер телефона и код из телеграмма.
client = Client(name='test', api_id=api_id, api_hash=api_hash)

# В эти кавычки вставлять текст для рассылки
text = '.'

# Задержка перед повторной рассылкой в секундах
delay = 360

# Функция отвечающая за рассылку сообщений в доступные чаты/группы/лс

stop = 0
chats = []
chats_names = []
post_text = ''
post_image = ''


class Set(StatesGroup):
    set_delay = State()
    set_post = State()


class Start(StatesGroup):
    posting = State()


@dp.message_handler(commands='start')
async def start_cmd(msg: Message):
    await msg.answer('Привет, ознакомиться с доступными функциями можно ниже.', reply_markup=KeyboardMain())


@dp.callback_query_handler(text='available_chats')
async def chats_btn_handler(call: CallbackQuery):
    global chats
    global chats_names
    chats = []
    chats_names = []
    await call.answer()
    await call.message.answer('Поиск доступных чатов...')
    await client.start()
    async for dialog in client.get_dialogs():
        try:
            if dialog.chat.first_name is not None or dialog.chat.username is not None or dialog.chat.title is not None:
                chats.append(dialog.chat.id)
                chats_names.append(dialog.chat.first_name or dialog.chat.username or dialog.chat.title)
            else:
                continue
        except Exception as e:
            print(e)
        except FloodWait as e:
            await asyncio.sleep(e.value)
    await client.stop()
    chats_for_print = ',\n'.join(chats_names)
    await call.message.answer(f'Доступные чаты: \n{chats_for_print}')


@dp.callback_query_handler(text='delay')
async def delay_btn_handler(call: CallbackQuery):
    await call.answer()
    await call.message.answer(f'Текущий интервал: {delay}', reply_markup=KeyboardDelay())


@dp.callback_query_handler(text='set_delay')
async def set_delay_btn_handler(call: CallbackQuery, state: FSMContext):
    global delay
    await call.answer()
    await call.message.answer('Введите новый интервал в секундах.')
    await state.set_state(Set.set_delay.state)


@dp.message_handler(state=Set.set_delay)
async def set_delay(msg: Message, state: FSMContext):
    global delay
    try:
        delay = int(msg.text)
    except Exception:
        await msg.answer('Неверный формат')
    finally:
        await state.reset_state()


@dp.callback_query_handler(text='post')
async def post_btn_handler(call: CallbackQuery):
    await call.answer()
    try:
        if not post_image:
            await call.message.answer('Текущий пост.', reply_markup=KeyboardPost())
            await call.message.answer(f'{post_text}')
        else:
            await call.message.answer('Текущий пост.', reply_markup=KeyboardPost())
            await call.message.answer_photo(photo=post_image, caption=post_text)
    except Exception:
        await call.answer('Ошибка!')


@dp.callback_query_handler(text='set_post')
async def set_post_btn(call: CallbackQuery, state: FSMContext):
    await call.message.answer('Отправьте пост сообщением.')
    await state.set_state(Set.set_post.state)


@dp.message_handler(state=Set.set_post, content_types=ContentType.ANY)
async def set_post(msg: Message, state: FSMContext):
    global post_text, post_image
    try:
        if not msg.photo:
            post_text = msg.text
        else:
            post_image = msg.photo[0].file_id
            post_text = msg.caption
    except Exception:
        await msg.answer('Не удается скопировать пост!')
        print(msg)
    finally:
        await state.reset_state()


@dp.callback_query_handler(text='start')
async def start_btn_handler(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await state.set_state(Start.posting.state)
    await call.message.answer('Для подтверждения запуска напишите start.')


@dp.message_handler(state=Start.posting.state, text='start')
async def start_posting(msg: Message):
    if not chats:
        await msg.answer('Рассылка запущенна.', reply_markup=KeyboardStop())
        await client.start()
        while stop == 0:
            for chat in chats:
                try:
                    if not post_image:
                        await client.send_message(chat_id=chat, text=post_text)
                    else:
                        await client.send_photo(chat_id=chat, photo=post_image, caption=post_text)
                except Exception as ex:
                    print(ex)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
            await asyncio.sleep(delay)
        await client.stop()
    else:
        await msg.answer('Перед запуском проверьте список доступных чатов.')


@dp.callback_query_handler(text='stop', state=Start.posting.state)
async def stop_btn_handler(call: CallbackQuery, state: FSMContext):
    global stop
    await call.answer()
    stop = 1
    await call.message.answer('Остановка...')
    await state.reset_state()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

