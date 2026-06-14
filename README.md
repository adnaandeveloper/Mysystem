# Telegram Productivity Bot v2 – Auto Timezone

Now with automatic timezone detection.

Features:
- 📥 Backlog, 🎯 Daily, 🔥 Habits, 👑 Admin
- 🌍 Auto timezone: share location → bot updates prompts
- ⏰ Prompts follow you when traveling

## Setup
Same as v1, plus new dependency `timezonefinder`.

Railway env vars:
- TELEGRAM_TOKEN
- ADMIN_ID
- TZ_DEFAULT=Europe/Copenhagen (fallback)

## Auto Timezone
1. /start → tap "📍 Update timezone"
2. Share location once
3. Bot saves e.g. "America/New_York" when you're in US
4. Morning prompt shifts automatically

You can re-share location anytime you travel.
