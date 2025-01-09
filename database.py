import aiosqlite
from datetime import datetime


class Database:
    def __init__(self):
        self.db_name = "tasks.db"

    async def init(self):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task TEXT NOT NULL,
                    created_date TIMESTAMP NOT NULL,
                    importance TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE
                )
            """)
            await db.commit()

    async def add_task(self, task: str, importance: str):
        async with aiosqlite.connect(self.db_name) as db:
            dt_now = datetime.now()
            dt = dt_now.replace(second=0, microsecond=0)
            await db.execute(
                "INSERT INTO tasks (task, created_date, importance) VALUES (?, ?, ?)",
                (task, dt, importance)
            )
            await db.commit()

    async def get_tasks(self, completed=False):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute(
                    "SELECT * FROM tasks WHERE completed = ?", (completed,)
            ) as cursor:
                return await cursor.fetchall()

    async def get_all_tasks(self):
        async with aiosqlite.connect(self.db_name) as db:
            async with db.execute("SELECT * FROM tasks") as cursor:
                return await cursor.fetchall()

    async def complete_task(self, task_id: int):
        async with aiosqlite.connect(self.db_name) as db:
            await db.execute(
                "UPDATE tasks SET completed = TRUE WHERE id = ?",
                (task_id,)
            )
            await db.commit()
