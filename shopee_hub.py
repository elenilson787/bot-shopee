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

        response = requests.post(self.endpoint, data=payload, headers=headers)
        return response.json()

    def get_flash_deals(self, limit: int = 15, min_discount: int = 30):
        graphql_query = """
        query GetHotOffers($limit: Int) {
            productOfferV2(page: 1, limit: $limit, sortType: 2) {
                nodes {
                    itemId
                    productName
                    price
                    discount
                    imageUrl
                    offerLink
                    commissionRate
                }
            }
        }
        """
        result = self._execute_query(graphql_query, {"limit": limit})
        offers = result.get("data", {}).get("productOfferV2", {}).get("nodes", [])
        return [item for item in offers if float(item.get("discount", 0)) >= min_discount]

    def convert_to_affiliate_link(self, original_url: str, sub_id: str = "github_bot") -> str:
        graphql_query = """
        query ConvertLink($originUrl: String!, $subId: String) {
            generateUrl(originUrl: $originUrl, subId1: $subId) {
                shortLink
            }
        }
        """
        result = self._execute_query(graphql_query, {"originUrl": original_url, "subId": sub_id})
        return result.get("data", {}).get("generateUrl", {}).get("shortLink", original_url)