import os
import json
import requests
from shopee_hub import ShopeeAffiliateHub

HISTORY_FILE = "posted_history.json"

def load_history() -> set:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return set(json.load(f))
        except json.JSONDecodeError:
            return set()
    return set()

def save_history(history_set: set):
    history_list = list(history_set)[-200:]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history_list, f, indent=2)

def run_once():
    posted_ids = load_history()
    shopee = ShopeeAffiliateHub(
        app_id=os.environ.get("SHOPEE_APP_ID"),
        app_secret=os.environ.get("SHOPEE_APP_SECRET")
    )
    
    deals = shopee.get_flash_deals(limit=15, min_discount=30)
    
    deal_to_post = None
    for item in deals:
        item_id = str(item.get("itemId"))
        if item_id not in posted_ids:
            deal_to_post = item
            break
            
    if deal_to_post:
        item_id = str(deal_to_post.get("itemId"))
        title = deal_to_post.get("productName")
        price_original = float(deal_to_post.get("price", 0))
        discount = float(deal_to_post.get("discount", 0))
        price_discounted = price_original * (1 - (discount / 100))
        
        affiliate_link = shopee.convert_to_affiliate_link(
            deal_to_post.get("offerLink"), 
            sub_id="telegram_bot"
        )
        
        caption = (
            f"🔥 <b>OFERTA RELÂMPAGO NA SHOPEE!</b> 🔥\n\n"
            f"📦 <b>{title[:70]}...</b>\n\n"
            f"💥 <b>{discount:.0f}% DE DESCONTO</b>\n"
            f"❌ De: <s>R$ {price_original:.2f}</s>\n"
            f"✅ Por: <b>R$ {price_discounted:.2f}</b>\n\n"
            f"🛒 <b>COMPRE AQUI:</b>\n{affiliate_link}"
        )
        
        url = f"https://api.telegram.org/bot{os.environ.get('TELEGRAM_BOT_TOKEN')}/sendPhoto"
        res = requests.post(url, data={
            "chat_id": os.environ.get("TELEGRAM_CHAT_ID"),
            "photo": deal_to_post.get("imageUrl"),
            "caption": caption,
            "parse_mode": "HTML"
        }).json()
        
        if res.get("ok"):
            print(f"✅ Oferta enviada para o Telegram com sucesso!")
            posted_ids.add(item_id)
            save_history(posted_ids)
        else:
            print(f"❌ Erro ao enviar Telegram: {res}")
    else:
        print("ℹ️ Nenhuma oferta nova encontrada nesta rodada.")

if __name__ == "__main__":
    run_once()