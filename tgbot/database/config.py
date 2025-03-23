import asyncpg
import logging
import os
async def create_pool():
    try:
        pool = await asyncpg.create_pool(
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            host=os.getenv('DB_HOST'),
            min_size=int(1),
            max_size=int(10)
        )
        return pool
    except Exception as e:
        logging.error(f'"create_pool error": {e}')
async def init_db(pool):
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            userid BIGINT PRIMARY KEY,
                            username TEXT UNIQUE,
                            name TEXT
                        );
                    """)

            await conn.execute("""
                        CREATE TABLE IF NOT EXISTS groups (
                            groupid BIGINT PRIMARY KEY,
                            username TEXT UNIQUE,
                            name TEXT
                        );
                    """)

            await conn.execute("""
                        CREATE TABLE IF NOT EXISTS user_states (
                            userid BIGINT PRIMARY KEY REFERENCES users(userid) ON DELETE CASCADE
                        );
                    """)

            await conn.execute("""
                        CREATE TABLE IF NOT EXISTS group_states (
                            groupid BIGINT PRIMARY KEY REFERENCES groups(groupid) ON DELETE CASCADE,
                            bot_status BOOLEAN DEFAULT 1 -- 1: turn on 0: turn off
                        );
                    """)

            await conn.execute("""
                        CREATE TABLE IF NOT EXISTS admins(
                            groupid BIGINT REFERENCES groups(groupid) ON DELETE CASCADE,
                            userid BIGINT REFERENCES users(userid) ON DELETE CASCADE,
                            status BOOLEAN NOT NULL -- 1 supperadmin. 0 admin
                        );
                    """)

            await conn.execute("""
                        CREATE TABLE IF NOT EXISTS bangifs(
                            groupid BIGINT PRIMARY KEY REFERENCES groups(groupid) ON DELETE CASCADE,
                            gif TEXT NOT NULL
                        );
                    """)

            await conn.execute("""
                        CREATE TABLE IF NOT EXISTS banstickers(
                            groupid BIGINT PRIMARY KEY REFERENCES groups(groupid) ON DELETE CASCADE,
                            sticker TEXT NOT NULL
                        );
                    """)
            await conn.execute("""
                        CREATE TABLE IF NOT EXISTS banwords(
                            groupid BIGINT PRIMARY KEY REFERENCES groups(groupid) ON DELETE CASCADE,
                            word TEXT NOT NULL
                        );
                    """)
            await conn.execute("""
                        CREATE TABLE IF NOT EXISTS privilage(
                            groupid BIGINT REFERENCES groups(groupid) ON DELETE CASCADE,
                            userid BIGINT REFERENCES users(userid) ON DELETE CASCADE,
                            datanow TIMESTAMP DEFAULT now(),
                            per_minutes BIGINT,
                            PRIMARY KEY (groupid, userid)
                        );
                    """)

    except Exception as e:
        logging.error(f'"init_db error": {e}')