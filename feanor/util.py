
def to_string_list(iterable):
    """Utility function to produce a string like: "'A', 'B', 'C'" from ['B', 'A', 'C'].

        >>> to_string_list(['B', 'A', 'C'])
        "'A', 'B', 'C'"

    """
    return ', '.join(map(repr, sorted(iterable)))