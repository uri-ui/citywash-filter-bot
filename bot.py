import os,json,re,logging
from telegram import Update,InlineKeyboardButton,InlineKeyboardMarkup
from telegram.ext import Application,CommandHandler,MessageHandler,CallbackQueryHandler,filters,ContextTypes

TOKEN=os.environ.get('TELEGRAM_BOT_TOKEN','')
DATA_FILE='subscribers.json'
BRANCHES=[
    'ירושלים','תל אביב','רעננה','כפר סבא','נתניה',
    'חיפה','באר שבע','אשדוד','ראשון לציון','פתח תקווה',
    'הרצליה','נחלים','גבעת שמואל','קרית מלאכי','מודיעין',
    'בית שמש','נתבג','כרמיאל','ישפרו','מנטה',
    'לוד','רמת גן','גבעתיים','חולון','בת ים','יבנה','רחובות',
]

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger(__name__)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,'r',encoding='utf-8') as f:return json.load(f)
    return {}
def save_data(d):
    with open(DATA_FILE,'w',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def extract_branch(text):
    tags=re.findall(r'#(\S+)',text)
    for c in (tags or [text]):
        c=c.strip().strip('#')
        for b in BRANCHES:
            if c==b or c in b or b in c:return b
    return None

async def start(u,ctx):
    await u.message.reply_text(
        f"שלום {u.effective_user.first_name}!\n"
        "ברוכים הבאים לבוט סינון עדכונים City Wash Express!\n\n"
        "/branches - בחר סניפים\n/my_branches - הסניפים שלך"
    )

async def show_menu(u,ctx):
    uid=str(u.effective_user.id)
    data=load_data()
    sel=data.get(uid,{}).get('branches',[])
    kb=[]
    for i in range(0,len(BRANCHES),2):
        row=[]
        for b in BRANCHES[i:i+2]:
            row.append(InlineKeyboardButton(('✅ ' if b in sel else '⬜ ')+b,callback_data='b_'+b))
        kb.append(row)
    kb.append([InlineKeyboardButton('🗑 נקה',callback_data='clear'),
               InlineKeyboardButton('💾 שמור',callback_data='save')])
    markup=InlineKeyboardMarkup(kb)
    txt="בחר סניפים לקבלת עדכונים:"
    if u.callback_query:await u.callback_query.edit_message_text(txt,reply_markup=markup)
    else:await u.message.reply_text(txt,reply_markup=markup)

async def my_branches_cmd(u,ctx):
    uid=str(u.effective_user.id)
    sel=load_data().get(uid,{}).get('branches',[])
    msg="\n".join('✅ '+b for b in sel) if sel else "לא נבחרו סניפים. /branches"
    await u.message.reply_text(msg)

async def button_cb(u,ctx):
    q=u.callback_query;await q.answer()
    uid=str(q.from_user.id)
    data=load_data()
    if uid not in data:data[uid]={'branches':[],'name':q.from_user.first_name or ''}
    if q.data.startswith('b_'):
        b=q.data[2:];brs=data[uid]['branches']
        if b in brs:brs.remove(b)
        else:brs.append(b)
        save_data(data);await show_menu(u,ctx)
    elif q.data=='clear':
        data[uid]['branches']=[];save_data(data);await show_menu(u,ctx)
    elif q.data=='save':
        save_data(data);sel=data[uid]['branches']
        if sel:await q.edit_message_text("נשמר!\n"+'\n'.join('✅ '+b for b in sel)+"\n\nלשינוי: /branches")
        else:await q.edit_message_text("לא נבחרו סניפים. /branches")

async def channel_post(u,ctx):
    msg=u.channel_post
    if not msg:return
    text=msg.text or msg.caption or ''
    if not text:return
    branch=extract_branch(text)
    if not branch:return
    data=load_data();sent=0
    for uid,ud in data.items():
        if branch not in ud.get('branches',[]):continue
        try:
            if msg.photo:
                await ctx.bot.send_photo(int(uid),msg.photo[-1].file_id,
                    caption=f"עדכון מ-{branch}:\n\n{text}")
            else:
                await ctx.bot.send_message(int(uid),f"עדכון מ-{branch}:\n\n{text}")
            sent+=1
        except Exception as e:logger.warning(f"Error {uid}: {e}")
    logger.info(f"Sent update about {branch} to {sent} subscribers")

def main():
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("branches",show_menu))
    app.add_handler(CommandHandler("change_branches",show_menu))
    app.add_handler(CommandHandler("my_branches",my_branches_cmd))
    app.add_handler(CallbackQueryHandler(button_cb))
    app.add_handler(MessageHandler(filters.UpdateType.CHANNEL_POSTS,channel_post))
    logger.info("Bot starting...")
    app.run_polling(drop_pending_updates=True)

if __name__=='__main__':main()
