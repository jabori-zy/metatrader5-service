class Mt5Error(Exception):
    def __init__(self, error_code: int, message: str):
        self.error_code = error_code
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message

