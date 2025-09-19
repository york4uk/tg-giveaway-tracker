# 🎁 Telegram Giveaway Tracker (UserBot)

Отслеживает розыгрыши во всех чатах, на которые вы подписаны, и присылает уведомления.

## 🚀 Запуск на Railway

1. Получите `API_ID`, `API_HASH` — https://my.telegram.org
2. Узнайте свой `OWNER_ID` — через @userinfobot
3. Авторизуйтесь локально → получите `SESSION_STRING`
4. Добавьте все 5 Secrets в Railway:
   - `API_ID`
   - `API_HASH`
   - `OWNER_ID`
   - `SESSION_NAME`
   - `SESSION_STRING`
5. Задеплойте!

## 💬 Команды управления

- `.add_keyword слово`
- `.remove_keyword слово`
- `.list_keywords`
- `.ignore_chat @username`
- `.unignore_chat -1001234567890`
- `.list_ignored`

Работает 24/7 🚀