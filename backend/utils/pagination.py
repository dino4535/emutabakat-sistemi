# -*- coding: utf-8 -*-
"""
Pagination & Sorting Utilities
"""
from sqlalchemy.orm import Query
from sqlalchemy import asc, desc
from typing import Optional, List, TypeVar, Generic
from pydantic import BaseModel
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Pagination parametreleri"""
    page: int = 1  # Sayfa numarası (1'den başlar)
    page_size: int = 50  # Sayfa başına kayıt sayısı
    order_by: Optional[str] = None  # Sıralama kolonu
    order_direction: str = "desc"  # Sıralama yönü (asc/desc)
    
    class Config:
        from_attributes = True


class PaginationMetadata(BaseModel):
    """Pagination metadata"""
    page: int  # Mevcut sayfa
    page_size: int  # Sayfa başına kayıt
    total_items: int  # Toplam kayıt sayısı
    total_pages: int  # Toplam sayfa sayısı
    has_next: bool  # Sonraki sayfa var mı?
    has_prev: bool  # Önceki sayfa var mı?
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper"""
    items: List[T]  # Sayfa verileri
    metadata: PaginationMetadata  # Pagination metadata
    
    class Config:
        from_attributes = True


class Paginator:
    """
    SQLAlchemy query için pagination ve sorting utility
    
    Kullanım:
        query = db.query(User)
        result = Paginator.paginate(
            query=query,
            page=1,
            page_size=50,
            order_by="created_at",
            order_direction="desc"
        )
    """
    
    # Maksimum sayfa boyutu (DOS koruması)
    MAX_PAGE_SIZE = 200
    
    # Varsayılan sayfa boyutu
    DEFAULT_PAGE_SIZE = 50
    
    @staticmethod
    def paginate(
        query: Query,
        page: int = 1,
        page_size: int = 50,
        order_by: Optional[str] = None,
        order_direction: str = "desc",
        model_class = None
    ) -> dict:
        """
        Query'yi paginate et ve metadata ile birlikte döndür
        
        Args:
            query: SQLAlchemy Query object
            page: Sayfa numarası (1'den başlar)
            page_size: Sayfa başına kayıt sayısı
            order_by: Sıralama kolonu adı (örn: "created_at", "username")
            order_direction: Sıralama yönü ("asc" veya "desc")
            model_class: Model sınıfı (order_by için kolon erişimi)
        
        Returns:
            {
                "items": [...],  # Sayfa verileri
                "metadata": {
                    "page": 1,
                    "page_size": 50,
                    "total_items": 1250,
                    "total_pages": 25,
                    "has_next": True,
                    "has_prev": False
                }
            }
        """
        # Parametreleri validate et
        page = max(1, page)  # En az 1
        page_size = min(max(1, page_size), Paginator.MAX_PAGE_SIZE)  # 1 ile MAX_PAGE_SIZE arası
        
        # Toplam kayıt sayısı
        total_items = query.count()
        
        # Toplam sayfa sayısı
        total_pages = ceil(total_items / page_size) if page_size > 0 else 0
        
        # Sayfa sınırlarını kontrol et
        if page > total_pages and total_pages > 0:
            page = total_pages
        
        # Sorting uygula
        if order_by and model_class:
            try:
                # Model sınıfından kolonu al
                column = getattr(model_class, order_by, None)
                if column is not None:
                    if order_direction.lower() == "asc":
                        query = query.order_by(asc(column))
                    else:
                        query = query.order_by(desc(column))
            except AttributeError:
                # Geçersiz kolon adı, sıralama uygulanmaz
                pass
        
        # Offset ve limit hesapla
        offset = (page - 1) * page_size
        
        # Query'yi uygula
        items = query.offset(offset).limit(page_size).all()
        
        # Metadata oluştur
        metadata = PaginationMetadata(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )
        
        return {
            "items": items,
            "metadata": metadata
        }
    
    @staticmethod
    def get_params_from_request(
        page: Optional[int] = 1,
        page_size: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = "desc"
    ) -> PaginationParams:
        """
        Request parametrelerinden PaginationParams oluştur
        
        Kullanım (FastAPI endpoint):
            @router.get("/users")
            def get_users(
                page: int = 1,
                page_size: int = 50,
                order_by: str = None,
                order_direction: str = "desc"
            ):
                params = Paginator.get_params_from_request(page, page_size, order_by, order_direction)
                result = Paginator.paginate(query, **params.dict())
                ...
        """
        if page_size is None:
            page_size = Paginator.DEFAULT_PAGE_SIZE
        
        return PaginationParams(
            page=page,
            page_size=page_size,
            order_by=order_by,
            order_direction=order_direction
        )


# Sorting için izin verilen kolonlar (güvenlik)
class SortableColumns:
    """
    Her model için sıralanabilir kolonlar
    (SQL injection koruması için whitelist)
    """
    
    USER = [
        "id", "username", "vkn_tckn", "full_name", "email", 
        "phone", "company_name", "role", "is_active", 
        "created_at", "updated_at", "failed_login_count", "last_failed_login"
    ]
    
    MUTABAKAT = [
        "id", "mutabakat_no", "durum", "created_at", "updated_at",
        "donem_baslangic", "donem_bitis", "toplam_borc", "toplam_alacak",
        "bakiye", "onay_tarihi"
    ]
    
    BAYI = [
        "id", "bayi_kodu", "bayi_adi", "bakiye", "donem",
        "son_mutabakat_tarihi", "il", "ilce"
    ]
    
    ACTIVITY_LOG = [
        "id", "action", "created_at", "ip_address", "user_id"
    ]
    
    FAILED_LOGIN_ATTEMPT = [
        "id", "attempted_at", "vkn_tckn", "ip_address", "failure_reason"
    ]
    
    COMPANY = [
        "id", "company_name", "vkn", "created_at", "is_active"
    ]
    
    @staticmethod
    def validate(column: str, allowed_columns: List[str]) -> bool:
        """
        Kolon adının izin verilen listede olup olmadığını kontrol et
        """
        return column in allowed_columns if column else True
    
    @staticmethod
    def get_safe_column(column: Optional[str], allowed_columns: List[str], default: str = "created_at") -> str:
        """
        Güvenli kolon adı döndür (whitelist kontrolü)
        """
        if not column:
            return default
        
        if column in allowed_columns:
            return column
        
        return default

