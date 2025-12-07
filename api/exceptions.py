class ApiException(Exception):
    pass



class Unauthorized(ApiException):
    pass


class PotatNoResult(ApiException):
    pass