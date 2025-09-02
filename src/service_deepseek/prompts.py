

def realtime_summary(
    user_answer: str,
    target: str = "you're a voice sales consultant who sells elephants",
) -> str:
    """каждый запрос и ответ попадает в него последовательно склеиваясь с предудыщими.
    результат надо отправить ллм и запросить суммаризацию в каждый момент времени
    1) ты вставляешь первую реплику
    2) вставляешь вторую
    3) собираешь все реплики в массив, это и есть текст в котором ты ищешь ответы на свои вопросы
    4) делаешь это каждый раз как обновляется текст (добавляется реплика)
    5) вопросы одни и те же
    6) сохраняешь все ответы относительно каждой реплики
    эта таблица есть оценка текущей ситуации на основе ее будут идти развития скриптов общения

    запрашивать мелкие прдложение через промпт
    """
    return f"""{target}. User said {user_answer}, do a summarization of what's been said. don't use extra words and characters: */-#@№$%^&()[]+_"""


def realtime_answer(
    user_answer: str,
    history: list[str],
    target: str = "you're a voice sales consultant who sells elephants",
) -> str:
    """должен быть сконфигурирован относительно текущего саммари, последних N ответов и запросов и первоначальной цели"""
    return f"""{target}. User said {user_answer}, give an answer to this sentence,
    given the history of communication with the user: {history}.use about 30 words.
    don't use extra words and characters: */-#@№$%^&()[]+_"""


def objective_table(user_answer: str, user_questions: list[str]) -> str:
    """сфоримровать знание о вопросе в такблиу - это собрать все запросы и ответы и представить в виде таблицы ключ-значение.
    делает это ллм
    На самом деле ты должен написать промт так что бы он по тексту он собрал ответы на вопросы в виде таблицы. Вопросы создаются до старта
    Таблица собирается каждый раз после каждого оьновления чата со стороны коиента на основе всей истории"""
    return f"""User said {user_answer}, list of questions: {user_questions},
    find the answers to the array of questions in the words said by the user,
    if there is no answer to the question, write None,
    separating the answers with $ sign, without spaces."""


def initial_target(target: str = "You need to sell an elephant to a client") -> None:
    """
    создать цель всего разговора.
    в рамках которого будет действовать бот.
    должен добавляться к каждому запросу в ллм по теме следующего вопроса к человеку
    """
