class AppException(Exception):
    def __init__(self, detail: str, status_code: int = 400, code: str = "bad_request") -> None:
        self.detail = detail
        self.status_code = status_code
        self.code = code
        super().__init__(detail)
