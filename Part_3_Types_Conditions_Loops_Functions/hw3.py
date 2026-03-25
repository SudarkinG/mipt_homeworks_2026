#!/usr/bin/env python

UNKNOWN_COMMAND_MSG = "Неизвестная команда!"
NONPOSITIVE_VALUE_MSG = "Значение должно быть больше нуля!"
INCORRECT_DATE_MSG = "Неправильная дата!"
OP_SUCCESS_MSG = "Добавлено"

DATE_PARTS_COUNT = 3
MONTH_MIN = 1
MONTH_MAX = 12
INCOME_ARGS_COUNT = 3
COST_ARGS_COUNT = 4
STATS_ARGS_COUNT = 2
ZERO = float(0)

Request = tuple[str, float, int, int, int]
Date = tuple[int, int, int]


def is_leap_year(year: int) -> bool:
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def extract_date(maybe_dt: str) -> tuple[int, int, int] | None:
    parts = maybe_dt.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None

    if not all(part.isdigit() for part in parts):
        return None

    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])

    if day <= 0 or month < MONTH_MIN or month > MONTH_MAX:
        return None

    if month in (1, 3, 5, 7, 8, 10, 12):
        max_day_value = 31
    elif month in (4, 6, 9, 11):
        max_day_value = 30
    elif is_leap_year(year):
        max_day_value = 29
    else:
        max_day_value = 28

    if day > max_day_value:
        return None

    return (day, month, year)


def parse_amount(amount_str: str) -> float | str:
    if not amount_str:
        return UNKNOWN_COMMAND_MSG
    amount_str = amount_str.replace(",", ".")
    if " " in amount_str:
        return UNKNOWN_COMMAND_MSG
    if amount_str[0] in ".-":
        return UNKNOWN_COMMAND_MSG
    valid = True
    if "." in amount_str:
        if amount_str.count(".") > 1:
            valid = False
        left, right = amount_str.split(".")
        valid = left.isdigit() and right.isdigit()
    else:
        valid = amount_str.isdigit()
    if not valid:
        return UNKNOWN_COMMAND_MSG
    value = float(amount_str)
    return NONPOSITIVE_VALUE_MSG if value <= 0 else value


incomes: list[Request] = []


def income_handler(amount: float, income_date: str) -> str:
    date = extract_date(income_date)
    if date is None:
        return INCORRECT_DATE_MSG
    day, month, year = date
    incomes.append(("", amount, day, month, year))
    return OP_SUCCESS_MSG


def is_valid_category_name(category: str) -> bool:
    return bool(category) and " " not in category and "." not in category and "," not in category


costs: list[Request] = []


def cost_handler(category: str, amount: float, date: str) -> str:
    if amount <= ZERO:
        return NONPOSITIVE_VALUE_MSG
    dt = extract_date(date)
    if dt is None:
        return INCORRECT_DATE_MSG
    if not is_valid_category_name(category):
        return UNKNOWN_COMMAND_MSG
    day, month, year = dt
    costs.append((category, amount, day, month, year))
    return OP_SUCCESS_MSG


def _request_date_leq(request: Request, current_date: Date) -> bool:
    if request[4] != current_date[2]:
        return request[4] < current_date[2]
    if request[3] != current_date[1]:
        return request[3] < current_date[1]
    return request[2] <= current_date[0]


def _request_in_month(request: Request, current_date: Date) -> bool:
    if request[4] != current_date[2]:
        return False
    return request[3] == current_date[1]


def _format_money(value: float) -> str:
    return f"{value:.2f}"


def _format_detail(value: float) -> str:
    rounded = round(value, 2)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.2f}"


def _format_details(details_by_category: dict[str, float]) -> list[str]:
    return [
        f"{idx}. {cat}: {_format_detail(details_by_category[cat])}"
        for idx, cat in enumerate(sorted(details_by_category), start=1)
    ]


def _add_detail(details_by_category: dict[str, float], category: str, amount: float) -> None:
    details_by_category[category] = details_by_category.get(category, ZERO) + amount


def stats_handler(stats_date: str) -> str:
    current_date = extract_date(stats_date)
    if current_date is None:
        return INCORRECT_DATE_MSG

    totals = [ZERO, ZERO, ZERO, ZERO]
    details_by_category: dict[str, float] = {}

    for request in incomes:
        if _request_date_leq(request, current_date):
            totals[0] += request[1]
        if _request_in_month(request, current_date):
            totals[2] += request[1]

    for request in costs:
        if _request_date_leq(request, current_date):
            totals[1] += request[1]
        if _request_in_month(request, current_date):
            totals[3] += request[1]
            _add_detail(details_by_category, request[0], request[1])

    answer = [
        f"Ваша статистика по состоянию на {stats_date}:",
        f"Суммарный капитал: {_format_money(totals[0] - totals[1])} рублей",
    ]
    if totals[2] >= totals[3]:
        answer.append(
            f"B этом месяце прибыль составила {_format_money(totals[2] - totals[3])} рублей",
        )
    else:
        answer.append(
            f"B этом месяце убыток составил {_format_money(totals[3] - totals[2])} рублей",
        )
    answer.append(f"Доходы: {_format_money(totals[2])} рублей")
    answer.append(f"Расходы: {_format_money(totals[3])} рублей")
    answer.append("")
    answer.append("Детализация (категория: сумма):")

    answer.extend(_format_details(details_by_category))
    return "\n".join(answer)


def handle_income(parts: list[str]) -> None:
    if len(parts) != INCOME_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    amount_str, date_str = parts[1], parts[2]
    value = parse_amount(amount_str)
    if isinstance(value, str):
        print(value)
        return
    print(income_handler(value, date_str))


def handle_cost(parts: list[str]) -> None:
    if len(parts) != COST_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    category = parts[1]
    amount_str = parts[2]
    date_str = parts[3]
    value = parse_amount(amount_str)
    if isinstance(value, str):
        print(value)
        return
    print(cost_handler(category, value, date_str))


def handle_stats(parts: list[str]) -> None:
    if len(parts) != STATS_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    date_str = parts[1]
    print(stats_handler(date_str))


def main() -> None:
    handlers = {"income": handle_income, "cost": handle_cost, "stats": handle_stats}

    line = input().strip()
    while line:
        parts = line.split()
        command = parts[0]

        handler = handlers.get(command)
        if handler is None:
            print(UNKNOWN_COMMAND_MSG)
        else:
            handler(parts)

        line = input().strip()


if __name__ == "__main__":
    main()
