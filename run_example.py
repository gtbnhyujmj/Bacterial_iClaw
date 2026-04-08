from config_example import build_bingx_client


if __name__ == "__main__":
    client = build_bingx_client()
    result = client.get_symbol_price_ticker("TIA-USDT")
    print(result)
