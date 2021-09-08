import ipdb
import re
import operator
import copy
from math import floor
from random import randint
import numpy as np

PATTERN_BASE_ROLL = r"([+-])? ?(\d+)?[dD](\d+)"
PATTERN_ROLL_OPTIONS = r"!(?:[<>=]?\d+)?|[kd][hl]?\d*|ro?(?:[<>=]?\d+)?"
PATTERN_MODIFIER = r" ?([+\-/*]) ?(\d*\.?\d+)"

class InfinityRolls(Exception):
    pass

def parse_base_roll(roll, option):
    match_roll = re.match(PATTERN_BASE_ROLL, roll)
    dice_operand = match_roll.group(1)
    if not dice_operand:
        dice_operand = "+"
    dice_num = match_roll.group(2)
    if not dice_num:
        dice_num = 1
    else:
        dice_num = int(dice_num)
    dice_type = int(match_roll.group(3))
    if dice_type < 1:
        raise ValueError()
    dice_results = [randint(1, dice_type) for n in range(dice_num)]

    ev_list, txt_list = evaluate_roll_options(dice_results, dice_type, option)

    ev_str = "+".join(str(x) for x in ev_list)
    to_be_evaluated = dice_operand + "(" + ev_str + ")"

    formatted_text_list = []
    for val in txt_list:
        s = re.search("\d+", val)
        num = s.group(0)
        n_start = s.span()[0]
        n_end = s.span()[1]
        if int(num) == 1:
            val = f"{val[:n_start]}<i>{num}</i>{val[n_end:]}"
            n_start += 3
            n_end += 3
        if int(num) == dice_type:
            val = f"{val[:n_start]}<b>{num}</b>{val[n_end:]}"
            n_start += 3
            n_end += 3
        formatted_text_list.append(val)
    formatted_text_str = "+".join(x for x in formatted_text_list)
    text_result = f"{dice_operand}({formatted_text_str})"

    return to_be_evaluated, text_result


def parse_modifiers(modifiers):
    if not modifiers:
        modifiers = ""
    ev_str = modifiers.replace(" ", "")
    res_str = ev_str
    return ev_str, res_str


def explode(dice_results, dice_type, option):
    new_results = []
    txt_results = []

    if dice_type == 1:
        raise InfinityRolls()

    if option == "!":
        option = f"!={dice_type}"
    elif re.match(r"!\d+", option):
        option = f"!={option[1:]}"

    func_comp, value_comp = get_comparison_function(option)

    for result in dice_results:
        new_results.append(result)
        if func_comp(result, value_comp):
            txt_results.append(f"<u>{result}</u>")
        else:
            txt_results.append(str(result))
        while func_comp(result, value_comp):
            result = randint(1, dice_type)
            new_results.append(result)
            if func_comp(result, value_comp):
                txt_results.append(f"<u>{result}</u>")
            else:
                txt_results.append(str(result))

    return new_results, txt_results


def get_comparison_function(option):
    symbol = option[1]
    value = int(option[2:])
    if symbol == "=":
        func = operator.eq
    elif symbol == ">":
        func = operator.ge
    elif symbol == "<":
        func = operator.le
    return func, value


def check_if_infinity_reroll(option, value, dice_type):
    symbol = option[1]
    if symbol in [">","="]  and value <= 1:
        return True
    elif symbol in ["<","="] and value >= dice_type:
        return True
    return False


def get_keep_drop_values(option):
    match = re.match(r"([kd])([hl])?(\d*)", option)
    action = match.group(1)
    if match.group(2):
        type = match.group(2)
    elif action == 'k':
        type = 'h'
    elif action == 'd':
        type = 'l'
    if match.group(3):
        number = int(match.group(3))
    else:
        number = 1
    return action, type, number


def keep_drop(dice_results, option):
    action, type, number = get_keep_drop_values(option)
    arr = np.array(dice_results)
    sort_idx = arr.argsort()
    txt_results = []
    if type == "h":
        idx = sort_idx[-number:][::-1]
    elif type == "l":
        idx = sort_idx[:number]
    if action == "k":
        for dice_idx, val in enumerate(dice_results):
            if dice_idx in idx:
                result = arr[idx]
                txt_results.append(str(val))
            else:
                txt_results.append(f"<s>{val}</s>")
    else:
        for dice_idx, val in enumerate(dice_results):
            if dice_idx not in idx:
                result = arr[idx]
                txt_results.append(str(val))
            else:
                txt_results.append(f"<s>{val}</s>")
    return result, txt_results


def reroll(dice_results, dice_type, option):
    txt_results = []
    new_results = []

    only_once = False
    if len(option) > 1 and option[1] == "o":
        only_once = True
        option = option.replace("o", "")

    if option == "r":
        option = "r=1"
    elif re.match(r"r\d+", option):
        option = f"r={option[1:]}"

    func_comp, value_comp = get_comparison_function(option)

    if check_if_infinity_reroll(option, value_comp, dice_type):
        raise InfinityRolls()

    for result in dice_results:
        if func_comp(result, value_comp):
            txt_results.append(f"<s>{result}</s>")
        else:
            txt_results.append(str(result))
        while func_comp(result, value_comp):
            result = randint(1, dice_type)
            if only_once:
                txt_results.append(result)
                break
            else:
                if func_comp(result, value_comp):
                    txt_results.append(f"<s>{result}</s>")
                else:
                    txt_results.append(str(result))
        new_results.append(result)

    return new_results, txt_results


def evaluate_roll_options(dice_results, dice_type, option):
    if not option:
        txt_string = [str(x) for x in dice_results]
        evaluation_string = txt_string
        return evaluation_string, txt_string
    elif option.startswith("!"):
        return explode(dice_results, dice_type, option)
    elif option.startswith("k") or option.startswith("d"):
        return keep_drop(dice_results, option)
    elif option.startswith("r"):
        return reroll(dice_results, dice_type, option)


def parse_roll(text):
    # ipdb.set_trace()
    new_text = text.strip()
    tot_ev_str = ""
    tot_res_str = ""
    full_pattern = f"(?P<roll>{PATTERN_BASE_ROLL})(?P<opt>{PATTERN_ROLL_OPTIONS})?(?P<mod>(?:{PATTERN_MODIFIER})*)(?![dD])"
    m_roll = re.match(full_pattern, new_text)
    if not m_roll:
        raise ValueError()
    while m_roll:
        ev_str, res_str = parse_base_roll(m_roll.group("roll"), m_roll.group("opt"))
        mod_ev_str, mod_res_str = parse_modifiers(m_roll.group("mod"))
        tot_ev_str += ev_str + mod_ev_str
        tot_res_str += res_str + mod_res_str

        new_text = new_text[m_roll.span()[1]:].strip()
        m_roll = re.match(full_pattern, new_text)

    result = eval(tot_ev_str)

    # roll description
    description = new_text

    return result, tot_res_str, description


def evaluate_roll(dice_num, dice_type, modifiers):
    dice_results = [randint(1, dice_type) for n in range(dice_num)]
    result = sum(dice_results)
    roll_string = f"{dice_num}d{dice_type}"
    for operation, value in modifiers:
        roll_string += f"{operation}{value:%g}"
        if operation == '+':
            result += value
        elif operation == '-':
            result -= value
        elif operation == '/':
            result = floor(result/value)
        elif operation == "*":
            result = floor(result*value)
    return roll_string, dice_results, result
