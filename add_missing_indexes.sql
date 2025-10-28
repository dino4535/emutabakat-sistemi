-- Eksik Failed Login Tracking Index'lerini Ekle
-- Tarih: 27 Ekim 2025

USE Mutabakat;
GO

-- failed_login_attempts tablosuna eksik index'leri ekle
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[failed_login_attempts]') AND name = N'idx_failed_login_vkn')
BEGIN
    CREATE NONCLUSTERED INDEX idx_failed_login_vkn
    ON failed_login_attempts(vkn_tckn);
    PRINT '[OK] idx_failed_login_vkn index eklendi';
END
ELSE
BEGIN
    PRINT '[OK] idx_failed_login_vkn index zaten mevcut';
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[failed_login_attempts]') AND name = N'idx_failed_login_user')
BEGIN
    CREATE NONCLUSTERED INDEX idx_failed_login_user
    ON failed_login_attempts(user_id);
    PRINT '[OK] idx_failed_login_user index eklendi';
END
ELSE
BEGIN
    PRINT '[OK] idx_failed_login_user index zaten mevcut';
END
GO

PRINT '';
PRINT '============================================================';
PRINT 'Eksik index''ler eklendi!';
PRINT '============================================================';
GO

