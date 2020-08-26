from aiogram import Bot

from .config import groups_col, users_col


async def check_group_and_user(chat_id, user_id):
    bot = Bot.get_current()
    user = users_col.find_one({'user_id': user_id})
    if not user:
        users_col.insert_one({'user_id': user_id,
                              'years': 100,
                              'games_finished': 0,
                              'loses': 0})
    grp = await bot.get_chat(chat_id)
    if grp.type == 'private':
        return
    group = groups_col.find_one({'group_id': chat_id})
    if not group:
        groups_col.insert_one({'group_id': chat_id,
                               'users': [user_id]})
        group = groups_col.find_one({'group_id': chat_id})
    if user_id not in group['users']:
        groups_col.update_one({'group_id': chat_id},
                              {'$push': {'users': user_id}})