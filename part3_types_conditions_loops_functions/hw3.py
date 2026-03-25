#!/usr/bin/env python

from typing import Any

UNKNOWN_COMMAND_MSG = "Unknown command!"
NONPOSITIVE_VALUE_MSG = "Value must be grater than zero!"
INCORRECT_DATE_MSG = "Invalid date!"
NOT_EXISTS_CATEGORY = "Category not exists!"
OP_SUCCESS_MSG = "Added"

DATE_PARTS_COUNT = 3
MONTH_MIN = 1
MONTH_MAX = 12
INCOME_ARGS_COUNT = 3
COST_ARGS_COUNT = 4
STATS_ARGS_COUNT = 2
COST_CATEGORIES_ARGS_COUNT = 2
MONEY_DECIMALS = 2
CATEGORY_SEPARATOR = "::"
CATEGORY_PARTS = 2
ZERO = float(0)

Date = tuple[int, int, int]

amount_field = "amount"
date_field = "date"
category_field = "category"

EXPENSE_CATEGORIES = {
    "Food": ("Supermarket", "Restaurants", "FastFood", "Coffee", "Delivery"),
    "Transport": ("Taxi", "Public transport", "Gas", "Car service"),
    "Housing": ("Rent", "Utilities", "Repairs", "Furniture"),
    "Health": ("Pharmacy", "Doctors", "Dentist", "Lab tests"),
    "Entertainment": ("Movies", "Concerts", "Games", "Subscriptions"),
    "Clothing": ("Outerwear", "Casual", "Shoes", "Accessories"),
    "Education": ("Courses", "Books", "Tutors"),
    "Communications": ("Mobile", "Internet", "Subscriptions"),
    "Other": ("SomeCategory", "SomeOtherCategory"),
}

financial_transactions_storage: list[dict[str, Any]] = []


def is_leap_year(year: int) -> bool:
    """
    Для заданного года определяет: високосный (True) или невисокосный (False).

    :param int year: Проверяемый год
    :return: Значение високосности.
    :rtype: bool
    """
    if year % 400 == 0:
        return True
    if year % 100 == 0:
        return False
    return year % 4 == 0


def days_in_month(month: int, year: int) -> int:
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    if is_leap_year(year):
        return 29
    return 28


def extract_date(date_string: str) -> Date | None:
    """
    Парсит дату формата DD-MM-YYYY из строки.

    :param str date_string: Проверяемая строка
    :return: typle формата (день, месяц, год) или None, если дата неправильная.
    :rtype: tuple[int, int, int] | None
    """
    parts = date_string.split("-")
    if len(parts) != DATE_PARTS_COUNT:
        return None

    for part in parts:
        if not part.isdigit():
            return None

    day = int(parts[0])
    month = int(parts[1])
    year = int(parts[2])

    if day <= 0 or month < MONTH_MIN or month > MONTH_MAX:
        return None

    max_day_value = days_in_month(month, year)

    if day > max_day_value:
        return None

    return (day, month, year)


def append_failed() -> None:
    financial_transactions_storage.append({})


def entry_date_tuple(entry: dict[str, Any]) -> tuple[int, int, int] | None:
    raw = entry.get(date_field)
    if isinstance(raw, tuple) and len(raw) == DATE_PARTS_COUNT:
        day, month, year = raw
        return (int(year), int(month), int(day))
    if isinstance(raw, str):
        parsed_calendar = extract_date(raw)
        if parsed_calendar is None:
            return None
        day, month, year = parsed_calendar
        return (year, month, day)
    return None


def is_on_or_before_report(
    record_date: tuple[int, int, int],
    report: tuple[int, int, int],
) -> bool:
    return record_date <= report


def row_calendar_date(row: dict[str, Any]) -> Date | None:
    raw = row.get(date_field)
    if isinstance(raw, tuple) and len(raw) == DATE_PARTS_COUNT:
        day, month, year = raw
        return (int(day), int(month), int(year))
    if isinstance(raw, str):
        return extract_date(raw)
    return None


def is_before_or_on(transaction_date: Date, report_date: Date) -> bool:
    if transaction_date[2] != report_date[2]:
        return transaction_date[2] < report_date[2]
    if transaction_date[1] != report_date[1]:
        return transaction_date[1] < report_date[1]
    return transaction_date[0] <= report_date[0]


def is_same_month_year(first_date: Date, second_date: Date) -> bool:
    same_month = first_date[1] == second_date[1]
    same_year = first_date[2] == second_date[2]
    return same_month and same_year


def storage_income_date_amount(row: dict[str, Any]) -> tuple[Date, float] | None:
    if not row or category_field in row:
        return None
    calendar_date = row_calendar_date(row)
    if calendar_date is None:
        return None
    return calendar_date, float(row[amount_field])


def storage_expense_date_amount(row: dict[str, Any]) -> tuple[Date, float] | None:
    if not row or category_field not in row:
        return None
    calendar_date = row_calendar_date(row)
    if calendar_date is None:
        return None
    return calendar_date, float(row[amount_field])


def calculate_income_totals(report_calendar_date: Date) -> tuple[float, float]:
    income_capital = ZERO
    month_income = ZERO
    for row in financial_transactions_storage:
        income_slice = storage_income_date_amount(row)
        if income_slice is None:
            continue
        transaction_date, amount = income_slice
        if is_before_or_on(transaction_date, report_calendar_date):
            income_capital += amount
            if is_same_month_year(transaction_date, report_calendar_date):
                month_income += amount
    return income_capital, month_income


def expense_counts_for_month_stats(transaction_date: Date, report_calendar_date: Date) -> bool:
    if not is_before_or_on(transaction_date, report_calendar_date):
        return False
    return is_same_month_year(transaction_date, report_calendar_date)


def calculate_expense_capital_delta(report_calendar_date: Date) -> float:
    capital = ZERO
    for row in financial_transactions_storage:
        expense_slice = storage_expense_date_amount(row)
        if expense_slice is None:
            continue
        transaction_date, amount = expense_slice
        if is_before_or_on(transaction_date, report_calendar_date):
            capital -= amount
    return capital


def calculate_month_expenses_and_categories(report_calendar_date: Date) -> tuple[float, dict[str, float]]:
    month_expenses = ZERO
    categories: dict[str, float] = {}
    for row in financial_transactions_storage:
        expense_slice = storage_expense_date_amount(row)
        if expense_slice is None:
            continue
        transaction_date, amount = expense_slice
        if not expense_counts_for_month_stats(transaction_date, report_calendar_date):
            continue
        month_expenses += amount
        category_name = str(row["category"])
        categories[category_name] = categories.get(category_name, ZERO) + amount
    return month_expenses, categories


def calculate_expenses_block(report_calendar_date: Date) -> tuple[float, float, dict[str, float]]:
    expense_capital = calculate_expense_capital_delta(report_calendar_date)
    month_expenses, categories = calculate_month_expenses_and_categories(report_calendar_date)
    return expense_capital, month_expenses, categories


def process_transactions(report_calendar_date: Date) -> tuple[float, float, float, dict[str, float]]:
    income_capital, month_income = calculate_income_totals(report_calendar_date)
    expense_capital, month_expenses, categories = calculate_expenses_block(report_calendar_date)
    total_capital = income_capital + expense_capital
    return total_capital, month_income, month_expenses, categories


def income_handler(amount: float, income_date: str) -> str:
    if amount <= 0:
        append_failed()
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        append_failed()
        return INCORRECT_DATE_MSG
    financial_transactions_storage.append({amount_field: amount, date_field: parsed_date})
    return OP_SUCCESS_MSG


def category_is_registered(category_name: str) -> bool:
    pieces = category_name.split(CATEGORY_SEPARATOR)
    if len(pieces) != CATEGORY_PARTS:
        return False
    parent_category, subcategory = pieces
    if not parent_category or not subcategory:
        return False
    if parent_category not in EXPENSE_CATEGORIES:
        return False
    return subcategory in EXPENSE_CATEGORIES[parent_category]


def cost_handler(category_name: str, amount: float, income_date: str) -> str:
    if amount <= 0:
        append_failed()
        return NONPOSITIVE_VALUE_MSG
    parsed_date = extract_date(income_date)
    if parsed_date is None:
        append_failed()
        return INCORRECT_DATE_MSG
    if not category_is_registered(category_name):
        append_failed()
        return NOT_EXISTS_CATEGORY
    financial_transactions_storage.append(
        {category_field: category_name, amount_field: amount, date_field: parsed_date},
    )
    return OP_SUCCESS_MSG


def expense_category_lines() -> list[str]:
    lines: list[str] = []
    for parent_category, subcategories in EXPENSE_CATEGORIES.items():
        for subcategory in subcategories:
            line = f"{parent_category}{CATEGORY_SEPARATOR}{subcategory}"
            lines.append(line)
    return lines


def cost_categories_handler() -> str:
    return "\n".join(expense_category_lines())


def parse_amount(amount_str: str) -> float | str:
    if not amount_str:
        return UNKNOWN_COMMAND_MSG
    normalized = amount_str.replace(",", ".")
    if " " in normalized or normalized[0] in ".-":
        return UNKNOWN_COMMAND_MSG
    valid = False
    if "." in normalized:
        if normalized.count(".") == 1:
            left, right = normalized.split(".")
            valid = left.isdigit() and right.isdigit()
    else:
        valid = normalized.isdigit()
    if not valid:
        return UNKNOWN_COMMAND_MSG
    parsed_number = float(normalized)
    if parsed_number <= 0:
        return NONPOSITIVE_VALUE_MSG
    return parsed_number


def rollup_until_report(report: tuple[int, int, int]) -> tuple[float, float]:
    costs_amount = ZERO
    incomes_amount = ZERO
    for row in financial_transactions_storage:
        record_date = entry_date_tuple(row)
        if record_date is None or not is_on_or_before_report(record_date, report):
            continue
        money = float(row[amount_field])
        if category_field in row:
            costs_amount += money
        else:
            incomes_amount += money
    return costs_amount, incomes_amount


def bump_category(totals: dict[str, float], category: str, amount: float) -> None:
    current = totals.get(category)
    if current is None:
        totals[category] = amount
    else:
        totals[category] = current + amount


def all_cost_category_totals() -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in financial_transactions_storage:
        if category_field not in row:
            continue
        category_name = str(row[category_field])
        bump_category(totals, category_name, float(row[amount_field]))
    return totals


def format_stat_category_details(details_by_category: dict[str, float]) -> list[str]:
    lines: list[str] = []
    for line_index, category_name in enumerate(details_by_category):
        amount = details_by_category[category_name]
        line = f"{line_index}. {category_name}: {amount}"
        lines.append(line)
    return lines


def join_stats_answer(header: list[str], detail_lines: list[str]) -> str:
    answer: list[str] = []
    answer.extend(header)
    answer.extend(detail_lines)
    if len(detail_lines) == 0:
        answer.append("")
    answer.append("")
    return "\n".join(answer)


def format_money_line(value: float) -> str:
    return f"{value:.2f}"


def format_detail_amount(value: float) -> str:
    rounded = round(value, 2)
    if rounded.is_integer():
        return str(int(rounded))
    return f"{rounded:.2f}"


def append_month_profit_or_loss(lines: list[str], month_in: float, month_out: float) -> None:
    if month_in >= month_out:
        month_balance = round(month_in - month_out, MONEY_DECIMALS)
        lines.append(f"This month, the profit amounted to {format_money_line(month_balance)} rubles.")
        return
    month_balance = round(month_out - month_in, MONEY_DECIMALS)
    lines.append(f"This month, the loss amounted to {format_money_line(month_balance)} rubles.")


def stats_text_from_parts(
    report_date: str,
    total_capital: float,
    month_in: float,
    month_out: float,
    details_by_category: dict[str, float],
) -> str:
    lines = [
        f"Your statistics as of {report_date}:",
        f"Total capital: {format_money_line(total_capital)} rubles",
    ]
    append_month_profit_or_loss(lines, month_in, month_out)
    lines.append(f"Income: {format_money_line(month_in)} rubles")
    lines.append(f"Expenses: {format_money_line(month_out)} rubles")
    lines.append("")
    lines.append("Details (category: amount):")
    for line_index, category_name in enumerate(sorted(details_by_category), start=1):
        lines.append(
            f"{line_index}. {category_name}: {format_detail_amount(details_by_category[category_name])}",
        )
    return "\n".join([*lines, ""])


def stats_handler(report_date: str) -> str:
    report_calendar_date = extract_date(report_date)
    if report_calendar_date is None:
        return INCORRECT_DATE_MSG

    total_capital, month_in, month_out, categories = process_transactions(report_calendar_date)
    total_capital = round(total_capital, MONEY_DECIMALS)
    return stats_text_from_parts(
        report_date,
        total_capital,
        month_in,
        month_out,
        categories,
    )


def process_income(args: list[str]) -> None:
    if len(args) != INCOME_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    amount_str = args[1]
    date_str = args[2]
    parsed_amount = parse_amount(amount_str)
    if isinstance(parsed_amount, str):
        print(parsed_amount)
        return
    print(income_handler(parsed_amount, date_str))


def process_cost(args: list[str]) -> None:
    if len(args) == COST_CATEGORIES_ARGS_COUNT and args[1] == "categories":
        print(cost_categories_handler())
        return
    if len(args) != COST_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    category = args[1]
    amount_str = args[2]
    date_str = args[3]
    parsed_amount = parse_amount(amount_str)
    if isinstance(parsed_amount, str):
        print(parsed_amount)
        return
    result = cost_handler(category, parsed_amount, date_str)
    print(result)
    if result == NOT_EXISTS_CATEGORY:
        print(cost_categories_handler())


def process_stats(args: list[str]) -> None:
    if len(args) != STATS_ARGS_COUNT:
        print(UNKNOWN_COMMAND_MSG)
        return
    date_str = args[1]
    print(stats_handler(date_str))


def main() -> None:
    """Ваш код здесь"""
    line = input().strip()
    while line:
        args = line.split()
        command = args[0]
        if command == "income":
            process_income(args)
        elif command == "cost":
            process_cost(args)
        elif command == "stats":
            process_stats(args)
        else:
            print(UNKNOWN_COMMAND_MSG)
        line = input().strip()


if __name__ == "__main__":
    main()
