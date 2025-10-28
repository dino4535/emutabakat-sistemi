"""
Yetkilendirme sistemi - Multi-Company E-Mutabakat
"""
from backend.models import UserRole

class Permissions:
    """Rol bazlı yetkilendirme (Multi-Company)"""
    
    # Mutabakat oluşturabilenler
    CAN_CREATE_MUTABAKAT = [UserRole.ADMIN, UserRole.COMPANY_ADMIN, UserRole.MUHASEBE, UserRole.PLANLAMA]
    
    # Mutabakat silebilecekler
    CAN_DELETE_MUTABAKAT = [UserRole.ADMIN, UserRole.COMPANY_ADMIN, UserRole.MUHASEBE, UserRole.PLANLAMA]
    
    # Mutabakat gönderebilecekler
    CAN_SEND_MUTABAKAT = [UserRole.ADMIN, UserRole.COMPANY_ADMIN, UserRole.MUHASEBE, UserRole.PLANLAMA]
    
    # Mutabakat onaylayabilecekler (müşteriler ve tedarikçiler)
    CAN_APPROVE_MUTABAKAT = [UserRole.MUSTERI, UserRole.TEDARIKCI]
    
    # Tüm mutabakatları görebilecekler (şirket içi)
    CAN_VIEW_ALL_MUTABAKAT = [UserRole.ADMIN, UserRole.COMPANY_ADMIN]
    
    # Kullanıcı yönetimi yapabilecekler (şirket içi)
    CAN_MANAGE_USERS = [UserRole.ADMIN, UserRole.COMPANY_ADMIN]
    
    # Toplu mutabakat oluşturabilecekler
    CAN_BULK_CREATE = [UserRole.ADMIN, UserRole.COMPANY_ADMIN, UserRole.MUHASEBE, UserRole.PLANLAMA]
    
    @staticmethod
    def can_create_mutabakat(role: UserRole) -> bool:
        """Mutabakat oluşturma yetkisi var mı?"""
        return role in Permissions.CAN_CREATE_MUTABAKAT
    
    @staticmethod
    def can_delete_mutabakat(role: UserRole) -> bool:
        """Mutabakat silme yetkisi var mı?"""
        return role in Permissions.CAN_DELETE_MUTABAKAT
    
    @staticmethod
    def can_send_mutabakat(role: UserRole) -> bool:
        """Mutabakat gönderme yetkisi var mı?"""
        return role in Permissions.CAN_SEND_MUTABAKAT
    
    @staticmethod
    def can_approve_mutabakat(role: UserRole) -> bool:
        """Mutabakat onaylama yetkisi var mı?"""
        return role in Permissions.CAN_APPROVE_MUTABAKAT
    
    @staticmethod
    def can_view_all_mutabakat(role: UserRole) -> bool:
        """Tüm mutabakatları görme yetkisi var mı?"""
        return role in Permissions.CAN_VIEW_ALL_MUTABAKAT
    
    @staticmethod
    def can_manage_users(role: UserRole) -> bool:
        """Kullanıcı yönetimi yetkisi var mı?"""
        return role in Permissions.CAN_MANAGE_USERS
    
    @staticmethod
    def can_bulk_create(role: UserRole) -> bool:
        """Toplu mutabakat oluşturma yetkisi var mı?"""
        return role in Permissions.CAN_BULK_CREATE

