import aiohttp

async def fetch(domain):
    url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=15) as r:
                if r.status != 200:
                    return []
                data = await r.json()
                subs = {x["hostname"] for x in data.get("passive_dns", []) if "hostname" in x}
                return list(subs)
        except:
            return []
