class QuestionsSequence:
    def __init__(self, questions, enter_topic, exit_topic):
        self.active = False
        self.enter_topic = enter_topic
        self.exit_topic = exit_topic
        self.questions = questions[:]
        self.topic = None
        self.gen = (item for item in self.questions)
        self.current = None
        self.ignore_list = []
        self.max_ignore_len = len(questions)

    def get_next(self):
        try:
            topic_ignored = True
            while topic_ignored:
                self.current = self.gen.__next__()
                self.topic = self.current['topic']
                topic_ignored = self.topic in self.ignore_list
            return self.current['question']
        except StopIteration:
            self.__init__(self.questions, self.enter_topic, self.exit_topic)
            self.topic = self.exit_topic
            return None

    def save_answer(self, value):
        if self.current:
            if self.current['answer_type'] is bool:
                self.current['answer'] = (value.lower() == 'да')
            elif self.current['answer_type'] is int:
                try:
                    self.current['answer'] = int(value)
                except ValueError:
                    pass
            else:
                if value.lower() == '-':
                    self.current['answer'] = ''
                else:
                    self.current['answer'] = value
