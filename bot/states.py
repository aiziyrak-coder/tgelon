from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    waiting_phone = State()
    waiting_name = State()


class AnnouncementStates(StatesGroup):
    choosing_type = State()
    waiting_name = State()
    waiting_route_from = State()
    waiting_route_to = State()
    waiting_departure = State()
    waiting_price = State()
    waiting_phone = State()
    waiting_extra = State()
    waiting_text = State()
    waiting_photo = State()
    waiting_custom_interval = State()
    confirming = State()
    editing_text = State()
    editing_photo = State()


class CollectionStates(StatesGroup):
    waiting_name = State()


class ScheduleStates(StatesGroup):
    waiting_custom_interval = State()
    waiting_edit_interval = State()


class AdminStates(StatesGroup):
    waiting_broadcast = State()
