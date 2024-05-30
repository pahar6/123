from __future__ import annotations

from pyrogram.types import Chat
from sqlalchemy import BigInteger, String, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship

from .project import Project
from ..base import Base


class ProjectChat(Base):
    __tablename__ = 'project_chats'
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sender_projects: Mapped[list[Project]] = relationship(
        back_populates="sender",
        foreign_keys=[Project.sender_id]
    )

    receiver_projects: Mapped[list[Project]] = relationship(
        back_populates="receiver",
        foreign_keys=[Project.receiver_id]
    )

    username: Mapped[str | None] = mapped_column(String(100), index=True)
    title: Mapped[str | None] = mapped_column(String(150))
    type: Mapped[str | None] = mapped_column(String(100))
    topic_id: Mapped[int | None] = mapped_column(Integer, default=None)

    def pretty(self):
        if self.topic_id:
            _id = int(str(self.id)[:-1 * len(str(self.topic_id))])
            return f'{self.title} | @{self.username}/{self.topic_id} | {_id}'
        return f'{self.title} | @{self.username} | {self.id}'


    @classmethod
    async def get_or_create_from_chat(cls, session, chat: Chat, topic_id: int | None):
        chat_id = chat.id
        if topic_id:
            chat_id = int(f"{chat_id}{topic_id}")
        return await cls.get_or_create(
            session,
            defaults=dict(  # defaults
                title=chat.title,
                username=chat.username,
                type=chat.type.value,
            ),
            id=chat_id,  # **kwargs
            topic_id=topic_id  # **kwargs
        )
