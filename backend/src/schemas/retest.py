from pydantic import BaseModel,Field,ConfigDict
from datetime import datetime
from src.constants.enums import MetricCode
class RetestRow(BaseModel):
    sample_code:str=Field(min_length=2,max_length=40,pattern=r'^[A-Za-z0-9_-]+$')
    metric:MetricCode=MetricCode.ABSORPTION
    value:float|None=Field(default=None,allow_inf_nan=False)
    unit:str=Field(min_length=1,max_length=50)
class RetestSubmit(BaseModel):
    batch:str=Field(default='',max_length=100)
    rows:list[RetestRow]=Field(min_length=1,max_length=300)
class RetestRecordOut(BaseModel):
    id:int
    note_id:int
    metric:str
    sample_code:str
    value:float|None
    unit:str
    batch:str
    submitted_by:str
    created_at:datetime
    model_config=ConfigDict(from_attributes=True)
class RetestConflict(BaseModel):
    sample_code:str
    metric:str
    reason:str
class RetestSubmitResult(BaseModel):
    accepted:int
    supplemented:int
    duplicates:int
    conflicts:list[RetestConflict]
class AnalysisOut(BaseModel):
    id:int
    note_id:int
    version:int
    created_by:str
    created_at:datetime
    detail:dict
    model_config=ConfigDict(from_attributes=True)
