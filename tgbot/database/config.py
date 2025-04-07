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
import logging

async def init_db(pool):
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    userid BIGINT PRIMARY KEY,
                    username TEXT UNIQUE,
                    name TEXT,
                    added_time TIMESTAMP NOT NULL DEFAULT NOW()
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    groupid BIGINT PRIMARY KEY,
                    username TEXT UNIQUE,
                    name TEXT,
                    added_time TIMESTAMP NOT NULL DEFAULT NOW(),
                    creator BIGINT REFERENCES users(userid)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_states (
                    userid BIGINT PRIMARY KEY REFERENCES users(userid) ON DELETE CASCADE,
                    last_group_update BIGINT REFERENCES groups(groupid) ON DELETE SET NULL
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS group_states (
                    groupid BIGINT PRIMARY KEY REFERENCES groups(groupid) ON DELETE CASCADE,
                    bot_status BOOLEAN NOT NULL DEFAULT TRUE -- 1: turn on 0: turn off
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS ban_messages (
                    groupid BIGINT REFERENCES groups(groupid) ON DELETE CASCADE,
                    message_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    added_time TIMESTAMP NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (groupid, message_id, message_type)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS global_ban_messages (
                    message_id TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    added_time TIMESTAMP NOT NULL DEFAULT NOW(),
                    PRIMARY KEY (message_id, message_type)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS global_white_texts (
                    text TEXT NOT NULL,
                    PRIMARY KEY (text)
                );
            """)

            await conn.execute("""
                CREATE TABLE IF NOT EXISTS group_settings (
                    groupid BIGINT REFERENCES groups(groupid) ON DELETE CASCADE,
                    userid BIGINT REFERENCES users(userid) ON DELETE SET NULL, -- км охрги марта настройка кганини сакласе болади
                    nsfw_prots INTEGER DEFAULT 20,
                    photo_with_opencv BOOLEAN DEFAULT TRUE,
                    logs BOOLEAN DEFAULT FALSE,
                    PRIMARY KEY (groupid)
                );
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS privilege (
                    groupid BIGINT REFERENCES groups(groupid) ON DELETE CASCADE,
                    userid BIGINT REFERENCES users(userid) ON DELETE CASCADE,
                    datanow TIMESTAMP DEFAULT NOW(),
                    per_minutes BIGINT,
                    PRIMARY KEY (groupid, userid)
                );
            """)

    except Exception as e:
        logging.error(f'"init_db error": {e}')
