from fastapi import APIRouter,Depends
from fastapi.responses import Response
from src.config.database import get_db
from src.utils.auth import current_user,editor
from src.schemas.retest import RetestSubmit,RetestSubmitResult,RetestRecordOut,AnalysisOut
from src.controllers import retest_controller as controller
router=APIRouter(prefix='/notes',tags=['retests'])
@router.get('/{note_id}/retests',response_model=list[RetestRecordOut])
def records(note_id:int,db=Depends(get_db),user=Depends(current_user)):return controller.records(db,note_id)
@router.post('/{note_id}/retests',response_model=RetestSubmitResult,status_code=201)
def submit(note_id:int,data:RetestSubmit,db=Depends(get_db),user=Depends(editor)):return controller.submit(db,note_id,data,user)
@router.get('/{note_id}/analyses',response_model=list[AnalysisOut])
def analyses(note_id:int,db=Depends(get_db),user=Depends(current_user)):return controller.analyses(db,note_id)
@router.post('/{note_id}/analyses',response_model=AnalysisOut,status_code=201)
def analyze(note_id:int,db=Depends(get_db),user=Depends(editor)):return controller.analyze(db,note_id,user)
@router.get('/{note_id}/analyses/{version}/export')
def export(note_id:int,version:int,db=Depends(get_db),user=Depends(current_user)):return Response(controller.export(db,note_id,version),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':f'attachment; filename="retest-analysis-{note_id}-v{version}.csv"'})
