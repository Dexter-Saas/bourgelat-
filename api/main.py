from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.video.processor import analyze_frames
from core.video.sampler import extract_frames
from core.triage.engine import triage
from core.rag.retriever import retrieve
from data.db.models import init_db, HealthRecord, Animal
from datetime import datetime
import uuid, os, tempfile

load_dotenv()
app = FastAPI(title="Bourgelat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def root():
    return {"status": "Bourgelat is running"}

@app.post("/analyze")
async def analyze(
    video: UploadFile = File(...),
    animal_id: str = Form(...),
    farmer_phone: str = Form(...)
):
    session = init_db()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(await video.read())
        tmp_path = tmp.name

    frames = extract_frames(tmp_path)
    os.unlink(tmp_path)

    if not frames:
        return {"error": "Could not extract frames from video"}

    analysis = await analyze_frames(frames)
    triage_result = triage(
        confidence=analysis.get("confidence", 0),
        severity_score=analysis.get("severity_score", 0)
    )

    rag_context = retrieve(
        " ".join(analysis.get("conditions", [])),
        topic="diseases"
    )

    record = HealthRecord(
        id=str(uuid.uuid4()),
        animal_id=animal_id,
        bcs_score=analysis.get("bcs_score"),
        diagnosis=str(analysis.get("conditions")),
        severity=triage_result["level"],
        treatment=rag_context,
        confidence=analysis.get("confidence"),
        created_at=datetime.utcnow()
    )
    session.add(record)
    session.commit()

    return {
        "analysis": analysis,
        "triage": triage_result,
        "treatment_context": rag_context,
        "disclaimer": "This is decision support only. Always consult a licensed veterinarian."
    }

@app.get("/animal/{animal_id}/records")
def get_records(animal_id: str):
    session = init_db()
    records = session.query(HealthRecord).filter_by(animal_id=animal_id).all()
    return [{
        "id": r.id,
        "bcs_score": r.bcs_score,
        "diagnosis": r.diagnosis,
        "severity": r.severity,
        "treatment": r.treatment,
        "confidence": r.confidence,
        "created_at": str(r.created_at)
    } for r in records]