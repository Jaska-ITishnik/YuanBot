from typing import Any, Union, Dict, List

from sqlalchemy import Dialect
from sqlalchemy_file import ImageField


class CustomImageField(ImageField):

    def process_bind_param(self, value: Any, dialect: Dialect) -> Union[None, Dict[str, Any], List[Dict[str, Any]]]:
        data = {
            'telegra_file_id': 'saytdagi linki'
        }
        value.update(data)
        return super().process_bind_param(value, dialect)