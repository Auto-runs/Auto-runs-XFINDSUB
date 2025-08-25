import aiohttp

async def fetch(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, timeout=15) as r:
                if r.status != 200:
                    return []
                data = await r.json(content_type=None)
                subs = set()
                for entry in data:
                    name = entry['name_value']
                    if "*" not in name:
                        subs.add(name.strip())
                return list(subs)
        except:
            return []
