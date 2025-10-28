-- Company tablosuna notification_email kolonu ekle
-- Mutabakat sonuç bildirimleri bu adrese gönderilecek
-- Tarih: 27 Ekim 2025

USE Mutabakat;
GO

-- Companies tablosuna notification_email kolonu ekle
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[companies]') AND name = 'notification_email')
BEGIN
    ALTER TABLE companies ADD notification_email NVARCHAR(255) NULL;
    PRINT '[OK] notification_email kolonu eklendi';
END
ELSE
BEGIN
    PRINT '[OK] notification_email kolonu zaten mevcut';
END
GO

-- Index ekle (email araması için)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE object_id = OBJECT_ID(N'[dbo].[companies]') AND name = N'idx_companies_notification_email')
BEGIN
    CREATE NONCLUSTERED INDEX idx_companies_notification_email
    ON companies(notification_email)
    WHERE notification_email IS NOT NULL;
    PRINT '[OK] idx_companies_notification_email index eklendi';
END
ELSE
BEGIN
    PRINT '[OK] idx_companies_notification_email index zaten mevcut';
END
GO

PRINT '';
PRINT '============================================================';
PRINT 'Email bildirim sistemi migration tamamlandi!';
PRINT '============================================================';
GO

