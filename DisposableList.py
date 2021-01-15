from Utility import Utility


class DisposableList(list):
    def __init__(self, *args, **kwargs):
        super(DisposableList, self).__init__(args)

    def __enter__(self):
        return self

    def __exit__(self, ex_type, ex_value, ex_traceback):
        for element in self:
            # As per my comment on AmazonBuyer, I'm not sure about garbage collector scenarios.
            with element:
                pass
