from vk_bot import VkBot
from vk_api.longpoll import VkEventType

bot = VkBot()

for event in bot.talk.longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:
            if not bot.user.is_defined(event.user_id):
                bot.set_user(event.user_id)
            bot.write_reply(event.text)




