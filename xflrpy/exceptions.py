from msgpackrpc.error import TimeoutError   # use RPC Client error

class GenericException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

class InvalidNacaValueError(GenericException):
    pass

class InvalidFoilPathError(GenericException):
    pass

class ClientAlreadyConnectedException(GenericException):
    pass

class ClientNotConnectedException(GenericException):
    pass

class Analysis2dInitializationError(GenericException):
    pass

class AnalysisDoesNotExistError(GenericException):
    pass