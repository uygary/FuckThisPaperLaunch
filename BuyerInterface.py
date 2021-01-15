import abc


class BuyerInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, 'try_authenticate')
                and callable(subclass.try_authenticate)
                and hasattr(subclass, 'try_buy_item')
                and callable(subclass.try_buy_item)
                and hasattr(subclass, '__del__')
                and callable(subclass.__del__)
                and hasattr(subclass, '__enter__')
                and callable(subclass.__enter__)
                and hasattr(subclass, '__exit__')
                and callable(subclass.__exit__)
                and hasattr(subclass, 'is_authenticated')
                and not callable(subclass.is_authenticated)
                and hasattr(subclass, 'item_counter')
                and not callable(subclass.item_counter)
                and hasattr(subclass, 'max_buy_count')
                and not callable(subclass.max_buy_count)
                and hasattr(subclass, 'item_name')
                and not callable(subclass.item_name))
