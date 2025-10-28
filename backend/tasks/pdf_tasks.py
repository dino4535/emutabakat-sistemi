"""
PDF Generation Tasks (Async)
"""
from celery import Task
from backend.celery_app import celery_app
from backend.database import get_db
from backend.models import Mutabakat, User
from backend.utils.pdf_service import create_mutabakat_pdf
from backend.utils.pdf_signer import pdf_signer
from backend.utils.pdf_permissions import apply_pdf_permissions
import os


class CallbackTask(Task):
    """Task with callbacks"""
    def on_success(self, retval, task_id, args, kwargs):
        """Task başarılı olduğunda"""
        print(f"Task {task_id} başarılı: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Task başarısız olduğunda"""
        print(f"Task {task_id} başarısız: {exc}")


@celery_app.task(base=CallbackTask, bind=True, name="backend.tasks.pdf_tasks.generate_mutabakat_pdf")
def generate_mutabakat_pdf(self, mutabakat_id: int) -> dict:
    """
    Mutabakat PDF'ini oluştur (async)
    
    Args:
        mutabakat_id: Mutabakat ID
    
    Returns:
        dict: {"status": "success", "pdf_path": "...", "task_id": "..."}
    """
    db = next(get_db())
    
    try:
        # Progress güncelle
        self.update_state(state="PROGRESS", meta={"current": 10, "total": 100, "status": "PDF oluşturuluyor..."})
        
        # Mutabakatı getir
        mutabakat = db.query(Mutabakat).filter(Mutabakat.id == mutabakat_id).first()
        if not mutabakat:
            raise ValueError(f"Mutabakat bulunamadı: {mutabakat_id}")
        
        # Company bilgilerini al
        company = mutabakat.company
        if not company:
            raise ValueError(f"Şirket bulunamadı: {mutabakat.company_id}")
        
        self.update_state(state="PROGRESS", meta={"current": 30, "total": 100, "status": "PDF rendering..."})
        
        # PDF oluştur
        pdf_filename = f"mutabakat_{mutabakat.mutabakat_no}.pdf"
        pdf_path = os.path.join("pdfs", pdf_filename)
        
        # Ensure directory exists
        os.makedirs("pdfs", exist_ok=True)
        
        # Create PDF
        create_mutabakat_pdf(mutabakat, pdf_path, db)
        
        self.update_state(state="PROGRESS", meta={"current": 60, "total": 100, "status": "Dijital imza ekleniyor..."})
        
        # Dijital imza ekle
        if company.certificate_path and os.path.exists(company.certificate_path):
            signed_path = pdf_path.replace(".pdf", "_signed.pdf")
            pdf_signer.sign_pdf(
                pdf_path,
                signed_path,
                company.certificate_path,
                company.certificate_password,
                company.company_name
            )
            os.remove(pdf_path)  # Unsigned PDF'i sil
            pdf_path = signed_path
        
        self.update_state(state="PROGRESS", meta={"current": 80, "total": 100, "status": "PDF izinleri ayarlanıyor..."})
        
        # PDF permissions
        final_path = pdf_path.replace("_signed.pdf", "_final.pdf") if "_signed" in pdf_path else pdf_path.replace(".pdf", "_final.pdf")
        apply_pdf_permissions(
            pdf_path,
            final_path,
            allow_print=True,
            allow_modify=False,
            allow_copy=False,
            allow_annotations=False
        )
        
        if final_path != pdf_path:
            os.remove(pdf_path)
            pdf_path = final_path
        
        # Database'i güncelle
        mutabakat.pdf_file_path = pdf_path
        db.commit()
        
        self.update_state(state="PROGRESS", meta={"current": 100, "total": 100, "status": "Tamamlandı!"})
        
        return {
            "status": "success",
            "pdf_path": pdf_path,
            "task_id": self.request.id,
            "mutabakat_id": mutabakat_id
        }
        
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="backend.tasks.pdf_tasks.generate_bulk_pdfs")
def generate_bulk_pdfs(mutabakat_ids: list) -> dict:
    """
    Toplu PDF oluşturma
    
    Args:
        mutabakat_ids: Mutabakat ID listesi
    
    Returns:
        dict: {"total": 10, "success": 9, "failed": 1, "results": [...]}
    """
    results = []
    success_count = 0
    failed_count = 0
    
    for mutabakat_id in mutabakat_ids:
        try:
            result = generate_mutabakat_pdf(mutabakat_id)
            results.append(result)
            success_count += 1
        except Exception as e:
            results.append({
                "status": "failed",
                "mutabakat_id": mutabakat_id,
                "error": str(e)
            })
            failed_count += 1
    
    return {
        "total": len(mutabakat_ids),
        "success": success_count,
        "failed": failed_count,
        "results": results
    }

