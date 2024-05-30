import asyncio

import csv
import datetime
from pprint import pprint

from loguru import logger
from pydantic import BaseModel

from chat_scanner.config import BASE_DIR
from chat_scanner.db.models import User, Project
from chat_scanner.db.models.project import ProjectSettings


class ModelUser(BaseModel):
    id: int
    username: str|None
    first_name: str
    last_name: str
    balance: int
    subscription_duration_days: int
    created_at: datetime.datetime



async def create_from_csv(session):
    with open(BASE_DIR / r"chat_scanner/utils/users.csv", newline="", encoding="utf8") as file:
        reader = csv.reader(file)
        data = list(reader)
        for row in data[1:]:
            user = ModelUser(
                id=int(row[0]),
                username=row[1] or None,
                first_name=row[2],
                last_name=row[3],
                balance=int(row[4]),
                subscription_duration_days=int(row[5]),
                created_at=datetime.datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S")
            )
            logger.info(user.id)
            db_user = await User.get_or_none(session, id=user.id)
            if not db_user:
                db_user = await User.create(session, **user.dict())
                project = await Project.create(session, user_id=db_user.id, is_general=True)
                await session.flush()
                await ProjectSettings.create(session, project_id=project.id)
                await session.commit()
        # await User.create(**user.dict())

if __name__ == '__main__':
    asyncio.run(create_from_csv())