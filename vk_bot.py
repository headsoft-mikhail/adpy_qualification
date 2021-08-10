import tokens
import person
from vk_classes import VkTalk, VkSearch
import db


class VkBot:
    def __init__(self):
        self.talk = VkTalk(tokens.vk_group_token)
        self.search = VkSearch(tokens.vk_user_token)
        self.user = person.Person()
        self.search_parameters = {'fields': '',
                                  'age_from': 0,
                                  'age_to': 99,
                                  'music': False,
                                  'books': False,
                                  'movies': False,
                                  'interests': False}
        self.db = db.DataBase('candidates', tokens.db_password)
        self.db.create_tables()

    def set_user(self, user_id):
        self.db.clear()
        self.user = person.Person()
        self.get_user_data(user_id)

    def get_user_data(self, user_id):
        self.user.from_dict(self.search.get_user_data(user_id))

    def get_user_photos(self, user_id):
        return self.search.get_user_photos(user_id, 3)

    def write_reply(self, request):
        answer = self.talk.write_reply(self.user.id, request)  # определение ответа и темы разговора (вне сценария)
        if self.talk.ml_bot.topic == 'show_db':
            self.send_best_candidates()  # показываем кандидатов из бд
        elif self.talk.ml_bot.topic == self.talk.ml_bot.scenarios[0].exit_topic:  # закончили вводить параметры поиска
            self.db.clear()  # очистка БД, т.к. это новый поиск
            self.update_question_ignore_list()  # определение недостающих данных
            self.talk.write_reply(self.user.id, answer)  # ответ пользователю
        elif self.talk.ml_bot.topic == self.talk.ml_bot.scenarios[1].exit_topic:  # закончили ввод недостающих данных
            self.save_missing_user_data()  # сохраняем данные пользователя, введенные вручную
            self.db.add_person(self.user,
                               list(self.search_parameters.keys())[3:],
                               self.user.id, viewed=True)  # сохраняем данные пользователя в БД
            self.save_search_parameters()  # сохраняем все параметры поиска
            self.talk.write_reply(self.user.id, answer)  # ответ пользователю
            self.talk.ml_bot.topic == 'search_complete'
        if self.talk.ml_bot.topic == 'search_complete':  # добавление кандидатов с теми же параметрами поиска
            self.find_candidates()  # поиск кандидатов
            self.send_best_candidates()  # выдача трех наиболее подходящих в чат

    def send_best_candidates(self):
        # отправка наиболее подходящих кандидатов в сообщении
        best_candidates = self.db.get_best(3)
        for candidate in best_candidates:
            self.talk.send_photos(self.user.id, candidate.covered_link(), candidate.photos)

    def find_candidates(self):
        # поиск кандидатов, получение их данных и фото
        for candidate in self.search.find_people(
                self.user.data['city'],
                self.user.data['sex'],
                self.search_parameters['age_from'],
                self.search_parameters['age_to'],
                self.search_parameters['fields']):
            new_candidate = person.Person()
            new_candidate.from_dict(candidate)

            if ('is_closed' in candidate.keys()) and not candidate['is_closed']:
                new_candidate.photos = self.get_user_photos(new_candidate.id)
            # сохраняем в БД всех кандидатов
            self.db.add_person(new_candidate, list(self.search_parameters.keys())[3:], self.user.id)

    def save_search_parameters(self):
        # сохраняем выбранные параметры поиска
        for topic in self.search_parameters:
            for question in self.talk.ml_bot.scenarios[0].questions:
                if question['topic'] == topic:
                    self.search_parameters[topic] = question['answer']
        self.search_parameters['fields'] = ','.join({item['topic']
                                                     for item in self.talk.ml_bot.scenarios[0].questions
                                                     if item['answer'] is True}.union({'sex', 'city', 'bdate'}))

    def save_missing_user_data(self):
        # сохраняем данные пользователя, введенные вручную
        for item in self.talk.ml_bot.scenarios[1].questions:
            if item['topic'] in self.user.data.keys():
                if (self.user.data[item['topic']] is None) \
                        or (self.user.data[item['topic']] == ''):
                    self.user.data[item['topic']] = item['answer']

    def update_question_ignore_list(self):
        # после получения параметров поиска добавляем ненужные вопросы о пользователе в игнор-лист
        # если параметр не будет учитываться при выборе пар
        for item in self.talk.ml_bot.scenarios[0].questions:
            if item['answer'] is False:
                self.talk.ml_bot.scenarios[1].ignore_list.append(item['topic'])
        # если параметр получен с помощью users.get
        for item in self.talk.ml_bot.scenarios[1].questions:
            if item['topic'] in self.user.data.keys():
                if (self.user.data[item['topic']] is not None) \
                        and (self.user.data[item['topic']] != ''):
                    self.talk.ml_bot.scenarios[1].ignore_list.append(item['topic'])
