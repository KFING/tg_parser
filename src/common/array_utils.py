from typing import TypeVar

TR = TypeVar("TR")


def flatten(matrix: list[list[TR]]) -> list[TR]:
    flat_list = []
    for row in matrix:
        flat_list += row
    return flat_list
