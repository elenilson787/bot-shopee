import os
import json
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from shopee_hub import ShopeeAffiliateHub

# Carrega os Tokens
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SHOPEE_APP_ID = os.environ.get("SHOPEE_APP_ID")
SHOPEE_APP_SECRET = os.environ.get("SHOPEE_APP_SECRET")

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
shopee = ShopeeAffiliateHub(app_id=SHOPEE_APP_ID, app_secret=SHOPEE_APP_SECRET)

# --- COMANDO /START E MENU INTERATIVO ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name
    
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    markup.add(
        InlineKeyboardButton("🔥 Buscar Oferta Relâmpago Agora", callback_data="get_deal"),
        InlineKeyboardButton("⚙️ Configurar Intervalo de Postagem", callback_data="config_interval"),
        InlineKeyboardButton("📢 Status do Grupo / Privado", callback_data="status_info")
    )
    
    welcome_text = (
        f"Olá, <b>{user_name}</b>! 👋\n\n"
        f"Eu sou o seu <b>Robô de Ofertas da Shopee</b>.\n\n"
        f"<b>O que eu posso fazer por você:</b>\n"
        f"• Monitorar e buscar ofertas relâmpago em tempo real.\n"
        f"• Converter links normais em links de afiliado com seu ID.\n"
        f"• Publicar ofertas automaticamente no seu grupo ou no seu privado.\n\n"
        f"<i>Escolha uma das opções abaixo para testar:</i>"
    )
    
    bot.reply_to(message, welcome_text, parse_mode="HTML", reply_markup=markup)

# --- RESPOSTA DOS BOTÕES ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    if call.data == "get_deal":
        bot.answer_callback_query(call.id, "🔍 Buscando a melhor oferta...")
        
        deals = shopee.get_flash_deals(limit=5, min_discount=30)
        if deals:
            item = deals[0]
            title = item.get("productName")
            price_original = float(item.get("price", 0))
            discount = float(item.get("discount", 0))
            price_discounted = price_original * (1 - (discount / 100))
            
            affiliate_link = shopee.convert_to_affiliate_link(item.get("offerLink"), sub_id="bot_private")
            
            caption = (
                f"🔥 <b>OFERTA RELÂMPAGO ENCONTRADA!</b> 🔥\n\n"
                f"📦 <b>{title[:70]}...</b>\n\n"
                f"💥 <b>{discount:.0f}% DE DESCONTO</b>\n"
                f"❌ De: <s>R$ {price_original:.2f}</s>\n"
                f"✅ Por: <b>R$ {price_discounted:.2f}</b>\n\n"
                f"🛒 <b>COMPRE AQUI:</b>\n{affiliate_link}"
            )
            
            bot.send_photo(call.message.chat.id, photo=item.get("imageUrl"), caption=caption, parse_mode="HTML")
        else:
            bot.send_message(call.message.chat.id, "⚠️ Nenhuma oferta acima de 30% encontrada agora.")

    elif call.data == "config_interval":
        bot.send_message(call.message.chat.id, "⚙️ <b>Modo de Configuração:</b>\nEm breve você poderá escolher intervalos de 10m, 20m ou 30m direto por aqui!", parse_mode="HTML")

    elif call.data == "status_info":
        bot.send_message(call.message.chat.id, f"ℹ️ <b>Seu Chat ID:</b> <code>{call.message.chat.id}</code>\nRobô ativo e pronto para uso!", parse_mode="HTML")

# --- INICIA O ESCUTADOR ATIVO ---
if __name__ == "__main__":
    print("🤖 Robô ativo e escutando o Telegram...")
    bot.infinity_polling()
