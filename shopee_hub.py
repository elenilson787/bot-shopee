import time
import hashlib
import json
import requests

class ShopeeAffiliateHub:
    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id or ""
        self.app_secret = app_secret or ""
        # Endpoint oficial da Shopee Brasil
        self.endpoint = "https://open-api.affiliate.shopee.com.br/graphql"

    def _generate_signature(self, timestamp: int, payload: str) -> str:
        factor = f"{self.app_id}{timestamp}{payload}{self.app_secret}"
        return hashlib.sha256(factor.encode('utf-8')).hexdigest()

    def _execute_query(self, query_str: str, variables: dict = None) -> dict:
        if not self.app_id or not self.app_secret:
            return {"error": "Credenciais da Shopee não configuradas no Render!"}

        timestamp = int(time.time())
        payload = json.dumps({"query": query_str, "variables": variables or {}}, separators=(',', ':'))
        signature = self._generate_signature(timestamp, payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"SHA256 Credential={self.app_id}, Timestamp={timestamp}, Signature={signature}"
        }

        try:
            response = requests.post(self.endpoint, data=payload, headers=headers, timeout=12)
            return response.json()
        except Exception as e:
            return {"error": f"Falha de conexão com a Shopee: {str(e)}"}

    def get_offers(self, limit: int = 15, sort_by_commission: bool = False):
        graphql_query = """
        query GetOffers($limit: Int) {
            productOfferV2(page: 1, limit: $limit) {
                nodes {
                    itemId
                    productName
                    price
                    imageUrl
                    offerLink
                    commissionRate
                }
            }
        }
        """
        result = self._execute_query(graphql_query, {"limit": limit})
        
        if "error" in result:
            return None, result["error"]

        if "errors" in result and result["errors"]:
            err_msg = result["errors"][0].get("message", "Erro GraphQL desconhecido")
            return None, f"Shopee Recusou: {err_msg}"

        data = result.get("data") or {}
        product_offer = data.get("productOfferV2") or {}
        offers = product_offer.get("nodes") or []

        if not offers:
            return None, "Nenhuma oferta retornada na lista da Shopee no momento."

        if sort_by_commission:
            offers.sort(key=lambda x: float(x.get("commissionRate", 0) or 0), reverse=True)

        return offers, None

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
