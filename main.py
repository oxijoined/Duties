import os
import telebot
import json
from dotenv import load_dotenv

load_dotenv()
admins = [2116186052, 1349414481, 1131940207, 5050639301]
TOKEN = os.getenv("token")
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")


def read_students_from_file():
    with open("students.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def find_min_duties_students(group):
    update_student_ids_by_duties()
    data = read_students_from_file()
    if group == 0:
        students_list = data.keys()
    else:
        students_list = [k for k, v in data.items() if v["group"] == group]

    return sorted(students_list, key=lambda x: data[x]["duties"])[:2]


def update_student_ids_by_duties():
    data = read_students_from_file()
    sorted_students = sorted(data.keys(), key=lambda x: data[x]["duties"])
    for i, student in enumerate(sorted_students, start=1):
        data[student]["id"] = i
    with open("students.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def select_new_duty_student(duty_students, index_to_replace, group=0):
    data = read_students_from_file()
    if group == 0:
        filtered_data = data
    else:
        filtered_data = {k: v for k, v in data.items() if v["group"] == group}

    sorted_students = sorted(filtered_data.keys(), key=lambda x: data[x]["id"])
    current_duty_student = duty_students[index_to_replace]
    current_id = data[current_duty_student]["id"]

    # Находим индекс текущего дежурного в отсортированном списке
    current_index = sorted_students.index(current_duty_student)

    # Если текущий дежурный - последний в списке, выбираем первого
    if current_index == len(sorted_students) - 1:
        new_duty_student = sorted_students[0]
    else:
        new_duty_student = sorted_students[current_index + 1]

    # Убеждаемся, что новый дежурный не совпадает с другим дежурным
    other_duty_student = duty_students[1 - index_to_replace]
    while new_duty_student == other_duty_student:
        current_index = sorted_students.index(new_duty_student)
        if current_index == len(sorted_students) - 1:
            new_duty_student = sorted_students[0]
        else:
            new_duty_student = sorted_students[current_index + 1]

    # Заменяем старого дежурного новым
    duty_students[index_to_replace] = new_duty_student

    return duty_students


def increment_duties(student_name):
    data = read_students_from_file()
    if student_name in data:
        data[student_name]["duties"] += 1

        # Запись обновленных данных в файл
        with open("students.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        print(f"Студент с именем {student_name} не найден в данных")


def create_students_message():
    data = read_students_from_file()
    message_lines = []

    for student_name, student_info in data.items():
        duties_count = student_info["duties"]
        line = f"<code>{student_name}</code> | {duties_count}"
        message_lines.append(line)

    return "\n".join(message_lines)


def set_duties(student_name, duties_count):
    data = read_students_from_file()

    if student_name in data:
        data[student_name]["duties"] = duties_count

        # Запись обновленных данных в файл
        with open("students.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        print(f"Студент с именем {student_name} не найден в данных")

    return data


@bot.message_handler(commands=["set"])
def handle_set_command(message):
    args = message.text.split()

    if len(args) != 3:
        bot.reply_to(
            message, "Неправильный формат команды. Используйте /set ФАМИЛИЯ КОЛИЧЕСТВО"
        )
        return

    _, student_name, duties_str = args

    try:
        duties_count = int(duties_str)
    except ValueError:
        bot.reply_to(message, "Количество дежурств должно быть целым числом.")
        return

    data = set_duties(student_name, duties_count)

    if student_name in data:
        bot.reply_to(
            message,
            f"Количество дежурств для студента {student_name} успешно установлено на {duties_count}.",
        )
    else:
        bot.reply_to(message, f"Студент с именем {student_name} не найден в данных.")


@bot.message_handler(commands=["log"])
def logProcessing(message):
    bot.reply_to(message, create_students_message())


@bot.message_handler(commands=["start"])
def startProcessing(message):
    if message.from_user.id not in admins:
        return bot.reply_to(message, create_students_message())
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(text="Общая", callback_data="choose|0")
    )
    markup.add(
        telebot.types.InlineKeyboardButton(
            text="1 группа", callback_data="choose|1"
        ),
        telebot.types.InlineKeyboardButton(
            text="2 группа", callback_data="choose|2"
        ),
    )
    bot.reply_to(message, "ᅠ", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    call.data = call.data.split("|")
    if call.from_user.id not in admins:
        bot.answer_callback_query(call.id, text="Низя", show_alert=True)
    else:
        if call.data[0] == "choose":
            group = call.data[1]
            markup = telebot.types.InlineKeyboardMarkup()
            choosen = find_min_duties_students(int(call.data[1]))
            first, second = choosen[0], choosen[1]
            markup.add(
                telebot.types.InlineKeyboardButton(
                    text=first,
                    callback_data=f"success|{first}",
                ),
                telebot.types.InlineKeyboardButton(
                    text=second,
                    callback_data=f"success|{second}",
                ),
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    text="♻️", callback_data=f"reroll|{first}|{second}|0|{group}"
                ),
                telebot.types.InlineKeyboardButton(
                    text="♻️", callback_data=f"reroll|{first}|{second}|1|{group}"
                ),
            )
            bot.edit_message_text(
                f"{first} | {second}",
                call.message.chat.id,
                call.message.id,
                reply_markup=markup,
            )
        if call.data[0] == "reroll":
            markup = telebot.types.InlineKeyboardMarkup()
            choosen = select_new_duty_student(
                [call.data[1], call.data[2]], int(call.data[3]), int(call.data[4])
            )
            first, second = choosen[0], choosen[1]
            markup.add(
                telebot.types.InlineKeyboardButton(
                    text=first,
                    callback_data=f"success|{first}",
                ),
                telebot.types.InlineKeyboardButton(
                    text=second,
                    callback_data=f"success|{second}",
                ),
            )
            markup.add(
                telebot.types.InlineKeyboardButton(
                    text="♻️", callback_data=f"reroll|{first}|{second}|0|{call.data[4]}"
                ),
                telebot.types.InlineKeyboardButton(
                    text="♻️", callback_data=f"reroll|{first}|{second}|1|{call.data[4]}"
                ),
            )
            bot.edit_message_text(
                f"{first} | {second}",
                call.message.chat.id,
                call.message.id,
                reply_markup=markup,
            )
        if call.data[0] == "success":
            increment_duties(call.data[1])
            return bot.send_message(call.message.chat.id, f"{call.data[1]} подежурил")


bot.polling()
