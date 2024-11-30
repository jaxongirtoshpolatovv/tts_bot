# O'zbek Text-to-Speech Telegram Bot

Bu Telegram bot matnli xabarlarni ovozli xabarlarga o'girib beradi. Bot o'zbek tilida ishlaydi.

## O'rnatish

1. Kerakli kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

2. Telegram botni yarating va tokenni oling:
   - [@BotFather](https://t.me/BotFather) ga boring
   - Yangi bot yarating `/newbot` buyrug'i orqali
   - Bot tokenini `bot.py` faylidagi `TOKEN` o'zgaruvchisiga joylang

3. Botni ishga tushiring:
```bash
python bot.py
```

## Ishlatish

1. Botni Telegramda toping
2. `/start` buyrug'ini yuboring
3. Istalgan matnni yuboring
4. Bot matnni ovozli xabar shaklida qaytaradi

## Texnologiyalar

- Python 3.7+
- python-telegram-bot
- gTTS (Google Text-to-Speech)
# tts_bot
