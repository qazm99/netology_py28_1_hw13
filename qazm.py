#собираем библиотеку "удобняков"

import datetime
#Счетчик времени для оценки затрат времени на операции
class date_logger:
    def __init__(self):
        self.date_start = datetime.datetime.now()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.date_stop = datetime.datetime.now()
        print(f"Время старта {self.date_start}")
        print(f"Время окочания {self.date_stop}")
        print(f"Затрачено для вычислений {(self.date_stop - self.date_start).seconds: .0F} секунд")


# Фильтр только целые положительные числа
def posintput(string):
    while True:
        integer = input(string)
        if integer.isdigit():
            return int(integer)
        else:
            print("Нужно ввести целое положительное число")