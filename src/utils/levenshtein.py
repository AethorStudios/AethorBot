def levenshtein_distance(s1: str, s2: str, case_sensitive: bool = False) -> int:
    if s1 is s2 or s1 == s2:
        return 0

    if not case_sensitive:
        s1 = s1.casefold()
        s2 = s2.casefold()
        if s1 == s2:
            return 0

    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1, case_sensitive=True)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


if __name__ == "__main__":
    # Example usage
    items = [
        ["hello", "hallo", False],
        ["hell", "hello", False],
        ["flaw", "lawn", False],
        ["intention", "execution", False],
        ["gumbo", "gambol", False],
        ["book", "back", False],
        ["Python", "python", True],
    ]
    expected_results = [1, 1, 2, 5, 2, 2, 1]
    for index, item in enumerate(items):
        dist = levenshtein_distance(*item)
        if dist != expected_results[index]:
            print(f"Test case {item} failed: expected {expected_results[index]}, got {dist}")
            continue
        print(f"Levenshtein distance between '{item[0]}' and '{item[1]}' is {dist} (PASS)")
