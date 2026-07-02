from datetime import timedelta

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.database.models import (
    Announcement,
    Chat,
    ChatCollection,
    CollectionChat,
    PostLog,
    Schedule,
    User,
)
from bot.utils.time import utcnow


class ScheduleExistsError(Exception):
    pass


class OwnershipError(Exception):
    pass


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    full_name: str | None,
) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user:
        changed = user.username != username
        user.username = username
        if not user.is_registered and full_name and not user.full_name:
            user.full_name = full_name
        if changed:
            await session.commit()
            await session.refresh(user)
        return user

    user = User(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        is_registered=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def complete_registration(
    session: AsyncSession, user_id: int, phone: str, full_name: str
) -> User | None:
    user = await get_user_by_id(session, user_id)
    if not user:
        return None
    user.phone = phone
    user.full_name = full_name.strip()[:255]
    user.is_registered = True
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count(User.id)))
    return int(result.scalar_one())


async def list_users_page(session: AsyncSession, page: int = 0, page_size: int = 10) -> tuple[list[User], int]:
    total = await count_users(session)
    result = await session.execute(
        select(User).order_by(User.created_at.desc()).limit(page_size).offset(page * page_size)
    )
    return list(result.scalars().all()), total


async def set_user_blocked(session: AsyncSession, user_id: int, blocked: bool) -> None:
    await session.execute(update(User).where(User.id == user_id).values(is_blocked=blocked))
    if blocked:
        await session.execute(
            update(Schedule).where(Schedule.user_id == user_id).values(is_active=False)
        )
    await session.commit()


# --- Announcements ---


async def create_announcement(
    session: AsyncSession,
    user_id: int,
    name: str,
    text: str,
    photo_file_id: str | None = None,
    phone: str | None = None,
    route_from: str | None = None,
    route_to: str | None = None,
    departure_time: str | None = None,
    price: str | None = None,
    *,
    is_active: bool = False,
) -> Announcement:
    ann = Announcement(
        user_id=user_id,
        name=name,
        text=text,
        photo_file_id=photo_file_id,
        phone=phone,
        route_from=route_from,
        route_to=route_to,
        departure_time=departure_time,
        price=price,
        is_active=is_active,
    )
    session.add(ann)
    await session.commit()
    await session.refresh(ann)
    return ann


async def list_announcements(session: AsyncSession, user_id: int) -> list[Announcement]:
    result = await session.execute(
        select(Announcement)
        .where(Announcement.user_id == user_id)
        .order_by(Announcement.created_at.desc())
    )
    return list(result.scalars().all())


async def get_announcement(session: AsyncSession, user_id: int, ann_id: int) -> Announcement | None:
    result = await session.execute(
        select(Announcement).where(Announcement.id == ann_id, Announcement.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_announcement(
    session: AsyncSession, ann_id: int, user_id: int, **kwargs
) -> Announcement | None:
    ann = await get_announcement(session, user_id, ann_id)
    if not ann:
        return None
    for key, value in kwargs.items():
        if hasattr(ann, key):
            setattr(ann, key, value)
    ann.updated_at = utcnow()
    await session.commit()
    await session.refresh(ann)
    return ann


async def delete_announcement(session: AsyncSession, user_id: int, ann_id: int) -> bool:
    ann = await get_announcement(session, user_id, ann_id)
    if not ann:
        return False
    await session.delete(ann)
    await session.commit()
    return True


async def count_user_schedules_for_announcement(
    session: AsyncSession, user_id: int, ann_id: int
) -> int:
    result = await session.execute(
        select(func.count(Schedule.id)).where(
            Schedule.user_id == user_id, Schedule.announcement_id == ann_id
        )
    )
    return int(result.scalar_one())


# --- Chats ---


async def upsert_chat(
    session: AsyncSession,
    user_id: int,
    chat_id: int,
    title: str,
    chat_type: str,
    bot_is_admin: bool,
    user_is_admin: bool | None = None,
) -> Chat:
    result = await session.execute(
        select(Chat).where(Chat.user_id == user_id, Chat.chat_id == chat_id)
    )
    chat = result.scalar_one_or_none()
    ready = bot_is_admin and (user_is_admin if user_is_admin is not None else False)
    if chat:
        chat.title = title
        chat.chat_type = chat_type
        chat.bot_is_admin = bot_is_admin
        if user_is_admin is not None:
            chat.user_is_admin = user_is_admin
        chat.is_active = ready
    else:
        chat = Chat(
            user_id=user_id,
            chat_id=chat_id,
            title=title,
            chat_type=chat_type,
            bot_is_admin=bot_is_admin,
            user_is_admin=user_is_admin or False,
            is_active=ready,
        )
        session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat


async def update_all_chats_by_telegram_id(
    session: AsyncSession,
    telegram_chat_id: int,
    *,
    bot_is_admin: bool | None = None,
    is_active: bool | None = None,
    title: str | None = None,
) -> int:
    values = {}
    if bot_is_admin is not None:
        values["bot_is_admin"] = bot_is_admin
    if is_active is not None:
        values["is_active"] = is_active
    if title is not None:
        values["title"] = title
    if not values:
        return 0
    result = await session.execute(
        update(Chat).where(Chat.chat_id == telegram_chat_id).values(**values)
    )
    await session.commit()
    return result.rowcount or 0


async def list_chats(session: AsyncSession, user_id: int) -> list[Chat]:
    result = await session.execute(
        select(Chat).where(Chat.user_id == user_id).order_by(Chat.title.asc())
    )
    return list(result.scalars().all())


async def get_chat(session: AsyncSession, user_id: int, chat_db_id: int) -> Chat | None:
    result = await session.execute(
        select(Chat).where(Chat.id == chat_db_id, Chat.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def toggle_chat_active(session: AsyncSession, user_id: int, chat_db_id: int) -> bool | None:
    chat = await get_chat(session, user_id, chat_db_id)
    if not chat:
        return None
    chat.is_active = not chat.is_active
    await session.commit()
    return chat.is_active


async def delete_chat(session: AsyncSession, user_id: int, chat_db_id: int) -> bool:
    chat = await get_chat(session, user_id, chat_db_id)
    if not chat:
        return False
    await session.delete(chat)
    await session.commit()
    return True


# --- Collections ---

DEFAULT_COLLECTION_NAME = "Asosiy guruhlar"


async def ensure_default_collection(session: AsyncSession, user_id: int) -> ChatCollection:
    result = await session.execute(
        select(ChatCollection).where(
            ChatCollection.user_id == user_id,
            ChatCollection.name == DEFAULT_COLLECTION_NAME,
        )
    )
    col = result.scalar_one_or_none()
    if col:
        return col
    col = ChatCollection(user_id=user_id, name=DEFAULT_COLLECTION_NAME)
    session.add(col)
    await session.commit()
    await session.refresh(col)
    return col


async def auto_add_chat_to_default(
    session: AsyncSession, user_id: int, chat_db_id: int
) -> None:
    col = await ensure_default_collection(session, user_id)
    await add_chat_to_collection(session, user_id, col.id, chat_db_id)


async def get_default_collection(
    session: AsyncSession, user_id: int
) -> ChatCollection | None:
    result = await session.execute(
        select(ChatCollection)
        .options(selectinload(ChatCollection.chats).selectinload(CollectionChat.chat))
        .where(
            ChatCollection.user_id == user_id,
            ChatCollection.name == DEFAULT_COLLECTION_NAME,
        )
    )
    return result.scalar_one_or_none()


async def get_user_dashboard(session: AsyncSession, user_id: int) -> dict:
    ann_count = int(
        (
            await session.execute(
                select(func.count(Announcement.id)).where(Announcement.user_id == user_id)
            )
        ).scalar_one()
    )
    chats = await list_chats(session, user_id)
    active_chats = [c for c in chats if c.is_active and c.bot_is_admin and c.user_is_admin]
    schedules = await list_schedules(session, user_id)
    active_sched = [s for s in schedules if s.is_active]
    next_send = None
    if active_sched:
        times = [s.next_send_at for s in active_sched if s.next_send_at]
        if times:
            next_send = min(times)
    last_log = (
        await session.execute(
            select(PostLog)
            .where(PostLog.user_id == user_id)
            .order_by(PostLog.sent_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return {
        "announcements": ann_count,
        "chats_total": len(chats),
        "chats_ready": len(active_chats),
        "schedules_active": len(active_sched),
        "next_send_at": next_send,
        "last_post_ok": last_log.success if last_log else None,
        "last_post_at": last_log.sent_at if last_log else None,
        "ready": ann_count > 0 and len(active_chats) > 0,
    }


async def find_route_duplicate(
    session: AsyncSession, user_id: int, route_from: str, route_to: str
) -> Announcement | None:
    if not route_to.strip():
        return None
    rf, rt = route_from.strip().lower(), route_to.strip().lower()
    anns = await list_announcements(session, user_id)
    for ann in anns:
        if ann.is_active and ann.route_from and ann.route_to:
            if ann.route_from.strip().lower() == rf and ann.route_to.strip().lower() == rt:
                return ann
    return None


async def create_collection(session: AsyncSession, user_id: int, name: str) -> ChatCollection:
    col = ChatCollection(user_id=user_id, name=name)
    session.add(col)
    await session.commit()
    await session.refresh(col)
    return col


async def list_collections(session: AsyncSession, user_id: int) -> list[ChatCollection]:
    result = await session.execute(
        select(ChatCollection)
        .options(selectinload(ChatCollection.chats))
        .where(ChatCollection.user_id == user_id)
        .order_by(ChatCollection.name.asc())
    )
    return list(result.scalars().all())


async def get_collection(
    session: AsyncSession, user_id: int, collection_id: int
) -> ChatCollection | None:
    result = await session.execute(
        select(ChatCollection)
        .options(selectinload(ChatCollection.chats).selectinload(CollectionChat.chat))
        .where(ChatCollection.id == collection_id, ChatCollection.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def delete_collection(session: AsyncSession, user_id: int, collection_id: int) -> bool:
    col = await get_collection(session, user_id, collection_id)
    if not col:
        return False
    await session.delete(col)
    await session.commit()
    return True


async def add_chat_to_collection(
    session: AsyncSession, user_id: int, collection_id: int, chat_db_id: int
) -> bool:
    col = await get_collection(session, user_id, collection_id)
    chat = await get_chat(session, user_id, chat_db_id)
    if not col or not chat or not chat.bot_is_admin or not chat.user_is_admin:
        return False

    existing = await session.execute(
        select(CollectionChat).where(
            CollectionChat.collection_id == collection_id,
            CollectionChat.chat_id == chat_db_id,
        )
    )
    if existing.scalar_one_or_none():
        return True

    session.add(CollectionChat(collection_id=collection_id, chat_id=chat_db_id))
    await session.commit()
    return True


async def remove_chat_from_collection(
    session: AsyncSession, user_id: int, collection_id: int, chat_db_id: int
) -> bool:
    col = await get_collection(session, user_id, collection_id)
    if not col:
        return False
    await session.execute(
        delete(CollectionChat).where(
            CollectionChat.collection_id == collection_id,
            CollectionChat.chat_id == chat_db_id,
        )
    )
    await session.commit()
    return True


async def get_collection_chats(
    session: AsyncSession, user_id: int, collection_id: int
) -> list[Chat]:
    col = await get_collection(session, user_id, collection_id)
    if not col:
        return []
    return [
        link.chat
        for link in col.chats
        if link.chat
        and link.chat.is_active
        and link.chat.bot_is_admin
        and link.chat.user_is_admin
    ]


async def count_ready_collection_chats(
    session: AsyncSession, user_id: int, collection_id: int
) -> int:
    return len(await get_collection_chats(session, user_id, collection_id))


async def count_schedules_for_collection(
    session: AsyncSession, user_id: int, collection_id: int
) -> int:
    result = await session.execute(
        select(func.count(Schedule.id)).where(
            Schedule.user_id == user_id, Schedule.collection_id == collection_id
        )
    )
    return int(result.scalar_one())


# --- Schedules ---


async def create_schedule(
    session: AsyncSession,
    user_id: int,
    announcement_id: int,
    collection_id: int,
    interval_minutes: int,
) -> Schedule:
    ann = await get_announcement(session, user_id, announcement_id)
    col = await get_collection(session, user_id, collection_id)
    if not ann or not col:
        raise OwnershipError("E'lon yoki jamlanma topilmadi")

    if interval_minutes < 1 or interval_minutes > 10080:
        raise ValueError("Interval 1 daqiqadan 7 kungacha bo'lishi kerak")

    now = utcnow()
    schedule = Schedule(
        user_id=user_id,
        announcement_id=announcement_id,
        collection_id=collection_id,
        interval_minutes=interval_minutes,
        next_send_at=now,
    )
    session.add(schedule)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise ScheduleExistsError("Bu e'lon va jamlanma uchun reja allaqachon mavjud")
    await session.refresh(schedule)
    return schedule


async def list_schedules(session: AsyncSession, user_id: int) -> list[Schedule]:
    result = await session.execute(
        select(Schedule)
        .options(
            selectinload(Schedule.announcement),
            selectinload(Schedule.collection),
        )
        .where(Schedule.user_id == user_id)
        .order_by(Schedule.created_at.desc())
    )
    return list(result.scalars().all())


async def get_schedule(session: AsyncSession, user_id: int, schedule_id: int) -> Schedule | None:
    result = await session.execute(
        select(Schedule)
        .options(
            selectinload(Schedule.announcement),
            selectinload(Schedule.collection),
        )
        .where(Schedule.id == schedule_id, Schedule.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_schedule_interval(
    session: AsyncSession, user_id: int, schedule_id: int, interval_minutes: int
) -> Schedule | None:
    sch = await get_schedule(session, user_id, schedule_id)
    if not sch:
        return None
    if interval_minutes < 1 or interval_minutes > 10080:
        raise ValueError("Interval noto'g'ri")
    sch.interval_minutes = interval_minutes
    await session.commit()
    await session.refresh(sch)
    return sch


async def toggle_schedule(session: AsyncSession, user_id: int, schedule_id: int) -> bool | None:
    sch = await get_schedule(session, user_id, schedule_id)
    if not sch:
        return None
    sch.is_active = not sch.is_active
    if sch.is_active and not sch.next_send_at:
        sch.next_send_at = utcnow()
    await session.commit()
    return sch.is_active


async def delete_schedule(session: AsyncSession, user_id: int, schedule_id: int) -> bool:
    sch = await get_schedule(session, user_id, schedule_id)
    if not sch:
        return False
    await session.delete(sch)
    await session.commit()
    return True


async def get_due_schedules(session: AsyncSession, limit: int = 50) -> list[Schedule]:
    now = utcnow()
    result = await session.execute(
        select(Schedule)
        .options(
            selectinload(Schedule.announcement),
            selectinload(Schedule.collection).selectinload(ChatCollection.chats).selectinload(
                CollectionChat.chat
            ),
            selectinload(Schedule.owner),
        )
        .where(Schedule.is_active.is_(True), Schedule.next_send_at <= now)
        .order_by(Schedule.next_send_at.asc())
        .limit(limit)
    )
    return [s for s in result.scalars().all() if s.owner and not s.owner.is_blocked]


async def mark_schedule_sent(session: AsyncSession, schedule_id: int, *, advance: bool) -> None:
    result = await session.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        return
    now = utcnow()
    if advance:
        schedule.last_sent_at = now
        schedule.next_send_at = now + timedelta(minutes=schedule.interval_minutes)
    await session.commit()


async def mark_schedule_attempt(
    session: AsyncSession,
    schedule_id: int,
    *,
    advance: bool,
    pause: bool = False,
    backoff_minutes: int | None = None,
) -> None:
    result = await session.execute(select(Schedule).where(Schedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    if not schedule:
        return
    now = utcnow()
    if pause:
        schedule.is_active = False
    elif advance:
        schedule.last_sent_at = now
        schedule.next_send_at = now + timedelta(minutes=schedule.interval_minutes)
    elif backoff_minutes:
        schedule.next_send_at = now + timedelta(minutes=backoff_minutes)
    else:
        schedule.next_send_at = now + timedelta(minutes=min(schedule.interval_minutes, 15))
    await session.commit()


async def log_posts_batch(
    session: AsyncSession,
    user_id: int,
    schedule_id: int | None,
    entries: list[tuple[int, str | None, bool, str | None]],
) -> None:
    for chat_id, chat_title, success, error_message in entries:
        session.add(
            PostLog(
                user_id=user_id,
                schedule_id=schedule_id,
                chat_id=chat_id,
                chat_title=chat_title,
                success=success,
                error_message=error_message,
            )
        )
    await session.commit()


async def get_user_post_logs(
    session: AsyncSession, user_id: int, limit: int = 20
) -> list[PostLog]:
    result = await session.execute(
        select(PostLog)
        .where(PostLog.user_id == user_id)
        .order_by(PostLog.sent_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_stats(session: AsyncSession) -> dict:
    users = await count_users(session)
    announcements = int(
        (await session.execute(select(func.count(Announcement.id)))).scalar_one()
    )
    chats = int((await session.execute(select(func.count(Chat.id)))).scalar_one())
    schedules = int((await session.execute(select(func.count(Schedule.id)))).scalar_one())
    active_schedules = int(
        (
            await session.execute(
                select(func.count(Schedule.id)).where(Schedule.is_active.is_(True))
            )
        ).scalar_one()
    )
    total_posts = int((await session.execute(select(func.count(PostLog.id)))).scalar_one())
    success_posts = int(
        (
            await session.execute(
                select(func.count(PostLog.id)).where(PostLog.success.is_(True))
            )
        ).scalar_one()
    )
    rate = round(success_posts / total_posts * 100, 1) if total_posts else 100.0
    return {
        "users": users,
        "announcements": announcements,
        "chats": chats,
        "schedules": schedules,
        "active_schedules": active_schedules,
        "total_posts": total_posts,
        "success_rate": rate,
    }
