from typing import Optional


class Figure:
    def __init__(self,
                 idx: Optional[str] = None,
                 label: Optional[str] = None,
                 caption: Optional[str] = None):

        self._id = idx
        self._label = label
        self._caption = caption

    @property
    def id(self):
        return self._id

    @property
    def label(self):
        return self._label if self._label is not None else ''

    @property
    def caption(self):
        return self._caption if self._caption is not None else ''

    @property
    def text(self):
        return self.__str__()

    @id.setter
    def id(self, idx):
        self._id = idx

    @label.setter
    def label(self, label):
        self._label = label

    @caption.setter
    def caption(self, caption):
        self._caption = caption

    def __str__(self):
        if self.label:
            return f"{self.label}. {self.caption}"
        else:
            return self.caption

    def __repr__(self):
        return self.__str__()
