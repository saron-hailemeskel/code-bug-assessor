def process_numbers(numbers):
    results = []

    for number in numbers:
        if number > 0:
            results.append(number * 2)
        elif number < 0:
            results.append(abs(number))
        else:
            results.append(0)

    return results