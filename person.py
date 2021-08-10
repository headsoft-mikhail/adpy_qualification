from datetime import datetime

class Person:
    def __init__(self):
        self.id = None
        self.first_name = ''
        self.last_name = ''
        self.photos = []
        self.data = {
            'age': None,
            'sex': None,
            'city': None,
            'books': '',
            'interests': '',
            'music': '',
            'movies': ''
        }

    def __str__(self):
        return f'id: {self.id}\n' \
               f'name: {self.full_name()}\n' \
               f'sex: {self.data["sex"]}\n' \
               f'city: {self.data["city"]}\n' \
               f'age: {self.data["age"]}'

    def from_dict(self, user):
        self.id = user['id']
        self.first_name = user['first_name']
        self.last_name = user['last_name']
        param_list = ['city', 'sex', 'books', 'interests', 'music', 'movies']
        for item in param_list:
            if item in user.keys():
                if item == 'city':
                    self.data[item] = user[item]['title']
                else:
                    self.data[item] = user[item]
        if 'bdate' in user.keys() and user['bdate'].count('.') == 2:
            # конвертация bdate в age
            bdate = datetime.strptime(user['bdate'], "%d.%m.%Y")
            today = datetime.now()
            self.data['age'] = today.year - bdate.year - ((today.month, today.day) < (bdate.month, bdate.day))


    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def link(self):
        return f'https://vk.com/id{str(self.id)}'

    def covered_link(self):
        return f'[id{str(self.id)}|{self.full_name()}]'

    def is_defined(self, user_id):
        return self.id == user_id


