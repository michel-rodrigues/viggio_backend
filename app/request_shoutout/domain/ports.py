import abc


class ProcessPaymentUnitOfWork(abc.ABC):

    @abc.abstractmethod
    def charge(self, order):
        pass


class DataBaseUnitOfWork(abc.ABC):

    @abc.abstractmethod
    def commit(self):
        pass
