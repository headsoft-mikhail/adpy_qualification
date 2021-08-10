import sqlalchemy
import psycopg2
import person


class DataBase:
    def __init__(self, name, password):
        try:
            self.db = self.open_db(name, password)
        except sqlalchemy.exc.OperationalError:
            self.db = self.create_db(name, password)

    def open_db(self, name, password):
        db_url = f"postgresql+psycopg2://postgres:{password}@localhost:5432/"
        engine = sqlalchemy.create_engine(f"{db_url}{name}")
        connection = engine.connect()
        return connection

    def create_db(self, name, password, default_db_name='postgres'):
        connection = self.open_db(default_db_name, password)
        connection.execute("COMMIT")
        connection.execute(f"CREATE DATABASE {name} WITH OWNER = postgres;")
        connection = self.open_db(name, password)
        return connection

    def create_tables(self):
        self.db.execute("""CREATE TABLE IF NOT EXISTS Persons(
                           Id SERIAL PRIMARY KEY,
                           Name VARCHAR(80) NOT NULL,
                           City VARCHAR(80) NOT NULL,
                           Sex INTEGER CHECK(Sex >= 0 AND Sex <= 2),
                           Age INTEGER CHECK(Age >= 0 AND Age <= 99),
                           Score NUMERIC,
                           Viewed BOOLEAN);""")
        self.create_interests_tables('Music')
        self.create_interests_tables('Movies')
        self.create_interests_tables('Books')
        self.create_interests_tables('Interests')
        self.create_photos_tables()

    def create_interests_tables(self, interest_name):
        self.db.execute(f"""CREATE TABLE IF NOT EXISTS {interest_name}(
                            Id SERIAL PRIMARY KEY,
                            Name VARCHAR(80) NOT NULL UNIQUE);""")
        self.db.execute(f"""CREATE TABLE IF NOT EXISTS Persons{interest_name}(
                            PersonId INTEGER REFERENCES Persons,
                            {interest_name}Id INTEGER REFERENCES {interest_name},
                            CONSTRAINT pk_Person{interest_name} PRIMARY KEY (PersonId, {interest_name}Id));""")

    def create_photos_tables(self):
        self.db.execute(f"""CREATE TABLE IF NOT EXISTS Photos(
                            Id SERIAL PRIMARY KEY,
                            Attachment VARCHAR(80) NOT NULL UNIQUE,
                            Url TEXT NOT NULL UNIQUE);""")
        self.db.execute(f"""CREATE TABLE IF NOT EXISTS PersonsPhotos(
                            PersonId INTEGER REFERENCES Persons,
                            PhotosId INTEGER REFERENCES Photos,
                            CONSTRAINT pk_PersonPhotos PRIMARY KEY (PersonId, PhotosId));""")

    def add_person(self, person, interest_list, user_id, viewed=False):
        city = person.data['city']
        sex = person.data['sex']
        age = person.data['age']
        if city is None:
            city = 'Unknown'
        if sex is None:
            sex = 0
        if age is None:
            age = 0
        self.db.execute(f"""INSERT INTO Persons (name, id, city, sex, age, viewed)
                           VALUES {person.full_name(),
                                    person.id,
                                    city,
                                    sex,
                                    age,
                                    viewed};""")
        for interest_name in interest_list:
            for item in person.data[interest_name].lower().split(','):
                if item.strip() != '':
                    self.add_to_interests_table(interest_name, item.strip().replace("'", "").replace('"', ''), person)
        for photo in person.photos:
            self.add_to_photos(photo, person)
        self.calculate_compatibility(user_id, person, interest_list)

    def add_to_photos(self, photo, person):
        self.db.execute(f"""INSERT INTO Photos (attachment, url) 
                                    VALUES ('{photo['attachment']}','{photo['url']}');""")
        photo_id = self.db.execute(f"SELECT id FROM Photos WHERE attachment = '{photo['attachment']}'").fetchone()[0]
        self.db.execute(f"""INSERT INTO PersonsPhotos (personid, photosid) 
                                    VALUES ({person.id}, {photo_id});""")

    def add_to_interests_table(self, interest_name, item, person):
        try:
            self.db.execute(f"""INSERT INTO {interest_name} (name) 
                                VALUES ('{item}');""")
        except sqlalchemy.exc.IntegrityError:
            pass
        item_id = self.db.execute(f"SELECT id FROM {interest_name} WHERE name = '{item}'").fetchone()[0]
        self.db.execute(f"""INSERT INTO Persons{interest_name} (personid, {interest_name}id) 
                            VALUES ({person.id}, {item_id});""")

    def get_person_params(self, person_id, params_list):
        params = ', '.join(params_list)
        return self.db.execute(f"""SELECT {params}  FROM Persons WHERE Id = {person_id};""").fetchone()

    def calculate_compatibility(self, user_id, person, interest_list):
        score = 0
        coefficients = {'music': 1.1, 'books': 0.7, 'interests': 0.6, 'movies': 0.9}
        for interest in interest_list:
            if interest in coefficients:
                coefficient = coefficients[interest]
            else:
                coefficient = 0.5
            score += self.get_coincidences(person, user_id, interest) * coefficient
        person_age, person_city, person_sex = self.get_person_params(user_id, ['age', 'city', 'sex'])
        # учтем разницу в возрасте
        score -= 0.05 * abs(person.data['age'] - person_age)
        # проверим, что город и пол соответствуют критериям поиска
        # даже если не соответствуют, считаем совместимость, но с большим вычетом
        if person.data['city'] == person_city:
            score += 20
        if person.data['sex'] not in (0, person_sex):
            score += 40
        # на всякий случай проверяем пол
        elif person.data['sex'] == person_sex:
            score -= 40

        self.db.execute(f"""UPDATE Persons 
                            SET score = {score} 
                            WHERE id = {person.id};""")

    def get_coincidences(self, person, user_id, interest):
        user_music_ids = self.db.execute(f"""SELECT {interest}id FROM Persons{interest} 
                                             WHERE PersonId = {user_id};""").fetchall()
        person_music_ids = self.db.execute(f"""SELECT {interest}Id FROM Persons{interest} 
                                               WHERE PersonId = {person.id};""").fetchall()
        return len(set(user_music_ids).intersection(set(person_music_ids)))

    def get_best(self, count):
        persons = []
        best_persons = self.db.execute(f"""SELECT id, name 
                                           FROM Persons 
                                           WHERE viewed = FALSE
                                           ORDER BY score DESC 
                                           LIMIT {count}""").fetchall()
        for item in best_persons:
            best_person = person.Person()
            best_person.id = item[0]
            [best_person.first_name, best_person.last_name] = item[1].split(' ')
            best_person.photos = self.db.execute(f"""SELECT Photos.attachment, Photos.url FROM Photos
                                                     JOIN PersonsPhotos ON PersonsPhotos.photosid = Photos.id
                                                     WHERE PersonsPhotos.personid = {item[0]}""").fetchall()
            persons.append(best_person)
            self.db.execute(f"""UPDATE Persons 
                                SET viewed = TRUE
                                WHERE id = {best_person.id};""")
        return persons

    def clear(self):
        tables = ['PersonsMusic', 'PersonsMovies', 'PersonsInterests', 'PersonsBooks', 'PersonsPhotos',
                  'Music', 'Movies', 'Interests', 'Books', 'Photos', 'Persons']
        for table_name in tables:
            self.db.execute(f"""TRUNCATE TABLE {table_name} CASCADE""")
        print('Таблицы очищены')

    def close(self):
        self.db.close()
