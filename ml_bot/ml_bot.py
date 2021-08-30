import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
import random
from ml_bot.bot_config import BOT_CONFIG, SEARCH_PARAMETERS, USER_MISSING_DATA
from ml_bot.questions_sequence import QuestionsSequence


class MLBot:
    def __init__(self):
        self.topic = None
        self.adding_favourite = False
        self.bot_config = BOT_CONFIG
        self.bot_config['intents'].update(
            {
                'enter_search':
                    {
                        'examples': ['любовь', 'пара', 'знакомство', 'найди пару', 'найди мне пару', 'поиск'],
                        'responses': ['Настроим параметры поиска']
                    },
                'ask_missing_data':
                    {
                        'examples': ['Параметры поиска заданы.'],
                        'responses': ['Для начала поиска не хватает еще кое-чего...']
                    },
                'search_parameters_set':
                    {
                        'examples': [],
                        'responses': ['Параметры поиска заданы.']
                    },
                'missing_data_set':
                    {
                        'examples': [],
                        'responses': ['Чтобы найти еще людей с теми же параметрами поиска, напишите "Ещё". '
                                      'Чтобы перейти к просмотру найденных кандидатов, напишите "Результат"']
                    },
                'search_complete':
                    {
                        'examples': ['Чтобы найти еще людей с теми же параметрами поиска, напишите "Ещё". '
                                     'Чтобы перейти к просмотру найденных кандидатов, напишите "Результат"'],
                        'responses': ['Подождите, идет поиск кандидатов...']
                    },
                'show_db':
                    {
                        'examples': ['Покажи найденные пары', 'Покажи', 'Покажи кандидатов', 'Результат',
                                     'найденные пары', 'кандидаты', 'найденные результаты', 'покажи результаты'],
                        'responses': ['Показываю найденных кандидатов. Их можно добавить в список избранных. '
                                      'Для завершения просмотра напишите "Стоп"']
                    },
                'show_favorites':
                    {
                        'examples': ['Избранное', 'Избранные пары', 'Лучшие пары', 'Лучшее'],
                        'responses': ['Избранные:']
                    },
                'clear_favorites':
                    {
                        'examples': ['Очистить избранное', 'Удалить избранное', 'Очистить', 'Очистить лучшее',
                                     'Удалить сохраненное', 'Очистить сохраненное', 'Удалить'],
                        'responses': ['Избранные пары удалены']
                    }
            })
        self.clf, self.vectorizer = self.ml_train()
        self.scenarios = [QuestionsSequence(SEARCH_PARAMETERS[:], 'enter_search', 'search_parameters_set'),
                          QuestionsSequence(USER_MISSING_DATA[:], 'ask_missing_data', 'missing_data_set')]

    def classify_intent(self, replica):
        # ML
        replica = clear_phrase(replica)
        if replica == '':
            return None
        intent = self.clf.predict(self.vectorizer.transform([replica]))[0]
        # check ML intent
        for example in BOT_CONFIG['intents'][intent]['examples']:
            example = clear_phrase(example)
            if example and nltk.edit_distance(example, replica) / len(example) <= 0.5:
                if intent != 'repeat':
                    return intent
                else:
                    return self.topic

    def get_answer(self, replica):
        scenario_active = any([scenario.active for scenario in self.scenarios])
        if not scenario_active:
            self.topic = self.classify_intent(replica)
            for scenario in self.scenarios:
                scenario.active = (self.topic == scenario.enter_topic)
        for scenario in self.scenarios:
            if scenario.active:
                return self.scenario_step(scenario, replica)
        if self.topic is not None:
            return self.get_answer_by_intent(self.topic)
        else:
            return self.get_failure_phrase()

    def scenario_step(self, scenario, replica):
        scenario.save_answer(replica)
        answer = scenario.get_next()
        self.topic = scenario.topic
        if self.topic == scenario.exit_topic:
            answer = self.get_answer_by_intent(self.topic)
        return answer

    def ml_train(self):
        # подготовка датасета для векторизации и обучения
        x_text = []  # набор строк, в котором будут перечислены все examples из всех intents
        y = []  # набор строк, в котором будут перечислены все intents, соответствующие элементам x_text
        for intent, intent_data in self.bot_config['intents'].items():
            for example in intent_data['examples']:
                x_text.append(example)
                y.append(intent)
        # векторизация
        vectorizer = TfidfVectorizer(ngram_range=(2, 3), analyzer='char')  # задаем векторизатор
        x = vectorizer.fit_transform(x_text)  # преобразует examples в весовые векторы
        # классификация
        clf = LinearSVC()  # задается модель обучения
        clf.fit(x, y)  # обучение
        return clf, vectorizer

    def get_failure_phrase(self):
        return random.choice(self.bot_config['failure_phrases'])

    def get_answer_by_intent(self, intent):
        if intent in self.bot_config['intents']:
            answer = random.choice(self.bot_config['intents'][intent]['responses'])
            return answer


def clear_phrase(phrase):
    phrase = phrase.lower()
    alphabet = '1234567890абвгдеёжзийклмнопрстуфхцчшщъыьэюя- '
    result = ''.join(symbol for symbol in phrase if symbol in alphabet)
    return result.strip()
