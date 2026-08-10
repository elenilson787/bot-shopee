import time
import hashlib
import json
import requests

def sanitize_key(val: str) -> str:
    """Limpa espaços, aspas simples e aspas duplas acidentais das variáveis de ambiente."""
    if not val:
        return ""
    return str(val).strip().strip('"').strip("'").strip()

class ShopeeAffiliateHub:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = sanitize_key(app_id)
        self.app_secret = sanitize_key(app_secret)
        self.endpoint = "https://open-api.affiliate.shopee.com.br/graphql"
        
        print(f"🔑 Shopee API Configurada - App ID: '{self.app_id}' (Tamanho do Secret: {len(self.app_secret)})")

    def _generate_signature(self, timestamp: int, payload: str) -> str:
        factor = f"{self.app_id}{timestamp}{payload}{self.app_secret}"
        return hashlib.sha256(factor.encode('utf-8')).hexdigest()

    def _execute_query(self, query_str: str, variables: dict = None, retries: int = 1) -> dict:
        timestamp = int(time.time())
        
        # Minifica a query GraphQL removendo espaços redundantes
        clean_query = " ".join(query_str.split())
        
        payload_dict = {"query": clean_query}
        if variables:
            payload_dict["variables"] = variables
            
        payload = json.dumps(payload_dict, separators=(',', ':'), ensure_ascii=False)
        signature = self._generate_signature(timestamp, payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={self.app_id}, Timestamp={timestamp}, Signature={signature}"
        }

        try:
            response = requests.post(
                self.endpoint, 
                data=payload.encode('utf-8'), 
                headers=headers, 
                timeout=12
            )
            res_json = response.json()
            
            if "errors" in res_json and res_json["errors"]:
                err_msg = res_json["errors"][0].get("message", "Erro de Autenticação")
                
                # Se for erro de assinatura (10020), tenta mais 1 vez atualizando o timestamp
                if ("10020" in err_msg or "Invalid Signature" in err_msg) and retries > 0:
                    time.sleep(1)
                    return self._execute_query(query_str, variables, retries=retries - 1)
                
                print(f"⚠️ Shopee Recusou: {err_msg}")
                return {"error": f"Shopee Recusou: {err_msg}"}
                
            return res_json
        except Exception as e:
            print(f"❌ Erro ao conectar com a API da Shopee: {e}")
            return {"error": str(e)}

    def get_offers(self, limit: int = 30, sort_by_commission: bool = False):
        graphql_query = """
        query GetHotOffers($limit: Int) {
            productOfferV2(page: 1, limit: $limit) {
                nodes {
                    itemId
                    productName
                    price
                    imageUrl
                    offerLink
                    commissionRate
                    commission
                }
            }
        }
        """
        result = self._execute_query(graphql_query, {"limit": limit})
        
        if "error" in result:
            return result

        data = result.get("data") or {}
        product_offer = data.get("productOfferV2") or {}
        offers = product_offer.get("nodes") or []
        
        if sort_by_commission and offers:
            offers.sort(key=lambda x: float(x.get("commissionRate", 0) or 0), reverse=True)
            
        return offers

    def convert_to_affiliate_link(self, original_url: str, sub_id: str = "bot_private") -> str:
        graphql_query = """
        query ConvertLink($originUrl: String!, $subId: String) {
            generateUrl(originUrl: $originUrl, subId1: $subId) {
                shortLink
            }
        }
        """
        result = self._execute_query(graphql_query, {"originUrl": original_url, "subId": sub_id})
        data = result.get("data") or {}
        gen_url = data.get("generateUrl") or {}
        return gen_url.get("shortLink", original_url)
        
