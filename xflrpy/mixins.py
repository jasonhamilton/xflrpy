from abc import ABC, abstractmethod

class MsgpackMixin:
    def __repr__(self):
        from pprint import pformat
        return "<" + type(self).__name__ + "> " + pformat(vars(self), indent=4, width=1)
    def to_msgpack(self, *args, **kwargs):
        return self.__dict__
    @classmethod
    def from_msgpack(cls, encoded, client = None):
        if client is not None:
            obj = cls(client)
        else:
            obj=cls()
        # obj.__dict__ = {k.decode('utf-8'): (v.__class__.from_msgpack(v.__class__, v) if hasattr(v, "__dict__") else v) for k, v in encoded.items()}
        obj.__dict__.update({ k : (v if not isinstance(v, dict) else getattr(getattr(obj, k).__class__, "from_msgpack")(v)) for k, v in encoded.items()})
        #return cls(**msgpack.unpack(encoded))
        return obj


class DictListInterface(ABC):
    """
    Adds a series of methods that creates an interface that behaves like both an unmutable list and unmutable dict
    by implementing the _get_items() method in an inherited class.

    Act like a List:
        [i for i in items]
        len(items)
        items.to_list()
        items[1]

    Act like a dict
        'itemname' in items
        items['itemname']
        items.to_dict()

    """
    def __len__(self):
        return len(self.to_dict().items())

    def __iter__(self):
        self._index = 0
        return self

    def __next__(self):
        if self._index < len(self.to_list()):
            value = self.to_list()[self._index]
            self._index += 1
            return value
        else:
            raise StopIteration
    
    def __getitem__(self, key):
        if type(key) == int:
            return self.to_list()[key]
        return self.to_dict()[key]

    def __call__(self):
        return self.to_list()

    def __contains__(self, name):
        if name in self.to_dict().keys():
            return True
        return False
    
    def to_list(self) -> list:
        return list(self.to_dict().values())

    def to_dict(self) -> dict:
        return self._get_items()
    
    @abstractmethod
    def _get_items(self) -> dict:
        print("_get_items needs to be implemented and return a dict with managed data")

