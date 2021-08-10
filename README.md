# Решение [курсового задания](https://github.com/netology-code/py-advanced-diplom/tree/new_diplom) по курсу Advanced Python
## Описание работы программы
1. За основу бота был взят ранее написанны бот с машинным обучением [ml_bot](https://github.com/headsoft-mikhail/adpy_qualification/blob/master/ml_bot/ml_bot.py). Словарь бота и прописанные сценарии задаются в  [bot_config.py](https://github.com/headsoft-mikhail/adpy_qualification/blob/master/ml_bot/bot_config.py), а класс сценариев описан в файле [questions_sequence.py](https://github.com/headsoft-mikhail/adpy_qualification/blob/master/ml_bot/questions_sequence.py). Сответствующие файлы помещены в пакет ml_bot. Бот умеет рассказывать анекдоты, интересные факты и др.
2. При создании объекта класса VkBot(), создаются объекты, используемые для запросов в вк, для отправки сообщений, и создаются таблицы базы данных.
3. При отправке сообщения боту, он сперва идентифицирует пользователя и получает информацию о нем.
4. Если сообщение соответствует входу в поиск пар, то сначала пользователь попадет в сценарий определения настроек поиска: задаст начальный и конечный возраст, использовать ли при расчете "коэффициента" соответствия интересы, музыкальные предпочтения, любимые книги и фильмы.
5. Далее пользователь попадет в сценарий ввода недостающих данных, если они не указаны на странице пользователя, или скрыты (возраст, пол, город, интересы). Бот спросит только нужные данные: если к примеру в настройках поиска было выбрано не использовать музыкальные предпочтения для поиска пар, ввод музыкальных предпочтений будет пропущен. 
6. Для ввода ответов вида да/нет (булевых) сделана клавиатура с соответствующими кнопками. Если в каких-то ответах ввод будет некорректным, применятся значения по умолчанию.
7. После ввода всех данных, происходит поиск людей  вконтакте по заданным фильтрам. 
   В качестве города был выбран родной город (hometown), т.к. если у пльзователя будет скрыт или не указан город в разделе контактов, то ему придется вводить город не строкой, а его id (потому что параметр  city принимает id города). А id города гарантированно можно узнать только выкачав все города командой getCityById, и сколько нужно id проверить - неизвестно (пердположительно - более 10000), т.к. города получали id не по порядку, и много пустых id. В итоге в результатах поиска по какой-то причине попадаются люди, у которых все равно другой city, также как и при поиске по hometown. Поэтому было принято решение искать по hometown. В итоге при оценке совместимости несоответствие города будет большим минусом и такие результаты опустятся вниз списка.
6. После поиска данных пользователей, происходит поиск их лучших фото и далее все данные пользователей записываются в базу данных. Для каждого пользователя рассчитывается совместимость. Поиск фото можно было бы сделать и после определения лучших кандидатов, и искать фото только для них (что уменьшит число запросов и объем БД), но такой выбор  был сделан в пользу более полной базы.
7. При рассчете совместимости учитывается разница в возрасте, количество совпадений в интересах с разными весовыми коэффициентами, совпадение города, и на всякий случай - пол.
8. Далее записи сортируются по убыванию совместимости, пользователям, попавшим в выдачу устанавливается значение столбца viewed - True, и они не попадут в выдачу при повторном поиске с теми же параметрами.
9. Ссылки на профили наиболее подходящих пар отправляются пользователю с прикрепленными фото.
10. Для добавления в БД еще кандидатов можно отправить боту "еще"
11. Запрос, приводящий бота в  topic 'show_db', выведет следующих по совместимости кандидатов.
12. При запуске повторного поиска с новыми параметрами, таблицы базы данных очищаются, но данные самого пользователя заново вводить не придется, а только настроить параметры поиска.
13. Токены хранятся в отдельном файле - tokens.py
## Итоги
1. Программа декомпозирована на функции/классы/модули/пакеты.
1. Результат программы записывается в БД.
1. Люди не повторяются при повторном поиске с теми же параметрами.
1. Для работы с vk использована библиотека vk_api
1. Недостающая информация запрашивается у пользователя
1. Похожие интересы учитываются при оценке совместимости, с помощью разбиения текста по запятым (т.к. в этих разделах идет перечисление интерсов, книг и т.д.) и поиска совпадений. 
1. У каждого критерия - свои веса. Город, пол и возраст учитываются еще при поиске  в ВК, но проверяются и учитываются еще раз при расчете совместимости.
