import time
import hashlib
import json
import requests

class ShopeeAffiliateHub:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.endpoint = "https://open-api.affiliate.shopee.com.br/graphql"

    def _generate_signature(self, timestamp: int, payload: str) -> str:
        factor = f"{self.app_id}{timestamp}{payload}{self.app_secret}"
        return hashlib.sha256(factor.encode('utf-8')).hexdigest()

    def _execute_query(self, query_str: str, variables: dict = None) -> dict:
        timestamp = int(time.time())
        payload = json.dumps({"query": query_str, "variables": variables or {}})
        signature = self._generate_signature(timestamp, payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={self.app_id}, Timestamp={timestamp}, Signature={signature}"
        }

        try:
            response = requests.post(self.endpoint, data=payload, headers=headers, timeout=10)
            return response.json()
        except Exception as e:
            print(f"❌ Erro de conexão com Shopee: {e}")
            return {}

    def get_offers(self, limit: int = 20, sort_by_commission: bool = False):
        """Busca ofertas na Shopee usando schema GraphQL padronizado."""
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
        
        # Exibe a resposta real nos logs do Render para acompanhamento
        print(f"🔍 Resposta da API Shopee: {json.dumps(result)}")

        if "errors" in result:
            print(f"⚠️ GraphQL retornou erro: {result.get('errors')}")

        data = result.get("data") or {}
        product_offer = data.get("productOfferV2") or {}
        offers = product_offer.get("nodes") or []
        
        # Ordena da maior comissão para a menor quando solicitado
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
