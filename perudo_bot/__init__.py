import logging

from aiogram import executor

from .config import dp


def main():
    logging.basicConfig(level=logging.INFO)
    from . import handlers
    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    main()
