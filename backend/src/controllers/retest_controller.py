from src.services import retest_service as service
def records(db,note_id):return service.list_records(db,note_id)
def submit(db,note_id,data,user):return service.submit_retests(db,note_id,data,user)
def analyses(db,note_id):return service.list_analyses(db,note_id)
def analyze(db,note_id,user):return service.create_analysis(db,note_id,user)
def export(db,note_id,version):return service.export_analysis(db,note_id,version)
