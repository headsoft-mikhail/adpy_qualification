import vk_api
from vk_api.longpoll import VkLongPoll
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from ml_bot.ml_bot import MLBot
from random import randrange

def message_parameters(user_id, message, keyboard=None, attachments=None):
    params_dict = {'user_id': user_id,
                   'message': message,
                   'random_id': randrange(10 ** 7)}
    if attachments:
        params_dict['attachment'] = attachments
    if keyboard:
        params_dict['keyboard'] = keyboard
    return params_dict


class Vk(vk_api.VkApi):
    def __init__(self, token):
        self.vk = vk_api.VkApi(token=token)


class VkSearch(Vk):
    def __init__(self, token=None):
        if token is not None:
            super().__init__(token)
        self.search_offset = 0
        self.single_search = 25

    def update_token(self, token):
        super().__init__(token)

    def get_user_data(self, user_id):
        return self.vk.method('users.get',
                              {'user_ids': user_id,
                               'fields': 'sex,city,books,movies,music,interests,bdate'})[0]

    def get_user_photos(self, user_id, count):
        photo_urls = {}
        for photo in self.vk.method('photos.get',
                                    {
                                        'owner_id': user_id,
                                        'album_id': 'profile',
                                        'extended': 1})['items']:
            # выбираем максимальный размер из доступных
            for size_type in ["w", "z", "y", "r", "q", "p", "o", "x", "m", "s"]:
                if size_type in [size_variant["type"] for size_variant in photo["sizes"]]:
                    max_size_type = size_type
                    break
            for size_variant in photo["sizes"]:
                if size_variant["type"] == max_size_type:
                    # добавляем фото с уникальными url в словарь
                    if size_variant["url"] not in photo_urls:
                        photo_urls[size_variant["url"]] = \
                            {"owner_id": photo["owner_id"],
                             "id": photo["id"],
                             "popularity": photo["likes"]["count"] + photo["comments"]["count"]}
                    else:
                        # если фото с одинаковыми url получены несколько раз, суммируем популярность
                        if photo["id"] != photo_urls[size_variant["url"]]["id"]:
                            photo_urls[size_variant["url"]]["popularity"] += photo["likes"]["count"] + \
                                                                             photo["comments"]["count"]
        best_list = [(photo_url,
                      photo_urls[photo_url]['popularity'],
                      photo_urls[photo_url]['id'],
                      photo_urls[photo_url]['owner_id'])
                     for photo_url in photo_urls]
        return [{'url': item[0], 'attachment': f'photo{item[3]}_{item[2]}'}
                for item in sorted(best_list, key=lambda x: x[1], reverse=True)[:count]]

    def find_people(self, city, sex, age_from, age_to, fields):
        try:
            age_from = int(age_from)
        except ValueError:
            age_from = 0
        try:
            age_to = int(age_to)
        except ValueError:
            age_to = 99
        parameters = {'sort': 0,
                      'count': self.single_search,
                      'status': 6,
                      'age_from': age_from,
                      'age_to': age_to,
                      'hometown': city,
                      'offset': self.search_offset,
                      'fields': f'{fields}'}
        if sex > 0:
            parameters.update({'sex': 3 - sex})
        self.search_offset += self.single_search
        return self.vk.method('users.search', parameters)['items']


class VkTalk(Vk):
    def __init__(self, token):
        super().__init__(token)
        self.longpoll = VkLongPoll(self.vk)
        self.ml_bot = MLBot()
        self.keyboard_enabled = False

    def send(self, user_id, message):
        self.vk.method('messages.send', message_parameters(user_id, message))

    def create_yn_menu(self, user_id, message):
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button(label='Да', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button(label='Нет', color=VkKeyboardColor.NEGATIVE)
        self.vk.method('messages.send', message_parameters(user_id, message, keyboard=keyboard.get_keyboard()))

    def send_photos(self, user_id, message, photos_list):
        attachment = ','.join([photo['attachment'] for photo in photos_list])
        self.vk.method('messages.send', message_parameters(user_id, message, attachments=attachment))

    def write_reply(self, user_id, request):
        answer = self.ml_bot.get_answer(request)
        if self.keyboard_enabled:
            self.send(user_id, answer)
        else:
            self.create_yn_menu(user_id, answer)
        return answer
