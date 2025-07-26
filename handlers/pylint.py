import subprocess
import tempfile
from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext

from models import PylintStates
from logger import logger  # централизованный логгер приложения

router = Router()

@router.message(F.text == "/pylint")
async def start_pylint(message: types.Message, state: FSMContext):
    """
    Обработчик команды /pylint:
    переводит пользователя в состояние ожидания Python-кода.
    """
    await state.set_state(PylintStates.waiting_for_code)
    logger.debug(f"[Pylint] Пользователь {message.from_user.id} начал проверку кода")
    await message.answer("Отправь, пожалуйста, код Python в следующем сообщении, оформленный как код.")


@router.message(PylintStates.waiting_for_code)
async def check_code(message: types.Message, state: FSMContext):
    """
    Обработчик текста от пользователя в состоянии ожидания кода.
    Извлекает код из сообщения, сохраняет во временный файл, запускает pylint и отправляет результат.
    """
    code = message.text
    user_id = message.from_user.id

    # Проверяем, обёрнут ли код в Markdown-блоки ```...``` и извлекаем содержимое
    if code.startswith("```") and code.endswith("```"):
        # удаляем первую и последнюю строки (```) и соединяем остальные обратно в строку
        code = "\n".join(code.split("\n")[1:-1])

    logger.debug(f"[Pylint] Получен код от пользователя {user_id}:\n{code[:100]}...")  # логируем первые 100 символов

    try:
        # Создаём временный файл с расширением .py (для корректной работы pylint)
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=True) as temp_file:
            temp_file.write(code)    # записываем код в файл
            temp_file.flush()        # принудительно записываем содержимое на диск

            logger.debug(f"[Pylint] Запускаю pylint на временном файле: {temp_file.name}")

            # Запускаем pylint с нужными флагами:
            # --disable=all отключает все проверки
            # --enable=E,F,W,C,R включает ошибки, фатальные, предупреждения, соглашения и рефакторинги
            result = subprocess.run(
                ["pylint", temp_file.name, "--disable=all", "--enable=E,F,W,C,R"],
                stdout=subprocess.PIPE,   # перенаправляем stdout
                stderr=subprocess.PIPE,   # перенаправляем stderr
                text=True,                # получаем вывод в виде строки
                timeout=10                # ограничиваем время выполнения
            )

        # Обрезаем и очищаем вывод от лишнего
        output = result.stdout.strip()

        if not output:
            # Если нет вывода — значит, ошибок не найдено
            await message.answer("Ошибок не найдено! 🎉")
            logger.info(f"[Pylint] У пользователя {user_id} ошибок не найдено")
        else:
            # Если вывод слишком длинный (Telegram ограничивает ~4096 символов), обрезаем до безопасной длины
            if len(output) > 1500:
                output = output[:1500] + "\n\n[вывод обрезан...]"

            # Отправляем результат пользователю как форматированный текст
            await message.answer(f"<pre>{output}</pre>", parse_mode="HTML")
            logger.info(f"[Pylint] У пользователя {user_id} найдены замечания")

    except subprocess.TimeoutExpired:
        # pylint не успел выполниться за отведённое время
        logger.warning(f"[Pylint] Таймаут при проверке кода у пользователя {user_id}")
        await message.answer("Превышено время ожидания анализа. Попробуй сократить код.")
    except Exception as e:
        # Любая другая ошибка — логируем и сообщаем пользователю
        logger.exception(f"[Pylint] Ошибка при запуске анализа у пользователя {user_id}: {e}")
        await message.answer("Произошла ошибка при анализе кода 😢")

    # Завершаем FSM и очищаем состояние
    await state.clear()
