import logging
import pytz
import tzlocal
tzlocal.get_localzone = lambda: pytz.timezone('Europe/Moscow') # из за этой хуеты я ебался 2 часа, но теперь все работает (петуту библиотека обновилась)
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, InlineQueryHandler, ContextTypes, filters # АИОГРАМ В СОТНИ РАЗ ЛУЧШЕ ЭТОЙ ХУЙНИ
from uuid import uuid4

# логинг, я его добавил что бы в сообщения ошибки не выводить, но если нужно, можно убрать
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

token = '-' # сюда токен, его получать в боте @BotFather
chanel = '-' # сюда айди канала, его можно получить:
"""
в общем, для анчала зайдите в веб версию тгшки 
зайдите в строку где ссылка, ну сверху тама
пример: https://web.telegram.org/k/#-1543515057
и добавьте -100 перед айди, поулчится:

айди канала: -1001543515057 <-- он всегда отрицательный, и состоит из 13 цифр

так и с группами, супергруппами, людьми и тд можна
"""

groups = [] # сюда айди группы, см вышеm, ВВОДИТЬ ЧЕЕЗ ЗАПЯТУЮ БЕЗ КОВЫЧЕК, минусы важны
pendinl = {} # это словарь, где ключи - токены, а значения - тексты сообщений, НЕ ТРОГАТЬ

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE): # эта функция обрабатывает inline запросы, как бы, очередь запросов
    iq = update.inline_query
    if not iq:
        return
    query = (iq.query or "").strip()

    token = uuid4().hex[:16]
    pendinl[token] = query

    keyboard = [[
        InlineKeyboardButton("отправить", callback_data=f"inline_send_groups:{token}"),
        InlineKeyboardButton("отмена", callback_data=f"inline_cancel:{token}"),
    ]]
    results = [
        InlineQueryResultArticle(
            id="1",
            title="отправить",
            input_message_content=InputTextMessageContent(query),
            description=query[:50] + "...",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
    ]
    try:
        await context.bot.answer_inline_query(iq.id, results=results, cache_time=0, is_personal=True)
    except Exception as e:
        logger.error(e)

async def format_message(update: Update, context: ContextTypes.DEFAULT_TYPE): # эта функция форматирует сообщения, за счет нее сообщения отправляются в канал
    try:
        msg = update.message
        if not msg:
            return
        if msg.via_bot and context.bot and msg.via_bot.id == context.bot.id:
            return
        if msg.chat.type in ['group', 'supergroup']:
            await msg.forward(chanel)
    except Exception as e:
        logger.error(f"ошибка: {str(e)}")


async def inline_channel_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # эта функция обрабатывает inline кнопки, это не главный обработчик inline запросов
    query = update.callback_query
    await query.answer()
    data = query.data or ''
    action, _, token = data.partition(':')
    if action == 'inline_send_groups':
        text = pendinl.pop(token, None)
        if text is None:
            text = (query.message.text if getattr(query, 'message', None) else '') or ''
        sent = 0
        for gid in groups:
            try:
                await context.bot.send_message(chat_id=gid, text=text)
                sent += 1
            except Exception as e:
                logger.error(f"{gid}: ошибка {e}")
        try:
            if getattr(query, 'message', None):
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
            elif query.inline_message_id:
                await context.bot.edit_message_reply_markup(inline_message_id=query.inline_message_id, reply_markup=None)
                await context.bot.edit_message_text(inline_message_id=query.inline_message_id, text='\u200B')
        except Exception:
            try:
                if query.inline_message_id:
                    await context.bot.edit_message_text(inline_message_id=query.inline_message_id, text=(f"групп: {sent}" if sent > 0 else "не отправлено"))
                else:
                    await query.edit_message_text(f"групп: {sent}" if sent > 0 else "не отправлено")
            except Exception:
                pass
    elif action == 'inline_cancel':
        try:
            if getattr(query, 'message', None):
                await context.bot.delete_message(chat_id=query.message.chat_id, message_id=query.message.message_id)
            elif query.inline_message_id:
                await context.bot.edit_message_reply_markup(inline_message_id=query.inline_message_id, reply_markup=None)
                await context.bot.edit_message_text(inline_message_id=query.inline_message_id, text='\u200B')
        except Exception:
            try:
                if query.inline_message_id:
                    await context.bot.edit_message_text(inline_message_id=query.inline_message_id, text='\u200B')
                else:
                    await query.edit_message_text('\u200B')
            except Exception:
                pass


def main(): # это запускает бота, тут все инициализируется
    app = ApplicationBuilder().token(token).job_queue(None).build()
    app.add_handler(CallbackQueryHandler(inline_channel_button, pattern=r'^(inline_send_groups|inline_cancel)(:.+)?$'))
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, format_message))
    app.add_handler(MessageHandler(~filters.COMMAND, format_message))

    app.run_polling(allowed_updates=[
        "message",
        "inline_query",
        "chosen_inline_result",
        "callback_query",
    ])


if __name__ == '__main__': # тут и так понятно
    main()


# Я ВЕСЬ ЭТОТ ПИЗДЕЦ В ОГОНИИ ПИСАЛ БЛЯТЬ, мне блять, даже чат гпт помочь не мог, это пиздец.