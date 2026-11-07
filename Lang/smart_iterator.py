
from collections.abc import Iterator, MutableSequence
from typing import Generic, TypeVar

T = TypeVar("T")


class IterationController(Generic[T]):
    """
    Controls the operation performed on the currently iterated element.

    By default, the current element is retained. The controller allows
    explicitly retaining, disposing of, or replacing the current element.
    """

    def __init__(self, iterable: MutableSequence[T], index: int) -> None:
        """
        Initializes an iteration controller.

        :param iterable: Mutable sequence containing the iterated elements.
        :param index: Index of the currently iterated element.
        """
        self._iterable = iterable
        self._index = index
        self._keep = True

    @property
    def is_kept(self) -> bool:
        """
        Indicates whether the current element should be retained.

        :return: True if the element should be retained, otherwise False.
        """
        return self._keep

    def keep(self) -> None:
        """
        Marks the current element for retention.
        """
        self._keep = True

    def dispose(self) -> None:
        """
        Marks the current element for removal.
        """
        self._keep = False

    def replace(self, value: T) -> None:
        """
        Replaces the current element with a new value.

        Replacement is performed immediately on the original sequence.
        The replacement also marks the element for retention.

        :param value: New value replacing the current element.
        """
        self._iterable[self._index] = value
        self._keep = True


class SmartIterator(Generic[T]):
    """
    Iterates over a mutable sequence while allowing in-place modifications.

    Elements can be retained, removed, or replaced during iteration.
    Structural modifications performed by the iterator are applied
    as the iteration progresses.
    """

    def __init__(self, iterable: MutableSequence[T]) -> None:
        """
        Initializes a SmartIterator.

        :param iterable: Mutable sequence to iterate over and modify.
        """
        self._iterable = iterable

    def __iter__(self) -> Iterator[tuple[IterationController[T], T]]:
        """
        Iterates over the sequence, yielding a controller and its element.

        Each element is initially marked for retention. After the consumer
        finishes processing an element, its controller determines whether
        the element remains in the sequence.

        Removed elements do not advance the iteration index, ensuring
        that subsequent elements are not skipped.

        :return: Iterator yielding (controller, value) pairs.
        """
        index = 0

        while index < len(self._iterable):
            controller = IterationController(self._iterable, index)
            value = self._iterable[index]

            yield controller, value

            if controller.is_kept:
                index += 1
            else:
                del self._iterable[index]
