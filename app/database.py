import re
from sqlalchemy.orm import DeclarativeBase, declared_attr

class Base(DeclarativeBase):

    @declared_attr.directive
    def __tablename__(cls) -> str:
        # add underscore between each word
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', cls.__name__)

        # add plural form
        if name.endswith('y'):
            name = name[:-1] + 'ies'
        elif not name.endswith('s'):
            name = name + 's'

        return name
