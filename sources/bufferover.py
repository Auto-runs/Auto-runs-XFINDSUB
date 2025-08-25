import aiohttp

async def fetch(domain):
    url = f"https://dns.bufferover.run/dns?q=.{domain}"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=15) as r:
                if r.status != 200:
                    return []
                data = await r.json()
                subs = set()
                for item in data.get("FDNS_A", []):
                    sub = item.split(",")[1]
                    subs.add(sub.strip())
                return list(subs)
        except:
            return []
