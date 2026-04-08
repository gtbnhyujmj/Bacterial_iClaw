from core import ApiCredentials
from exchanges.bingx_swap import BingXSwapClient, BingXSwapEnv


def build_bingx_client() -> BingXSwapClient:
    env = BingXSwapEnv(
        base_url="https://open-api.bingx.com",
        timeout=10,
    )
    credentials = ApiCredentials(
        api_key="YOUR_API_KEY",
        secret_key="YOUR_SECRET_KEY",
    )
    return BingXSwapClient(env=env, credentials=credentials)
