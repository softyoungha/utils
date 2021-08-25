class ScheduleNotFoundError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f'스케쥴을 찾을 수 없습니다: {self.msg}'


class TableNotDefinedError(Exception):
    def __init__(self, table_name):
        self.table_name = table_name

    def __str__(self):
        return f'테이블이 없습니다: {self.table_name}'


class IterationError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg