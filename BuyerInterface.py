import abc


class BuyerInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'try_authenticate') and
                callable(subclass.try_authenticate) and
                hasattr(subclass, 'try_buy_item') and
                callable(subclass.try_buy_item))
