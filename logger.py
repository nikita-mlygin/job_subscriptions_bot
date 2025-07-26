import logging

# создаём логгер с именем "job_bot"
logger = logging.getLogger("job_bot")

# устанавливаем уровень логирования на INFO — будет выводить info, warning, error, critical
logger.setLevel(logging.INFO)

# проверяем, есть ли уже добавленные обработчики (handler)
# чтобы не дублировать вывод, если скрипт импортируется несколько раз
if not logger.hasHandlers():
    # создаём обработчик, который выводит логи в стандартный поток вывода (консоль)
    handler = logging.StreamHandler()

    # задаём формат сообщений лога: время, уровень, имя логгера и текст сообщения
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        "%Y-%m-%d %H:%M:%S"  # формат даты и времени для %(asctime)s
    )
    # применяем форматтер к обработчику
    handler.setFormatter(formatter)

    # добавляем обработчик к логгеру
    logger.addHandler(handler)
