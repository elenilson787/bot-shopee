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
        InlineKeyboardButton("💰 Maiores Comissões", callback_data="fetch_top_commission"),
        InlineKeyboardButton("🎁 Qualquer Oferta Ativa na Shopee", callback_data="fetch_disc_0"),
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
    
    try:
        if call.data == "menu_filters":
            show_filter_menu(chat_id, call.message.message_id)

        elif call.data == "menu_main":
            send_welcome(call.message)

        elif call.data in ["fetch_top_commission", "fetch_disc_0"]:
            bot.answer_callback_query(call.id, "🔍 Consultando API da Shopee...")
            
            sort_comm = (call.data == "fetch_top_commission")
            msg_header = "💰 <b>PRODUTO COM ALTA COMISSÃO!</b> 💰" if sort_comm else "📦 <b>OFERTA ENCONTRADA NA SHOPEE!</b> 📦"

            # Lê o retorno da função sem forçar desempacotamento de variáveis
            res = shopee.get_offers(limit=15, sort_by_commission=sort_comm)
            
            # Trata resposta caso a Shopee retorne dicionário de erro
            if isinstance(res, dict) and "error" in res:
                bot.send_message(chat_id, f"⚠️ <b>Erro ao buscar oferta:</b>\n<code>{res['error']}</code>", parse_mode="HTML")
                return

            deals = res if isinstance(res, list) else []
            
            if deals:
                item = deals[0]
                title = item.get("productName", "Produto Shopee")
                price = float(item.get("price", 0) or 0)
                commission_rate = float(item.get("commissionRate", 0) or 0)
                
                if 0 < commission_rate < 1.0:
                    commission_rate *= 100
                
                affiliate_link = shopee.convert_to_affiliate_link(item.get("offerLink"), sub_id="bot_private")
                
                caption = (
                    f"{msg_header}\n\n"
                    f"📦 <b>{title[:70]}...</b>\n\n"
                    f"💵 <b>Comissão Estimada:</b> {commission_rate:.1f}%\n"
                    f"✅ Preço: <b>R$ {price:.2f}</b>\n\n"
                    f"🛒 <b>COMPRE AQUI:</b>\n{affiliate_link}"
                )
                
                bot.send_photo(chat_id, photo=item.get("imageUrl"), caption=caption, parse_mode="HTML")
            else:
                bot.send_message(chat_id, "⚠️ Nenhuma oferta encontrada no momento.")

        elif call.data == "status_info":
            bot.send_message(chat_id, f"ℹ️ <b>Seu Chat ID:</b> <code>{chat_id}</code>\nRobô ativo e conectado!", parse_mode="HTML")

    except Exception as e:
        print(f"❌ Erro ao processar clique do botão: {e}")
        bot.send_message(chat_id, f"⚠️ <b>Ocorreu uma falha interna:</b>\n<code>{e}</code>", parse_mode="HTML")

if __name__ == "__main__":
    print("🤖 Robô atualizado e escutando o Telegram...")
    try:
        bot.remove_webhook()
    except Exception as e:
        print(f"Aviso ao limpar webhook: {e}")
        
    bot.infinity_polling(skip_pending=True)
    
