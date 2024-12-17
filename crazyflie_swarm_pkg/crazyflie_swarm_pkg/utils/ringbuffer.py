import numpy as np

class RingBuffer:

    def __init__(self, size: int, shape: tuple) -> None:
        self.size: int = size
        self.data = np.zeros(shape=(size, *shape), dtype=np.float32)
        self.index: int = 0
        self.__filled = False

    def append(self, elem) -> None:
        if type(elem) != float:
            return
        if np.isnan(elem):
            return
        self.data[self.index] = elem
        self.index = (self.index + 1) % self.size
        if self.index == 0:
            self.__filled = True

    def get_current(self) -> np.ndarray:
        if self.index == 0:
            return self.__getitem__(self.size - 1).squeeze()
        return self.__getitem__(self.index - 1).squeeze()

    def compute_mean(self) -> float:
        if self.__filled:
            return np.mean(self.data)
        return np.mean(self.data[: self.index])

    def __getitem__(self, index) -> np.ndarray:
        return self.data[index]

    def __str__(self):
        return str(self.data)

    def __setitem__(self, index, value):
        self.data[index] = value

    def __len__(self):
        return self.size

    def __iter__(self):
        return iter(self.data)

    @property
    def shape(self):
        return self.data.shape
