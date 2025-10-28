"""
WebSocket Event Definitions
"""
from enum import Enum


class EventType(str, Enum):
    """WebSocket event types"""
    # Mutabakat events
    MUTABAKAT_CREATED = "mutabakat_created"
    MUTABAKAT_SENT = "mutabakat_sent"
    MUTABAKAT_APPROVED = "mutabakat_approved"
    MUTABAKAT_REJECTED = "mutabakat_rejected"
    
    # Notification events
    NEW_NOTIFICATION = "new_notification"
    
    # Task events
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    # System events
    SYSTEM_MESSAGE = "system_message"


def create_event(event_type: EventType, data: dict) -> dict:
    """WebSocket event oluştur"""
    return {
        "type": event_type.value,
        "data": data,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


# Mutabakat events
def mutabakat_created_event(mutabakat_no: str, sender_name: str) -> dict:
    """Yeni mutabakat oluşturuldu"""
    return create_event(EventType.MUTABAKAT_CREATED, {
        "mutabakat_no": mutabakat_no,
        "sender": sender_name,
        "message": f"Yeni mutabakat oluşturuldu: {mutabakat_no}"
    })


def mutabakat_sent_event(mutabakat_no: str, receiver_name: str) -> dict:
    """Mutabakat gönderildi"""
    return create_event(EventType.MUTABAKAT_SENT, {
        "mutabakat_no": mutabakat_no,
        "receiver": receiver_name,
        "message": f"Mutabakat gönderildi: {mutabakat_no}"
    })


def mutabakat_approved_event(mutabakat_no: str, approver_name: str) -> dict:
    """Mutabakat onaylandı"""
    return create_event(EventType.MUTABAKAT_APPROVED, {
        "mutabakat_no": mutabakat_no,
        "approver": approver_name,
        "message": f"✅ Mutabakat onaylandı: {mutabakat_no}"
    })


def mutabakat_rejected_event(mutabakat_no: str, rejector_name: str, reason: str) -> dict:
    """Mutabakat reddedildi"""
    return create_event(EventType.MUTABAKAT_REJECTED, {
        "mutabakat_no": mutabakat_no,
        "rejector": rejector_name,
        "reason": reason,
        "message": f"❌ Mutabakat reddedildi: {mutabakat_no}"
    })


# Task events
def task_progress_event(task_id: str, progress: int, status: str) -> dict:
    """Task progress"""
    return create_event(EventType.TASK_PROGRESS, {
        "task_id": task_id,
        "progress": progress,
        "status": status
    })


def task_completed_event(task_id: str, result: dict) -> dict:
    """Task tamamlandı"""
    return create_event(EventType.TASK_COMPLETED, {
        "task_id": task_id,
        "result": result,
        "message": "İşlem tamamlandı!"
    })


# Notification event
def new_notification_event(title: str, message: str, link: str = None) -> dict:
    """Yeni bildirim"""
    return create_event(EventType.NEW_NOTIFICATION, {
        "title": title,
        "message": message,
        "link": link
    })

