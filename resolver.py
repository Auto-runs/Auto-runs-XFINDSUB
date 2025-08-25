import dns.resolver

async def resolve(sub):
    try:
        dns.resolver.resolve(sub, "A")
        return True
    except:
        return False
