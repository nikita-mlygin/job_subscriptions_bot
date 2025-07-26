from aiogram.fsm.state import StatesGroup, State

class SubscriptionForm(StatesGroup):
    """
    Класс состояний для формы оформления подписки.
    Используется aiogram FSM (Finite State Machine) для поэтапного
    взаимодействия с пользователем при заполнении подписки.
    
    Состояния:
    keywords — ожидание ввода ключевых слов для подписки;
    level — ожидание выбора уровня вакансий (junior, middle, senior);
    area — ожидание выбора региона/города;
    frequency — ожидание выбора частоты рассылки (daily, weekly);
    confirm — ожидание подтверждения данных подписки.
    """
    keywords = State()    # пользователь вводит ключевые слова для вакансий
    level = State()       # выбор уровня вакансий (junior, middle, senior)
    area = State()        # выбор региона / города для поиска вакансий
    frequency = State()   # выбор частоты рассылки: ежедневно или еженедельно
    confirm = State()     # подтверждение всех введённых данных и сохранение


class PylintStates(StatesGroup):
    """
    Класс состояний для проверки Python-кода с помощью pylint.
    Используется для поэтапного диалога с пользователем:
    бот ожидает, когда пользователь пришлёт код для анализа.
    """
    waiting_for_code = State()  # состояние ожидания кода Python от пользователя
