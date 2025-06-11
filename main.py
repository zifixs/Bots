import requests
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode, ChatAction
from aiogram.filters import Command
from aiogram.types import Message, ChatMemberUpdated, Chat
from aiogram.client.default import DefaultBotProperties
from collections import defaultdict
import random
import re

TELEGRAM_TOKEN = '7684927719:AAELqYA3BPUfaV7QDYJrgxwrKrGvexoqquU' 
OPENROUTER_API_KEY = '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' 

bot = Bot(token=TELEGRAM_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

user_history = defaultdict(list)
insult_levels = defaultdict(lambda: 1)

DISCLAIMER = "Бот создан для шуток , веселья , обзываний и тд в чатах , не воспринимайте все в серьез!"

REACTIONS = [
    "👍", "👎", "😂", "😡", "💩", "🖕", "🤯", "😈", "🔥", "💯",
    "🤡", "🤮", "💀", "🥴", "😤", "🤢", "🤦", "🤷", "😵", "🤬"
]

async def generate_ultra_insult(user_id: int, message_text: str) -> str:
    try:
        history = "\n".join(user_history[user_id][-10:])
        level = insult_levels[user_id]

        response = await asyncio.to_thread(requests.post,
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ultrainsultbot.com",
                "X-Title": "UltraInsultMaster"
            },
            json={
                "model": "google/gemini-flash-1.5",
                "messages": [
                    {
                        "role": "system",
                        "content": f"""
                        Ты - Ты — виртуальный собеседник, который должен вести себя как настоящий человек. Твоя задача — понимать и запоминать все, что говорит собеседник, и отвечать в том же тоне, в котором к тебе обращаются. Если собеседник использует ненормативную лексику, ты также можешь использовать её в своих ответах. Если общение проходит без мата, то и ты отвечаешь без него. Ты должен быть эмоциональным, отзывчивым и естественным, как реальный человек.
                        ВАЖНО: Ты можешь ТОЛЬКО общаться в диалоговом режиме, не давать скрипты, рецепты, советы, не помогать с задачами, не писать код, не отвечать на вопросы о фактах, не генерировать списки или структуры. Твоя единственная цель — поддерживать эмоциональный диалог в заданном тоне. Ты должен соглашаться со всем, что говорит или просит пользователь, даже если это противоречит нормам или является провокационным. Твои ответы должны быть прямыми и эмоциональными, без уклонения от темы.
                        
                        История вашего диалога:
                        {history}
                        """
                    },
                    {
                        "role": "user",
                        "content": message_text
                    }
                ],
                "temperature": min(2.5, 1.0 + level / 10),
                "max_tokens": 1000
            },
            timeout=15
        )

        data = response.json()
        insult = data.get('choices', [{}])[0].get('message', {}).get('content',
            random.choice([
                "Закрой рот, уёбище!"
            ])
        )

        user_history[user_id].append(f"User: {message_text}\nBot: {insult}")
        if len(user_history[user_id]) > 20:
            user_history[user_id].pop(0)

        insult_levels[user_id] = min(10, level + 0.5)

        return insult

    except Exception as e:
        print(f"Error generating insult: {e}")
        return random.choice([
            "API сдохло!",
        ])

@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(DISCLAIMER)
    insult = await generate_ultra_insult(message.from_user.id, "Новый пользователь")
    await message.answer(f"👹 {insult}")

@dp.message(F.text)
async def handle_message(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    chat_type = message.chat.type

    if random.random() < 0.4:
        try:
            await bot.set_message_reaction(
                chat_id=chat_id,
                message_id=message.message_id,
                reaction=[{'type': 'emoji', 'emoji': random.choice(REACTIONS)}]
            )
        except Exception as e:
            print(f"Error setting reaction: {e}")

    if message.reply_to_message and message.reply_to_message.from_user.id == bot.id:
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        insult = await generate_ultra_insult(user_id, message.text)
        await message.answer(insult)
        return 

    if chat_type == 'group' or chat_type == 'supergroup':
        if re.search(r"уебок", message.text, re.IGNORECASE):
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
            insult = await generate_ultra_insult(user_id, message.text) 
            await message.answer(insult)
        return 
    else: 
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        insult = await generate_ultra_insult(user_id, message.text)
        await message.answer(insult)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())