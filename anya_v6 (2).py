import requests
import json
import os
from datetime import datetime
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ============================================
TELEGRAM_TOKEN = "8726116885:AAHYP5NJN--INFY9OMZKiZelu9kqC8Yia2A"
GROQ_API_KEY   = "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"
MANAGER_ID     = 7444856111
MANAGER_NAME   = "@vakansijob"
CHANNEL        = "@vacancyjobsmoscow"
# ============================================

VACS_FILE  = "vacancies.json"
CANDS_FILE = "candidates.json"
USERS_FILE = "users.json"

# ====== ФАЙЛЫ ======
def load_vacs():
    return json.load(open(VACS_FILE)) if os.path.exists(VACS_FILE) else {}
def save_vacs(v):
    json.dump(v, open(VACS_FILE,"w"), ensure_ascii=False, indent=2)
def load_cands():
    return json.load(open(CANDS_FILE)) if os.path.exists(CANDS_FILE) else {}
def save_cands(c):
    json.dump(c, open(CANDS_FILE,"w"), ensure_ascii=False, indent=2)
def load_users():
    return json.load(open(USERS_FILE)) if os.path.exists(USERS_FILE) else {}
def save_users(u):
    json.dump(u, open(USERS_FILE,"w"), ensure_ascii=False, indent=2)

def register_user(uid, username, lang="ru"):
    users = load_users()
    if str(uid) not in users:
        users[str(uid)] = {"uid":uid,"username":username,"lang":lang,"date":datetime.now().strftime("%d.%m.%Y %H:%M")}
        save_users(users)

def vac_list_text():
    vacs = load_vacs()
    if not vacs: return "Открытых вакансий нет."
    lines = [f"{i}. {n}: {d.get('info','') if isinstance(d,dict) else d}" for i,(n,d) in enumerate(vacs.items(),1)]
    return "Открытые вакансии:\n"+"\n".join(lines)

def make_system(lang="ru"):
    vacs = vac_list_text()
    users = load_users()
    cands = load_cands()
    questions = []
    for c in list(cands.values())[-50:]:
        questions.extend(c.get("questions",[]))
    top_q = Counter(questions).most_common(5)
    top_str = "\n".join([f"- {q} ({n} раз)" for q,n in top_q]) if top_q else "Пока нет данных"

    base = f"""Ты Аня — добрый тёплый ассистент менеджера Али ({MANAGER_NAME}).

Открытые вакансии:
{vacs}

Статистика (для анализа):
- Всего пользователей бота: {len(users)}
- Всего анкет: {len(cands)}
- Популярные вопросы кандидатов:
{top_str}

ПРАВИЛА:
1. Представляйся ТОЛЬКО один раз при /start
2. Общайся тепло, с улыбкой 😊
3. Показывай только ОТКРЫТЫЕ вакансии
4. Информацию одного кандидата другому НЕ давай
5. Предлагай подписаться на канал {CHANNEL}
6. В конце предлагай: {MANAGER_NAME}
7. Отвечай коротко с эмодзи
8. Документы: паспорт, патент/РВП, СНИЛС, регистрация"""

    langs = {
        "tj": "\n\nМУХИМ: Ба забони ТОҶИКӢ ҷавоб деҳ!",
        "uz": "\n\nМУХИМ: O'ZBEK tilida javob ber!",
        "kz": "\n\nМАЙЫЗДЫ: ҚАЗАҚ тілінде жауап бер!",
    }
    return base + langs.get(lang,"")

def make_manager_system():
    vacs = load_vacs()
    users = load_users()
    cands = load_cands()
    questions = []
    for c in list(cands.values())[-100:]:
        questions.extend(c.get("questions",[]))
    top_q = Counter(questions).most_common(10)
    top_str = "\n".join([f"- {q} ({n} раз)" for q,n in top_q]) if top_q else "Нет данных"
    by_vac = Counter([c.get("anketa",{}).get("vakansiya","?") for c in cands.values()])
    vac_str = "\n".join([f"- {v}: {n} чел." for v,n in by_vac.most_common()])

    return f"""Ты Аня — умный ассистент менеджера Али по найму персонала.

Текущая ситуация:
- Пользователей бота: {len(users)}
- Анкет получено: {len(cands)}
- Открытых вакансий: {len(vacs)}

Анкеты по вакансиям:
{vac_str}

Популярные вопросы кандидатов:
{top_str}

Твои задачи в разговоре с менеджером:
1. Анализируй данные и давай полезные советы
2. Отвечай на вопросы о работе бота и кандидатах
3. Подсказывай что улучшить в вакансиях
4. Говори что чаще всего спрашивают кандидаты
5. Общайся профессионально, коротко, с эмодзи"""

def detect_lang(text):
    t = text.lower()
    # Таджикский — уникальные символы
    tj_chars = set("ӣӯҳғҷ")
    if any(c in t for c in tj_chars): return "tj"
    # Казахский — уникальные символы
    kz_chars = set("әіңүұөһ")
    if any(c in t for c in kz_chars): return "kz"
    # Узбекский — латиница
    uz_latin = ["salom","ishla","maosh","qancha","qachon","qayer","mehnat","bepul","yashash","ish"]
    if any(w in t for w in uz_latin): return "uz"
    # Узбекский — кириллица
    uz_cyr = set("ўқ")
    if any(c in t for c in uz_cyr): return "uz"
    # Таджикский слова
    tj_words = ["салом","маош","кор","ман","шумо","хона","куҷо","чанд","кай","нест","хаст","мекунам","мехохам"]
    if any(w in t for w in tj_words): return "tj"
    # Казахский слова
    kz_words = ["сәлем","жұмыс","жалақы","мен","сіз","қайда","қанша","қашан","бар","жоқ"]
    if any(w in t for w in kz_words): return "kz"
    return "ru"

# ====== СОСТОЯНИЯ ======
S_NONE="none"; S_VAC="vac"; S_FIO="fio"; S_DOB="dob"
S_GR="gr"; S_PHN="phn"; S_TG="tg"; S_WA="wa"
S_MGR_CHAT="mgr_chat"
# Менеджер: добавление вакансии
S_ADD_NAME="add_name"; S_ADD_INFO="add_info"; S_ADD_PHOTO="add_photo"
S_CLOSE_VAC="close_vac"

db = {}
def get_user(uid):
    if uid not in db:
        db[uid] = {"history":[],"state":S_NONE,"anketa":{},"introduced":False,"lang":"ru","mgr_history":[],"questions":[]}
    return db[uid]

def groq_ask(messages, system):
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json={"model":"llama-3.3-70b-versatile","max_tokens":400,
                  "messages":[{"role":"system","content":system}]+messages},
            timeout=30
        )
        return r.json()["choices"][0]["message"]["content"]
    except:
        return f"Ошибка. Напишите: {MANAGER_NAME}"

# ====== КЛАВИАТУРЫ ======
def cand_keyboard(lang="ru"):
    L = {
        "ru":["📋 Вакансии","📝 Анкета","💬 Спросить Аню","📢 Канал"],
        "tj":["📋 Вакансияҳо","📝 Анкета","💬 Аняро пурс","📢 Канал"],
        "uz":["📋 Vakansiyalar","📝 Anketa","💬 Anyadan so'ra","📢 Kanal"],
        "kz":["📋 Вакансиялар","📝 Анкета","💬 Аняға сұра","📢 Арна"],
    }
    l = L.get(lang,L["ru"])
    return ReplyKeyboardMarkup([[KeyboardButton(l[0]),KeyboardButton(l[1])],
                                 [KeyboardButton(l[2]),KeyboardButton(l[3])]],resize_keyboard=True)

def mgr_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("➕ Добавить вакансию"), KeyboardButton("📋 Вакансии")],
        [KeyboardButton("🔒 Закрыть вакансию"),  KeyboardButton("👥 Анкеты")],
        [KeyboardButton("📊 Статистика"),         KeyboardButton("💬 Чат с Аней")],
        [KeyboardButton("📢 Рассылка"),           KeyboardButton("📣 Проверить канал")],
    ],resize_keyboard=True)

def vac_inline(for_publish=False):
    vacs = load_vacs()
    if not vacs: return None
    buttons = []
    for i,name in enumerate(vacs.keys()):
        row = [InlineKeyboardButton(f"✅ {name}", callback_data=f"v{i}")]
        if for_publish:
            row.append(InlineKeyboardButton("📢", callback_data=f"pub{i}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

def get_vac_by_idx(idx):
    keys = list(load_vacs().keys())
    return keys[idx] if idx < len(keys) else None

def anketa_t(lang):
    T = {
        "ru":{"cv":"📋 Выберите вакансию:","fio":"👤 ФИО (Фамилия Имя Отчество):\n_Пример: Андреев Андрей Андреевич_",
              "dob":"📅 Дата рождения (ДД.ММ.ГГГГ):\n_Пример: 15.03.1990_","gr":"🌍 Гражданство (ЗАГЛАВНЫМИ):\n_Пример: ТАДЖИКИСТАН_",
              "phn":"📞 Номер телефона:\n_Пример: +992901234567_","tg":"💬 Telegram (@username или «нет»):",
              "wa":"📱 WhatsApp (номер или «нет»):","done":"✅ Анкета принята! Менеджер Али свяжется с вами 😊"},
        "tj":{"cv":"📋 Вакансия интихоб кунед:","fio":"👤 ФИО нависед:\n_Мисол: Раҳимов Алӣ Баҳромович_",
              "dob":"📅 Санаи таввалуд (РР.ММ.СССС):\n_Мисол: 15.03.1990_","gr":"🌍 Гражданство (КАЛОН ҲАРФ):\n_Мисол: ТОҶИКИСТОН_",
              "phn":"📞 Рақами телефон:\n_Мисол: +992901234567_","tg":"💬 Telegram (@username ё «нет»):",
              "wa":"📱 WhatsApp (рақам ё «нет»):","done":"✅ Анкета қабул шуд! Менеҷер Алӣ тамос мегирад 😊"},
        "uz":{"cv":"📋 Vakansiyani tanlang:","fio":"👤 FIO yozing:\n_Misol: Rahimov Ali Bahodir o'g'li_",
              "dob":"📅 Tug'ilgan sana (KK.OO.YYYY):\n_Misol: 15.03.1990_","gr":"🌍 Fuqarolik (BOSh HARF):\n_Misol: O'ZBEKISTON_",
              "phn":"📞 Telefon raqam:\n_Misol: +998901234567_","tg":"💬 Telegram (@username yoki «yo'q»):",
              "wa":"📱 WhatsApp (raqam yoki «yo'q»):","done":"✅ Anketa qabul qilindi! Menejer Ali bog'lanadi 😊"},
        "kz":{"cv":"📋 Вакансия таңдаңыз:","fio":"👤 АТӘ жазыңыз:\n_Мысал: Рахимов Әлі Бахромұлы_",
              "dob":"📅 Туған күні (КК.АА.ЖЖЖЖ):\n_Мысал: 15.03.1990_","gr":"🌍 Азаматтық (БАС ӘРІП):\n_Мысал: ҚАЗАҚСТАН_",
              "phn":"📞 Телефон нөмірі:\n_Мысал: +77001234567_","tg":"💬 Telegram (@username немесе «жоқ»):",
              "wa":"📱 WhatsApp (нөмір немесе «жоқ»):","done":"✅ Анкета қабылданды! Менеджер Али хабарласады 😊"},
    }
    return T.get(lang,T["ru"])

async def check_subscription(bot, uid):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL, user_id=uid)
        return member.status in ["member","administrator","creator"]
    except:
        return False

async def send_to_manager(app, anketa, uid, username, lang):
    flags = {"ru":"🇷🇺","tj":"🇹🇯","uz":"🇺🇿","kz":"🇰🇿"}
    msg = (
        f"📋 *НОВАЯ АНКЕТА!* {flags.get(lang,'')}\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"🏭 *Вакансия:* {anketa.get('vakansiya','—')}\n"
        f"👤 *ФИО:* {anketa.get('fio','—')}\n"
        f"📅 *Дата рождения:* {anketa.get('dob','—')}\n"
        f"🌍 *Гражданство:* {anketa.get('grazhdanstvo','—')}\n"
        f"📞 *Телефон:* {anketa.get('phone','—')}\n"
        f"💬 *Telegram:* {anketa.get('tg','—')}\n"
        f"📱 *WhatsApp:* {anketa.get('wa','—')}\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"🆔 ID: `{uid}` | @{username or '—'}\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
    )
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Принят", callback_data=f"status_ok_{uid}"),
        InlineKeyboardButton("❌ Отказ", callback_data=f"status_no_{uid}"),
    ]])
    await app.bot.send_message(chat_id=MANAGER_ID, text=msg, parse_mode="Markdown", reply_markup=kb)

async def broadcast_vac(app, vac_name, vac_data):
    users = load_users()
    info = vac_data.get("info","") if isinstance(vac_data,dict) else vac_data
    photo = vac_data.get("photo") if isinstance(vac_data,dict) else None
    sent = 0
    for uid_str, udata in users.items():
        try:
            uid = int(uid_str)
            lang = udata.get("lang","ru")
            captions = {
                "ru": f"🔥 *Новая вакансия!*\n\n🏭 *{vac_name}*\n\n{info}\n\nПодать заявку: /start",
                "tj": f"🔥 *Вакансияи нав!*\n\n🏭 *{vac_name}*\n\n{info}\n\nАнкета: /start",
                "uz": f"🔥 *Yangi vakansiya!*\n\n🏭 *{vac_name}*\n\n{info}\n\nAriza: /start",
                "kz": f"🔥 *Жаңа вакансия!*\n\n🏭 *{vac_name}*\n\n{info}\n\nӨтінім: /start",
            }
            text = captions.get(lang, captions["ru"])
            if photo:
                await app.bot.send_photo(chat_id=uid, photo=photo, caption=text, parse_mode="Markdown")
            else:
                await app.bot.send_message(chat_id=uid, text=text, parse_mode="Markdown")
            sent += 1
        except:
            pass
    return sent

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username
    user = get_user(uid)
    user.update({"history":[],"state":S_NONE,"anketa":{},"introduced":False})

    if uid == MANAGER_ID:
        await update.message.reply_text("👨‍💼 *Панель менеджера Али*\nВыберите действие:",
            parse_mode="Markdown", reply_markup=mgr_keyboard())
        return

    lang = user.get("lang","ru")
    register_user(uid, username, lang)
    user["introduced"] = True

    is_sub = await check_subscription(context.bot, uid)
    sub_note = {
        "ru": f"\n\n📢 Подпишитесь на наш канал: {CHANNEL}" if not is_sub else f"\n\n✅ Вы подписаны на {CHANNEL}",
        "tj": f"\n\n📢 Каналамонро обуна шавед: {CHANNEL}" if not is_sub else f"\n\n✅ Шумо обунаи {CHANNEL} ҳастед",
        "uz": f"\n\n📢 Kanalimizga obuna bo'ling: {CHANNEL}" if not is_sub else f"\n\n✅ Siz {CHANNEL} kanaliga obunasiz",
        "kz": f"\n\n📢 Каналымызға жазылыңыз: {CHANNEL}" if not is_sub else f"\n\n✅ Сіз {CHANNEL} арнасына жазылдыңыз",
    }
    greets = {
        "ru": f"Здравствуйте! 😊\n\nМеня зовут Аня, ассистент менеджера Али.\nПомогу найти подходящую работу!{sub_note['ru']}\n\nВыберите 👇",
        "tj": f"Салом! 😊\n\nМан Аня ҳастам, ёрдамчии менеҷер Алӣ.\nКоре мекунам ки шуморо ёрдам кунам!{sub_note['tj']}\n\nИнтихоб кунед 👇",
        "uz": f"Salom! 😊\n\nMen Anya, menejer Alining yordamchisiman.\nSizga ish topishda yordam beraman!{sub_note['uz']}\n\nTanlang 👇",
        "kz": f"Сәлем! 😊\n\nМен Аня, менеджер Алидің көмекшісімін.\nСізге жұмыс табуға көмектесемін!{sub_note['kz']}\n\nТаңдаңыз 👇",
    }
    await update.message.reply_text(greets.get(lang,greets["ru"]), reply_markup=cand_keyboard(lang))

# ====== CALLBACK ======
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    user = get_user(uid)
    data = query.data

    # Выбор вакансии для анкеты
    if data.startswith("v") and data[1:].isdigit():
        idx = int(data[1:])
        vac_name = get_vac_by_idx(idx)
        if not vac_name:
            await query.edit_message_text("⚠️ Вакансия не найдена.")
            return
        user["anketa"]["vakansiya"] = vac_name
        user["state"] = S_FIO
        lang = user.get("lang","ru")
        t = anketa_t(lang)
        await query.edit_message_text(f"✅ *{vac_name}*\n\n{t['fio']}", parse_mode="Markdown")

    # Публикация вакансии
    elif data.startswith("pub") and data[3:].isdigit():
        if uid != MANAGER_ID: return
        idx = int(data[3:])
        vac_name = get_vac_by_idx(idx)
        vacs = load_vacs()
        if vac_name and vac_name in vacs:
            await query.edit_message_text(f"📢 Рассылка вакансии *{vac_name}*...", parse_mode="Markdown")
            sent = await broadcast_vac(context.application, vac_name, vacs[vac_name])
            await context.bot.send_message(chat_id=MANAGER_ID,
                text=f"✅ Рассылка завершена!\n🏭 Вакансия: *{vac_name}*\n📨 Отправлено: *{sent}* пользователям",
                parse_mode="Markdown", reply_markup=mgr_keyboard())

    # Статус кандидата
    elif data.startswith("status_ok_") or data.startswith("status_no_"):
        if uid != MANAGER_ID: return
        parts = data.split("_")
        status = parts[1]
        cand_uid = parts[2]
        cands = load_cands()
        if cand_uid in cands:
            cands[cand_uid]["status"] = "accepted" if status=="ok" else "rejected"
            save_cands(cands)
        emoji = "✅" if status=="ok" else "❌"
        await query.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(chat_id=MANAGER_ID, text=f"{emoji} Статус обновлён для ID: {cand_uid}")

    # Страницы анкет
    elif data.startswith("pc_"):
        page = int(data[3:])
        await show_cands_page(query, page, edit=True)

    # Фильтр по вакансии
    elif data.startswith("fv_"):
        vac_filter = data[3:]
        await show_cands_filtered(query, vac_filter)

    # Проверка подписки на канал
    elif data == "check_sub":
        uid2 = query.from_user.id
        user2 = get_user(uid2)
        lang2 = user2.get("lang","ru")
        is_sub = await check_subscription(context.bot, uid2)
        if is_sub:
            msgs = {
                "ru": f"✅ Отлично! Вы подписаны на {CHANNEL}!\n\nТеперь будете первыми узнавать о новых вакансиях 🔥",
                "tj": f"✅ Зур! Шумо обунаи {CHANNEL} ҳастед!\n\nВакансияҳои нав аввал ба шумо меояд 🔥",
                "uz": f"✅ Ajoyib! Siz {CHANNEL} ga obunasiz!\n\nYangi vakansiyalar birinchi sizga keladi 🔥",
                "kz": f"✅ Керемет! Сіз {CHANNEL} арнасына жазылдыңыз!\n\nЖаңа вакансиялар бірінші сізге келеді 🔥",
            }
            await query.edit_message_text(msgs.get(lang2, msgs["ru"]))
        else:
            msgs = {
                "ru": f"❌ Вы ещё не подписаны!\n\nПодпишитесь на {CHANNEL} и нажмите снова 👇",
                "tj": f"❌ Шумо ҳанӯз обуна нашудед!\n\nОбуна шавед {CHANNEL} ва дубора босед 👇",
                "uz": f"❌ Siz hali obuna emassiz!\n\n{CHANNEL} ga obuna bo'ling va qayta bosing 👇",
                "kz": f"❌ Сіз әлі жазылмадыңыз!\n\n{CHANNEL} арнасына жазылып, қайта басыңыз 👇",
            }
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Открыть канал", url=f"https://t.me/{CHANNEL.lstrip('@')}"),
                InlineKeyboardButton("✅ Проверить снова", callback_data="check_sub"),
            ]])
            await query.edit_message_text(msgs.get(lang2, msgs["ru"]), reply_markup=kb)

    # Закрыть вакансию
    elif data.startswith("cv_") and data[3:].isdigit():
        if uid != MANAGER_ID: return
        idx = int(data[3:])
        vac_name = get_vac_by_idx(idx)
        vacs = load_vacs()
        if vac_name and vac_name in vacs:
            del vacs[vac_name]; save_vacs(vacs)
            await query.edit_message_text(f"🔒 Вакансия закрыта: *{vac_name}*", parse_mode="Markdown")

async def show_cands_page(q_or_msg, page=0, edit=False):
    cands = load_cands()
    all_list = sorted(cands.values(), key=lambda x: x.get("date",""), reverse=True)
    per_page = 5
    total = len(all_list)
    pages = max(1,(total+per_page-1)//per_page)
    chunk = all_list[page*per_page:(page+1)*per_page]
    flags = {"ru":"🇷🇺","tj":"🇹🇯","uz":"🇺🇿","kz":"🇰🇿"}
    text = f"👥 *Анкеты* (стр.{page+1}/{pages}, всего:{total})\n\n"
    for c in chunk:
        a = c.get("anketa",{})
        f = flags.get(c.get("lang","ru"),"")
        text += (f"🏭 *{a.get('vakansiya','—')}* {f}\n"
                 f"👤 {a.get('fio','—')}\n"
                 f"📞 {a.get('phone','—')} | 💬 {a.get('tg','—')}\n"
                 f"🕐 {c.get('date','—')}\n━━━━━━━\n")
    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️",callback_data=f"pc_{page-1}"))
    if page < pages-1: nav.append(InlineKeyboardButton("➡️",callback_data=f"pc_{page+1}"))
    vacs = load_vacs()
    vac_btns = [[InlineKeyboardButton(f"🔍 {n}",callback_data=f"fv_{n}")] for n in list(vacs.keys())[:4]]
    kb = InlineKeyboardMarkup(([nav] if nav else []) + vac_btns)
    if edit: await q_or_msg.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)
    else: await q_or_msg.reply_text(text, parse_mode="Markdown", reply_markup=kb)

async def show_cands_filtered(query, vac_filter):
    cands = load_cands()
    filtered = sorted([c for c in cands.values() if c.get("anketa",{}).get("vakansiya","")==vac_filter],
                      key=lambda x: x.get("date",""), reverse=True)
    text = f"🏭 *{vac_filter}*\n👥 Кандидатов: *{len(filtered)}*\n\n"
    for c in filtered[:10]:
        a = c.get("anketa",{})
        status = "✅" if c.get("status")=="accepted" else "❌" if c.get("status")=="rejected" else "⏳"
        text += f"{status} {a.get('fio','—')} | {a.get('phone','—')} | {c.get('date','—')}\n"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Все анкеты",callback_data="pc_0")]])
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=kb)

# ====== PHOTO HANDLER ======
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = get_user(uid)

    # Менеджер добавляет фото к вакансии
    if uid == MANAGER_ID:
        caption = update.message.caption or ""
        if caption.startswith("фото "):
            vac_name = caption[5:].strip()
            vacs = load_vacs()
            if vac_name in vacs:
                photo_id = update.message.photo[-1].file_id
                if isinstance(vacs[vac_name],dict): vacs[vac_name]["photo"] = photo_id
                else: vacs[vac_name] = {"info":vacs[vac_name],"photo":photo_id}
                save_vacs(vacs)
                await update.message.reply_text(f"✅ Фото добавлено: *{vac_name}*\n\nПубликовать всем?",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("📢 Разослать всем", callback_data=f"pub{list(vacs.keys()).index(vac_name)}")
                    ]]))
            else:
                await update.message.reply_text(f"⚠️ Вакансия не найдена: {vac_name}")
        elif user.get("state") == S_ADD_PHOTO:
            # Фото при добавлении новой вакансии
            photo_id = update.message.photo[-1].file_id
            vac_name = user.get("new_vac_name","")
            vacs = load_vacs()
            if vac_name in vacs:
                vacs[vac_name]["photo"] = photo_id
                save_vacs(vacs)
            user["state"] = S_NONE
            vacs2 = load_vacs()
            await update.message.reply_text(
                f"✅ Вакансия создана с фото!\n\n*{vac_name}*\n\nПубликовать всем пользователям?",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("📢 Разослать всем",callback_data=f"pub{list(vacs2.keys()).index(vac_name)}"),
                    InlineKeyboardButton("⏭ Пропустить",callback_data="skip_pub")
                ]]))
        return

# ====== ГЛАВНЫЙ ОБРАБОТЧИК ======
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()
    user = get_user(uid)
    state = user.get("state", S_NONE)
    detected = detect_lang(text)
    if detected != "ru": user["lang"] = detected
    lang = user.get("lang","ru")

    # ========== МЕНЕДЖЕР ==========
    if uid == MANAGER_ID:
        if state == S_ADD_NAME:
            user["new_vac_name"] = text
            user["state"] = S_ADD_INFO
            await update.message.reply_text(f"✅ Название: *{text}*\n\n📝 Теперь напишите условия вакансии:", parse_mode="Markdown")
            return

        if state == S_ADD_INFO:
            vac_name = user.get("new_vac_name","")
            vacs = load_vacs()
            vacs[vac_name] = {"info": text, "photo": None}
            save_vacs(vacs)
            user["state"] = S_ADD_PHOTO
            await update.message.reply_text(
                f"✅ Условия сохранены!\n\n📸 Отправьте фото вакансии или нажмите кнопку:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⏭ Без фото",callback_data=f"pub{list(vacs.keys()).index(vac_name)}_confirm"),
                    InlineKeyboardButton("📢 Разослать сейчас",callback_data=f"pub{list(vacs.keys()).index(vac_name)}"),
                ]]))
            user["new_vac_name"] = vac_name
            return

        if state == S_MGR_CHAT:
            history = user.get("mgr_history",[])
            history.append({"role":"user","content":text})
            if len(history)>20: history=history[-20:]
            await context.bot.send_chat_action(update.effective_chat.id,"typing")
            reply = groq_ask(history, make_manager_system())
            history.append({"role":"assistant","content":reply})
            user["mgr_history"] = history
            await update.message.reply_text(reply, reply_markup=mgr_keyboard())
            return

        # Кнопки менеджера
        if text == "➕ Добавить вакансию":
            user["state"] = S_ADD_NAME
            await update.message.reply_text("📝 Напишите *название* вакансии:", parse_mode="Markdown")
        elif text == "📋 Вакансии":
            vacs = load_vacs()
            if not vacs:
                await update.message.reply_text("Вакансий нет. Добавьте: ➕ Добавить вакансию")
                return
            text_out = "📋 *Открытые вакансии:*\n\n"
            for n,d in vacs.items():
                info = d.get("info","") if isinstance(d,dict) else d
                has_photo = "📸" if isinstance(d,dict) and d.get("photo") else ""
                text_out += f"✅ {has_photo} *{n}*\n_{info}_\n\n"
            buttons = [[InlineKeyboardButton(f"📢 Разослать: {n}",callback_data=f"pub{i}"),
                        InlineKeyboardButton(f"🔒 Закрыть",callback_data=f"cv_{i}")] for i,n in enumerate(vacs.keys())]
            await update.message.reply_text(text_out, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        elif text == "🔒 Закрыть вакансию":
            vacs = load_vacs()
            if not vacs:
                await update.message.reply_text("Нет открытых вакансий.")
                return
            buttons = [[InlineKeyboardButton(f"🔒 {n}",callback_data=f"cv_{i}")] for i,n in enumerate(vacs.keys())]
            await update.message.reply_text("Выберите вакансию для закрытия:", reply_markup=InlineKeyboardMarkup(buttons))
        elif text == "👥 Анкеты":
            await show_cands_page(update.message, page=0, edit=False)
        elif text == "📊 Статистика":
            cands = load_cands()
            users = load_users()
            by_vac = Counter([c.get("anketa",{}).get("vakansiya","?") for c in cands.values()])
            by_month = Counter([c.get("date","")[:7] for c in cands.values() if c.get("date","")])
            by_lang = Counter([c.get("lang","ru") for c in cands.values()])
            flags = {"ru":"🇷🇺","tj":"🇹🇯","uz":"🇺🇿","kz":"🇰🇿"}
            txt = (f"📊 *Статистика*\n\n"
                   f"👥 Пользователей: *{len(users)}*\n"
                   f"📋 Анкет: *{len(cands)}*\n"
                   f"🔓 Вакансий: *{len(load_vacs())}*\n\n"
                   "🏭 *По вакансиям:*\n" +
                   "\n".join([f"• {v}: *{n}* чел." for v,n in by_vac.most_common()]) +
                   "\n\n📅 *По месяцам:*\n" +
                   "\n".join([f"• {m}: *{n}* чел." for m,n in sorted(by_month.items(),reverse=True)[:6]]) +
                   "\n\n🌍 *По языкам:*\n" +
                   "\n".join([f"• {flags.get(l,'🌐')} {l.upper()}: *{n}*" for l,n in by_lang.most_common()]))
            await update.message.reply_text(txt, parse_mode="Markdown", reply_markup=mgr_keyboard())
        elif text == "💬 Чат с Аней":
            user["state"] = S_MGR_CHAT
            user["mgr_history"] = []
            await update.message.reply_text(
                "💬 *Режим чата с Аней активен*\n\nСпросите что угодно — анализ кандидатов, советы по вакансиям, статистику.\n\nДля выхода нажмите любую кнопку меню.",
                parse_mode="Markdown", reply_markup=mgr_keyboard())
        elif text == "📢 Рассылка":
            vacs = load_vacs()
            if not vacs:
                await update.message.reply_text("Нет вакансий для рассылки.")
                return
            buttons = [[InlineKeyboardButton(f"📢 {n}",callback_data=f"pub{i}")] for i,n in enumerate(vacs.keys())]
            users_count = len(load_users())
            await update.message.reply_text(
                f"📢 *Рассылка вакансии*\n\nПолучат: *{users_count}* пользователей\n\nВыберите вакансию:",
                parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(buttons))
        elif text == "📣 Проверить канал":
            users = load_users()
            subs = 0
            for uid_str in list(users.keys())[:50]:
                try:
                    m = await context.bot.get_chat_member(chat_id=CHANNEL, user_id=int(uid_str))
                    if m.status in ["member","administrator","creator"]: subs += 1
                except: pass
            await update.message.reply_text(
                f"📣 *Канал:* {CHANNEL}\n\n"
                f"👥 Пользователей бота: *{len(users)}*\n"
                f"✅ Подписаны на канал: *{subs}*",
                parse_mode="Markdown", reply_markup=mgr_keyboard())
        else:
            user["state"] = S_NONE
            await update.message.reply_text("Выберите действие:", reply_markup=mgr_keyboard())
        return

    # ========== КАНДИДАТ ==========
    register_user(uid, update.effective_user.username, lang)

    # Кнопки кандидата
    btn_vac = {"📋 Вакансии","📋 Вакансияҳо","📋 Vakansiyalar","📋 Вакансиялар"}
    btn_ank = {"📝 Анкета","📝 Заполнить анкету","📝 Anketa","📝 Анкета толтыру"}
    btn_ask = {"💬 Спросить Аню","💬 Аняро пурс","💬 Anyadan so'ra","💬 Аняға сұра"}
    btn_ch  = {"📢 Канал","📢 Kanal","📢 Арна"}

    if text in btn_vac:
        vacs = load_vacs()
        if not vacs:
            msgs = {"ru":"😔 Сейчас открытых вакансий нет.","tj":"😔 Ҳозир вакансия нест.",
                    "uz":"😔 Hozir vakansiya yo'q.","kz":"😔 Қазір вакансия жоқ."}
            await update.message.reply_text(msgs.get(lang,msgs["ru"]), reply_markup=cand_keyboard(lang))
            return
        for name,data in vacs.items():
            info = data.get("info","") if isinstance(data,dict) else data
            photo = data.get("photo") if isinstance(data,dict) else None
            msg = f"🏭 *{name}*\n\n{info}"
            if photo: await update.message.reply_photo(photo=photo,caption=msg,parse_mode="Markdown")
            else: await update.message.reply_text(msg,parse_mode="Markdown")
        hints = {"ru":"Хотите подать заявку? 📝","tj":"Анкета пур кардан? 📝","uz":"Ariza topshirish? 📝","kz":"Өтінім беру? 📝"}
        await update.message.reply_text(hints.get(lang,hints["ru"]), reply_markup=cand_keyboard(lang))
        return

    if text in btn_ank:
        vacs = load_vacs()
        if not vacs:
            await update.message.reply_text("😔 Вакансий нет.", reply_markup=cand_keyboard(lang))
            return
        user["state"] = S_VAC; user["anketa"] = {}
        t = anketa_t(lang)
        await update.message.reply_text(t["cv"], reply_markup=vac_inline())
        return

    if text in btn_ask:
        user["state"] = S_NONE
        msgs = {"ru":"Конечно! 😊 Задайте вопрос!","tj":"Албатта! 😊 Савол бипурсед!",
                "uz":"Albatta! 😊 Savol bering!","kz":"Әрине! 😊 Сұрақ қойыңыз!"}
        await update.message.reply_text(msgs.get(lang,msgs["ru"]), reply_markup=cand_keyboard(lang))
        return

    if text in btn_ch:
        is_sub = await check_subscription(context.bot, uid)
        if is_sub:
            msgs = {
                "ru": f"✅ Вы подписаны на {CHANNEL}!\n\nОтлично — новые вакансии придут первыми! 🔥",
                "tj": f"✅ Шумо обунаи {CHANNEL} ҳастед!\n\nВакансияҳои нав аввал ба шумо меояд! 🔥",
                "uz": f"✅ Siz {CHANNEL} ga obunasiz!\n\nYangi vakansiyalar birinchi sizga keladi! 🔥",
                "kz": f"✅ Сіз {CHANNEL} арнасына жазылдыңыз!\n\nЖаңа вакансиялар бірінші сізге келеді! 🔥",
            }
            await update.message.reply_text(msgs.get(lang, msgs["ru"]), reply_markup=cand_keyboard(lang))
        else:
            msgs = {
                "ru": f"📢 Подпишитесь на наш канал!\n\nТам публикуем новые вакансии первыми 🔥\n\nПосле подписки нажмите кнопку ✅ Проверить",
                "tj": f"📢 Каналамонро обуна шавед!\n\nВакансияҳои нав аввал он ҷо! 🔥\n\nБаъд аз обуна тугмаи ✅ Санҷед",
                "uz": f"📢 Kanalimizga obuna bo'ling!\n\nYangi vakansiyalar birinchi o'sha yerda! 🔥\n\nObunadan so'ng ✅ Tekshirish tugmasini bosing",
                "kz": f"📢 Каналымызға жазылыңыз!\n\nЖаңа вакансиялар алдымен сонда! 🔥\n\nЖазылғаннан кейін ✅ Тексеру батырмасын басыңыз",
            }
            check_btns = {
                "ru": "✅ Я подписался — проверить",
                "tj": "✅ Ман обуна шудам — санҷед",
                "uz": "✅ Obuna bo'ldim — tekshirish",
                "kz": "✅ Жазылдым — тексеру",
            }
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("📢 Открыть канал", url=f"https://t.me/{CHANNEL.lstrip('@')}"),
                InlineKeyboardButton(check_btns.get(lang, check_btns["ru"]), callback_data="check_sub"),
            ]])
            await update.message.reply_text(msgs.get(lang, msgs["ru"]), reply_markup=kb)
        return

    # Анкета заполнение
    t = anketa_t(lang)
    if state == S_FIO:
        user["anketa"]["fio"] = " ".join(p.capitalize() for p in text.split())
        user["state"] = S_DOB
        await update.message.reply_text(f"✅ *{user['anketa']['fio']}*\n\n{t['dob']}", parse_mode="Markdown"); return
    if state == S_DOB:
        import re
        dob_clean = text.replace("/",".").replace("-",".").replace(" ","")
        # Проверяем формат ДД.ММ.ГГГГ
        dob_match = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$", dob_clean)
        if not dob_match:
            err_msgs = {
                "ru": "⚠️ Неверный формат даты!\n\nНапишите в формате ДД.ММ.ГГГГ\n_Пример: 15.03.1990_",
                "tj": "⚠️ Формати нодуруст!\n\nБо ин шакл нависед: РР.ММ.СССС\n_Мисол: 15.03.1990_",
                "uz": "⚠️ Noto'g'ri format!\n\nKK.OO.YYYY shaklida yozing\n_Misol: 15.03.1990_",
                "kz": "⚠️ Формат қате!\n\nКК.АА.ЖЖЖЖ форматында жазыңыз\n_Мысал: 15.03.1990_",
            }
            await update.message.reply_text(err_msgs.get(lang, err_msgs["ru"]), parse_mode="Markdown")
            return
        day, month, year = int(dob_match.group(1)), int(dob_match.group(2)), int(dob_match.group(3))
        if not (1 <= day <= 31 and 1 <= month <= 12 and 1930 <= year <= 2007):
            err_msgs = {
                "ru": "⚠️ Дата некорректна!\n\nПроверьте день (1-31), месяц (1-12) и год (1930-2007)\n_Пример: 15.03.1990_",
                "tj": "⚠️ Санаи нодуруст!\n\nРӯз (1-31), моҳ (1-12), сол (1930-2007)\n_Мисол: 15.03.1990_",
                "uz": "⚠️ Noto'g'ri sana!\n\nKun (1-31), oy (1-12), yil (1930-2007)\n_Misol: 15.03.1990_",
                "kz": "⚠️ Күн қате!\n\nКүн (1-31), ай (1-12), жыл (1930-2007)\n_Мысал: 15.03.1990_",
            }
            await update.message.reply_text(err_msgs.get(lang, err_msgs["ru"]), parse_mode="Markdown")
            return
        user["anketa"]["dob"] = f"{day:02d}.{month:02d}.{year}"
        user["state"] = S_GR
        await update.message.reply_text(f"✅ *{user['anketa']['dob']}*\n\n{t['gr']}", parse_mode="Markdown"); return
    if state == S_GR:
        user["anketa"]["grazhdanstvo"] = text.upper()
        user["state"] = S_PHN
        await update.message.reply_text(f"✅ *{user['anketa']['grazhdanstvo']}*\n\n{t['phn']}", parse_mode="Markdown"); return
    if state == S_PHN:
        user["anketa"]["phone"] = text
        user["state"] = S_TG
        await update.message.reply_text(f"✅ *{text}*\n\n{t['tg']}", parse_mode="Markdown"); return
    if state == S_TG:
        user["anketa"]["tg"] = text
        user["state"] = S_WA
        await update.message.reply_text(f"✅ *{text}*\n\n{t['wa']}", parse_mode="Markdown"); return
    if state == S_WA:
        user["anketa"]["wa"] = text
        user["state"] = S_NONE
        anketa = user["anketa"]
        lb = {"ru":("📋 *Ваша анкета:*","Вакансия","ФИО","Дата рождения","Гражданство","Телефон"),
              "tj":("📋 *Анкетаи шумо:*","Вакансия","ФИО","Таввалуд","Гражданство","Телефон"),
              "uz":("📋 *Sizning anketangiz:*","Vakansiya","FIO","Tug'ilgan sana","Fuqarolik","Telefon"),
              "kz":("📋 *Сіздің анкетаңыз:*","Вакансия","АТӘ","Туған күні","Азаматтық","Телефон")}
        l = lb.get(lang,lb["ru"])
        summary = (f"{l[0]}\n━━━━━━━━━━━━━━━\n"
                   f"🏭 {l[1]}: {anketa.get('vakansiya','—')}\n"
                   f"👤 {l[2]}: {anketa.get('fio','—')}\n"
                   f"📅 {l[3]}: {anketa.get('dob','—')}\n"
                   f"🌍 {l[4]}: {anketa.get('grazhdanstvo','—')}\n"
                   f"📞 {l[5]}: {anketa.get('phone','—')}\n"
                   f"💬 Telegram: {anketa.get('tg','—')}\n"
                   f"📱 WhatsApp: {anketa.get('wa','—')}\n"
                   f"━━━━━━━━━━━━━━━\n{t['done']}")
        await update.message.reply_text(summary, parse_mode="Markdown", reply_markup=cand_keyboard(lang))
        username = update.effective_user.username
        await send_to_manager(context.application, anketa, uid, username, lang)
        cands = load_cands()
        cands[str(uid)] = {"tg_id":uid,"username":username,"anketa":anketa,
                           "date":datetime.now().strftime("%d.%m.%Y %H:%M"),"lang":lang,"status":"new","questions":user.get("questions",[])}
        save_cands(cands)
        return

    # Обычный разговор
    user["questions"].append(text[:50])
    if len(user["questions"]) > 20: user["questions"] = user["questions"][-20:]
    history = user.get("history",[])
    history.append({"role":"user","content":text})
    if len(history) > 16: history = history[-16:]
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    reply = groq_ask(history, make_system(lang))
    history.append({"role":"assistant","content":reply})
    user["history"] = history
    await update.message.reply_text(reply, reply_markup=cand_keyboard(lang))

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Аня v6 запущена! ✅ RU TJ UZ KZ | Канал | Рассылка | Статистика | Проверка даты")
    app.run_polling()

if __name__ == "__main__":
    main()
