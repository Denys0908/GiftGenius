from pydantic import BaseModel


class PydanticBaseModel(BaseModel):
    """
    Базовий клас усіх DTO-схем проєкту (ЛР-2, Рисунок 3.2).
    Успадковує методи model_validate() та model_dump() із pydantic.BaseModel.
    """
    pass