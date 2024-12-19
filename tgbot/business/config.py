class MainClassBusiness:
    def __init__(self, pool, bot):
        self.pool = pool
        self.bot = bot

class UsersClassBusiness(MainClassBusiness):
    async def get_user(self, userid):
        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('SELECT * FROM users WHERE userid = $1', userid)
            if result:
                return {"userid": result["userid"], "username": result["username"]}
            return None
