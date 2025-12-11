import requests, time

# Stores known dev wallets from pool creation (pair → dev address)
dev_wallets = {}

def dev_sell_sniper():
    print("Base — Dev Sell Sniper (alerts the second dev wallet dumps)")
    seen_txs = set()

    while True:
        try:
            # 1. Catch new pools and extract dev wallet
            r = requests.get("https://api.dexscreener.com/latest/dex/pairs/base")
            for pair in r.json().get("pairs", []):
                pair_addr = pair["pairAddress"]
                if pair_addr in dev_wallets:
                    continue

                age = time.time() - pair.get("pairCreatedAt", 0) / 1000
                if age > 120:  # skip old pools
                    continue

                tx_hash = pair.get("pairCreatedTxHash")
                if not tx_hash:
                    continue

                tx = requests.get(f"https://api.basescan.org/api?module=proxy&action=eth_getTransactionByHash&txhash={tx_hash}").json()
                creator = tx["result"]["from"]
                dev_wallets[pair_addr] = creator.lower()

            # 2. Watch all recent sells
            r2 = requests.get("https://api.dexscreener.com/latest/dex/transactions/base?limit=300")
            for tx in r2.json().get("transactions", []):
                txid = tx["hash"]
                if txid in seen_txs or tx.get("side") != "sell":
                    continue
                seen_txs.add(txid)

                seller = tx["from"].lower()
                pair_addr = tx["pairAddress"]
                usd = tx.get("valueUSD", 0)

                if pair_addr not in dev_wallets:
                    continue
                if seller == dev_wallets[pair_addr]:
                    token = tx["token0"]["symbol"] if "WETH" in tx["token1"]["symbol"] else tx["token1"]["symbol"]
                    print(f"DEV JUST DUMPED!\n"
                          f"{token} dev wallet sold ${usd:,.0f}\n"
                          f"Dev: {seller}\n"
                          f"Token age: {tx.get('age', 0)}s\n"
                          f"https://dexscreener.com/base/{pair_addr}\n"
                          f"https://basescan.org/address/{seller}\n"
                          f"→ The creator is out. Run or die.\n"
                          f"{'DEV SELL'*20}")

        except:
            pass
        time.sleep(1.6)

if __name__ == "__main__":
    dev_sell_sniper()
