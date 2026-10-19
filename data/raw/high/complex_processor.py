def process_data(items, limit, strict, reverse, multiplier):
    results = []

    try:
        for item in items:
            if item is not None:
                if isinstance(item, (int, float)):
                    if item > limit and strict:
                        results.append(item * multiplier)
                    elif item < limit and not strict:
                        results.append(item / multiplier)
                    else:
                        if reverse:
                            results.insert(0, item)
                        else:
                            results.append(item)
                else:
                    if strict:
                        raise ValueError("Invalid item")
                    else:
                        continue

    except ValueError:
        return []

    return results