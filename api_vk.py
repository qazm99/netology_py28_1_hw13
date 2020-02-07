import json
import time
from collections import Counter
from datetime import datetime
from pprint import pprint

import requests

import token_vk
from qazm import posintput


# https://vk.com/eshmargunov id (171691064)

# При создании экземпляра задаем первый обязательный параметр id: int либо screen_name: string
# Второй параметр не обязательный автосинхронизация с сервером ВК при создании класса тип bool
# Далее не обязательные параметры с ключами first_name last_name screen_name у всех тип string
class User_vk:
    # если передали какойнибудь идентефикатор пользователя - то создаем экземпляр
    def __new__(cls, *args, **kwargs):
        for number, argument in enumerate(args):
            if (number == 0) and (isinstance(argument, int) or isinstance(argument, str)):
                return super().__new__(cls)

    def __init__(self, *args, **kwargs):
        self.id = None
        self.screen_name = None
        self.user_data_update = None
        self.first_name = None
        self.last_name = None

        for iteration, argument in enumerate(args):
            # первый параметр id или screen_name
            if iteration == 0:
                # если что-то похоже на id
                if isinstance(argument, int):
                    self.id = argument
                # если что то похоже на имя
                elif isinstance(argument, str):
                    self.screen_name = argument
                # если есть аргументы с ключами - пишем атрибуты пользователя и метку обновления данных
                for key, key_argument in kwargs.items():
                    if isinstance(key_argument, str):
                        if key == 'screen_name':
                            self.screen_name = key_argument
                        elif key == 'first_name':
                            self.first_name = key_argument
                        elif key == 'last_name':
                            self.last_name = key_argument
                    elif isinstance(key_argument, datetime):
                        self.user_data_update = key_argument
            # если есть второй параметр - автосинхронизация True
            elif iteration == 1:
                if isinstance(argument, bool) and argument:
                    # пробуем взять данные пользователя с сайта ВК
                    try:
                        if self.id is not None:
                            new_user_data = get_user_data(self.id)
                        else:
                            new_user_data = get_user_data(self.screen_name)
                        if new_user_data:
                            # print(new_user_data)
                            self.id = new_user_data[0]['id']
                            self.screen_name = new_user_data[0]['screen_name']
                            self.first_name = new_user_data[0]['first_name']
                            self.last_name = new_user_data[0]['last_name']
                            self.user_data_update = datetime.now()
                    except Exception as exc:
                        print(f'Не удалось синхронизировать пользователя {self.id} {self.screen_name}: {exc}')


# передаем метод и параметры запроса к апи ВК
def requests_vk(method, params):
    url = 'https://api.vk.com/method/'
    params['access_token'] = token_vk.token_vk
    params['v'] = '5.103'
    # если не получаем какой-нибудь ответ делаем 10 попыток
    for number_try in range(10):
        try:
            result_request = requests.get(url + method, params)
            if (result_request.json().get('error') is not None) and result_request.json()['error']['error_code'] == 6:
                print('Превышено число запросов, ждем')
                time.sleep(1.1)
            elif result_request.status_code == 200:
                return result_request.json()
            elif result_request.status_code == 404:
                print(f'Неудачная попытка соединения: {result_request.status_code}')
            else:
                print(f'Неудачная попытка соединения: {result_request.status_code}-{result_request.text}')
        except Exception as exc:
            print(f'Не удалось получить ответ на запрос от сайта: {exc}')


# запрашиваем данные пользователей
def get_user_data(user_id):
    user_id_param = ''
    if isinstance(user_id, list):
        user_id_param = ', '.join(user_id)
    elif isinstance(user_id, str) or isinstance(user_id, int):
        user_id_param = user_id
    try:
        return requests_vk('users.get', params={'user_ids': user_id_param, 'fields': 'screen_name'})['response']
    except Exception as exc:
        print(f'Не удалось получить данные пользователя {user_id_param}: {exc}')


# ищем всех друзей пользователя
def get_all_friends(user_id):
    return requests_vk('friends.get', params={'user_id': user_id})['response']['items']


# по списку id пользователей найдем все ихние группы, если id один - можно передать просто int или strQ
def get_list_groups_on_id(user_id):
    if isinstance(user_id, int):
        try:
            result_request = requests_vk('groups.get', params={'user_id': user_id})
            if result_request.get("response") is not None:
                return result_request['response']['items']
            else:
                if result_request.get('error') is not None:
                    return result_request['error']['error_code']
        except Exception as exc:
            print(f'Не удалось получить группы по id пользователя: {exc}')
            return None
    else:
        print('Поиск групп осуществляется только по integer')


# Получаем инфу о группах
def get_group_data(group_id):
    if isinstance(group_id, list) or isinstance(group_id, set):
        group_ids = ','.join(list(map(str, group_id)))
    elif isinstance(group_id, str) or isinstance(group_id, int):
        group_ids = group_id
    result_request = requests_vk('groups.getById', params={'group_ids': group_ids, 'fields': 'members_count'})
    return result_request


# сохраняем словарь в json
def save_dict_json(dict_in, filename):
    with open(filename, "w") as file:
        json.dump(dict_in, file)


# долгий поиск путем отдельного запроса по каждому пользователю,
# на вход принимаем список пользователей на выходе полный список групп
def find_all_group_all_friends_list(all_friends_ids_list):
    friends_all_group_list = []
    count_friends = len(all_friends_ids_list)
    for num_friend, friend_id in enumerate(all_friends_ids_list):
        status_bar = ('█' * int(100 / count_friends * num_friend)) + str(int(100 / count_friends * num_friend)) + '%'
        print(status_bar)
        recived_data = False
        while not recived_data:
            friend_group = get_list_groups_on_id(friend_id)
            if isinstance(friend_group, list):
                friends_all_group_list.extend(friend_group)
                recived_data = True
            elif friend_group in (7, 18):
                print(f'Не удалось получить доступ к группам пользователя {friend_id}')
                recived_data = True
            else:
                print('Ждем')
                time.sleep(2)
    return friends_all_group_list


# быстрый поиск, в каждный запрос отсылаем по 25 пользователей
# на входе список пользователей на выходе полный список всех групп
def find_all_group_all_friends_list_25(all_friends_ids_list):
    friends_all_group_list = []
    all_friends_ids_25 = [all_friends_ids_list[d:d + 25] for d in range(0, len(all_friends_ids_list), 25)]
    count_friends = len(all_friends_ids_25)
    for num_friend, friend_ids_25 in enumerate(all_friends_ids_25):
        status_bar = ('█' * int(100 / count_friends * num_friend)) + str(int(100 / count_friends * num_friend)) + '%'
        print(status_bar)
        string_api_execute = 'return ['
        for friend_id_in_25 in friend_ids_25:
            string_api_execute += 'API.groups.get({"user_id":' + str(friend_id_in_25) + '}), '
        string_api_execute = string_api_execute[:len(string_api_execute) - 2] + '];'
        result_current_25 = requests_vk('execute', params={'code': string_api_execute})
        for user_friend_group in result_current_25['response']:
            if isinstance(user_friend_group, dict):
                friends_all_group_list.extend(user_friend_group['items'])
    return friends_all_group_list


# Находим "личные группы" на вход подаем словарь:
# ключ-группа, значение-сколько друзей в группе,
# Так же передаем сколько друзей допустимо в "личных группах"
# на выходе множество "личных групп"
def find_secret_groups(friends_all_group_dict, number_friends_in_group):
    secret_groups = set()
    for group in group_target_user:
        if (friends_all_group_dict.get(group) is None) or \
                (friends_all_group_dict.get(group) is not None
                 and friends_all_group_dict.get(group) <= number_friends_in_group):
            secret_groups.add(group)
    return secret_groups


# из сведений о группах вытаскиваем только нужные
def get_need_data_groups(groups_data):
    group_data_list = []
    for group_data in groups_data.get('response'):
        group_data_list.append({'name': group_data.get('name'), 'gid': group_data.get('id'),
                                'members_count': group_data.get('members_count')})
    return group_data_list


if __name__ == '__main__':
    while True:
        print('Сейчас будем пробовать искать "личные" группы в ВК у Евгения, или еще у кого нибудь.')
        number_friends_in_group_main = posintput('Сколько друзей допускается найти в "личных" группах пользователя?')
        find_speed = input('Медленно(0) поищем или быстро(1)?(1/0): ')
        if input('Вы хотите сами ввести пользователя для поиска "личных" групп?(да/нет)').lower() == 'да':
            try:
                user_target = User_vk(input('Введите ид или имя пользователя: '), True)
            except Exception as e:
                print(f'Некорректные данные пользователя: {e}')
        else:
            print('Тогда используем Евгения')
            user_target = User_vk(171691064, True)
        try:
            all_friends_ids = get_all_friends(user_target.id)
            print(f'Нашли все ИД друзей {user_target.first_name} {user_target.last_name}')
            print(f'Нашли все ИД групп {user_target.first_name} {user_target.last_name}:')
            group_target_user = set(get_list_groups_on_id(user_target.id))
            print(group_target_user)
            print('Приступаем к поиску всех групп друзей')
            if find_speed != '0':
                friends_all_group_list_main = find_all_group_all_friends_list_25(all_friends_ids)
            else:
                friends_all_group_list_main = find_all_group_all_friends_list(all_friends_ids)
            # создаем словарь в котором видно сколько друзей есть в каждой группе
            friends_all_group_dict_main = (Counter(friends_all_group_list_main))
            # находим группы в которых нет друзей, либо есть ограниченное число друзей
            groups_data_main = get_group_data(
                find_secret_groups(friends_all_group_dict_main, number_friends_in_group_main))

            # получили необходимые данные о целевых группах и сохранили в файл
            group_dict = {'data': get_need_data_groups(groups_data_main)}
            save_dict_json(group_dict, 'groups.json')
            # файлик прочитали для наглядности
            with open('groups.json', "rb") as json_file:
                print('Вот что мы сохранили в файл с "личными" группами:')
                pprint(json.load(json_file))
        except Exception as e:
            print(f'Что то пошло не так: {e}')
        if input('Попробуем еще разок?(да/нет)').lower() != 'да':
            break
    print('Работа программы завершена')
