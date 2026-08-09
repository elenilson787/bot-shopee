import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from shopee_hub import ShopeeAffiliateHub

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SHOPEE_APP_ID = os.environ.get("SHOPEE_APP_ID")
SHOPEE_APP_SECRET = os.environ.get("SHOPEE_APP_SECRET")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
shopee = ShopeeAffiliateHub(app_id=SHOPEE_APP_ID, app_secret=SHOPEE_APP_SECRET)

# --- COMANDO /START E MENU PRINCIPAL ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("🔎 Buscar Oferta por Filtros", callback_data="menu_filters"),
        InlineKeyboardButton("⚙️ Configurar Intervalo de Postagem", callback_data="config_interval"),
        InlineKeyboardButton("📢 Status do Robô / Chat ID", callback_data="status_info")
    )
    
    welcome_text = (
        f"Olá, <b>{user_name}</b>! 👋\n\n"
        f"Eu sou o seu <b>Robô de Ofertas e Altas Comissões da Shopee</b>.\n\n"
        f"<b>Escolha uma das opções abaixo:</b>"
    )
    
    bot.reply_to(message, welcome_text, parse_mode="HTML", reply_markup=markup)

# --- SUBMENU DE FILTROS ---
def show_filter_menu(chat_id, message_id=None):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("💰 Maiores Comissões (Qualquer Desconto)", callback_data="fetch_top_commission"),
        InlineKeyboardButton("💥 Descontos Maiores de 10%", callback_data="fetch_disc_10"),
        InlineKeyboardButton("🔥 Descontos Maiores de 30%", callback_data="fetch_disc_30"),
        InlineKeyboardButton("🎁 Qualquer Desconto / Oferta Ativa", callback_data="fetch_disc_0"),
        InlineKeyboardButton("⬅️ Voltar ao Menu Principal", callback_data="menu_main")
    )
    
    text = "🎯 <b>Como você deseja buscar as ofertas agora?</b>\n<i>Escolha o tipo de filtro desejado:</i>"
    
    if message_id:
        bot.edit_message_text(text, chat_id, message_id, parse_mode="HTML", reply_markup=markup)
    else:
        bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup)

# --- RESPOSTAS DOS BOTÕES ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    
    if call.data == "menu_filters":
        show_filter_menu(chat_id, call.message.message_id)

    elif call.data == "menu_main":
        send_welcome(call.message)

    elif call.data in ["fetch_top_commission", "fetch_disc_10", "fetch_disc_30", "fetch_disc_0"]:
        bot.answer_callback_query(call.id, "🔍 Consultando API da Shopee...")
        
        # Define os parâmetros de acordo com o botão clicado
        if call.data == "fetch_top_commission":
            min_disc = 0
            sort_comm = True
            msg_header = "💰 <b>PRODUTO COM ALTA COMISSÃO!</b> 💰"
        elif call.data == "fetch_disc_10":
            min_disc = 10
            sort_comm = False
            msg_header = "💥 <b>OFERTA COM MAIS DE 10% DE DESCONTO!</b> 💥"
        elif call.data == "fetch_disc_30":
            min_disc = 30
            sort_comm = False
            msg_header = "🔥 <b>SUPER DESCONTO (MAIS DE 30%)!</b> 🔥"
        else: # fetch_disc_0
            min_disc = 0
            sort_comm = False
            msg_header = "📦 <b>OFERTA ENCONTRADA NA SHOPEE!</b> 📦"

        deals = shopee.get_offers(limit=20, min_discount=min_disc, sort_by_commission=sort_comm)
        
        if deals:
            item = deals[0]
            title = item.get("productName")
            price_original = float(item.get("price", 0))
            discount = float(item.get("discount", 0))
            commission_rate = float(item.get("commissionRate", 0))
            price_discounted = price_original * (1 - (discount / 100)) if discount > 0 else price_original
            
            affiliate_link = shopee.convert_to_affiliate_link(item.get("offerLink"), sub_id="bot_private")
            
            caption = (
                f"{msg_header}\n\n"
                f"📦 <b>{title[:70]}...</b>\n\n"
                f"🏷️ <b>Desconto:</b> {discount:.0f}%\n"
                f"💵 <b>Comissão Estimada do Afiliado:</b> {commission_rate:.1f}%\n"
                f"❌ De: <s>R$ {price_original:.2f}</s>\n"
                f"✅ Por: <b>R$ {price_discounted:.2f}</b>\n\n"
                f"🛒 <b>COMPRE AQUI:</b>\n{affiliate_link}"
            )
            
            bot.send_photo(chat_id, photo=item.get("imageUrl"), caption=caption, parse_mode="HTML")
        else:
            bot.send_message(chat_id, f"⚠️ Nenhuma oferta encontrada para este critério no momento.")

    elif call.data == "config_interval":
        bot.send_message(chat_id, "⚙️ <b>Configuração de Intervalo:</b>\nVocê pode alterar os horários e o tempo entre disparos no painel principal.", parse_mode="HTML")

    elif call.data == "status_info":
        bot.send_message(chat_id, f"ℹ️ <b>Seu Chat ID:</b> <code>{chat_id}</code>\nRobô ativo e conectado!", parse_mode="HTML")

if __name__ == "__main__":
    print("🤖 Robô atualizado e escutando o Telegram...")
    bot.infinity_polling()
