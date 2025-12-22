import aiohttp
from .constants import OAUTH_TOKEN_URL

class AuthManager:
    """
    Manages OAuth 2.0 Refresh Flow automatically.
    """
    def __init__(self, client_id, refresh_token):
        self.client_id = client_id
        self.refresh_token = refresh_token
        self.access_token = None

    async def refresh_access_token(self):
        """
        Exchanges the stored Refresh Token for a new Access Token.
        """
        print("🔐 [AUTH] Refreshing Access Token via Etsy API...")
        async with aiohttp.ClientSession() as session:
            payload = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": self.refresh_token
            }
            try:
                async with session.post(OAUTH_TOKEN_URL, data=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.access_token = data.get("access_token")
                        
                        # Update refresh token if returned (rotation)
                        if data.get("refresh_token"):
                            self.refresh_token = data.get("refresh_token")
                            
                        print("✅ [AUTH] Token refreshed successfully.")
                        return True
                    else:
                        text = await response.text()
                        print(f"❌ [AUTH ERROR] Failed to refresh: {text}")
                        return False
            except Exception as e:
                print(f"❌ [AUTH EXCEPTION] {str(e)}")
                return False

    def get_headers(self):
        """Returns headers with the valid Bearer token."""
        return {
            "x-api-key": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
            "X-Is-Load-Test": "true"
        }