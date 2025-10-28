-- Failed Login Tracking Kolonlarını Ekle
-- Tarih: 27 Ekim 2025

USE Mutabakat;
GO

-- Users tablosuna yeni kolonlar ekle
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND name = 'failed_login_count')
BEGIN
    ALTER TABLE users ADD failed_login_count INT DEFAULT 0 NOT NULL;
    PRINT 'failed_login_count kolonu eklendi';
END
ELSE
BEGIN
    PRINT 'failed_login_count kolonu zaten mevcut';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND name = 'last_failed_login')
BEGIN
    ALTER TABLE users ADD last_failed_login DATETIME NULL;
    PRINT 'last_failed_login kolonu eklendi';
END
ELSE
BEGIN
    PRINT 'last_failed_login kolonu zaten mevcut';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND name = 'account_locked_until')
BEGIN
    ALTER TABLE users ADD account_locked_until DATETIME NULL;
    PRINT 'account_locked_until kolonu eklendi';
END
ELSE
BEGIN
    PRINT 'account_locked_until kolonu zaten mevcut';
END
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID(N'[dbo].[users]') AND name = 'account_locked_reason')
BEGIN
    ALTER TABLE users ADD account_locked_reason NVARCHAR(500) NULL;
    PRINT 'account_locked_reason kolonu eklendi';
END
ELSE
BEGIN
    PRINT 'account_locked_reason kolonu zaten mevcut';
END
GO

-- Failed Login Attempts tablosu oluştur
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'failed_login_attempts')
BEGIN
    CREATE TABLE failed_login_attempts (
        id INT PRIMARY KEY IDENTITY(1,1),
        vkn_tckn NVARCHAR(11) NOT NULL,
        username NVARCHAR(100) NULL,
        user_id INT NULL,
        company_id INT NULL,
        ip_address NVARCHAR(50) NOT NULL,
        user_agent NVARCHAR(500),
        isp NVARCHAR(255),
        city NVARCHAR(255),
        country NVARCHAR(255),
        organization NVARCHAR(255),
        failure_reason NVARCHAR(500),
        attempted_at DATETIME NOT NULL DEFAULT GETDATE(),
        
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
    );
    
    -- İndeksler
    CREATE NONCLUSTERED INDEX idx_failed_login_vkn ON failed_login_attempts(vkn_tckn);
    CREATE NONCLUSTERED INDEX idx_failed_login_user ON failed_login_attempts(user_id);
    CREATE NONCLUSTERED INDEX idx_failed_login_ip ON failed_login_attempts(ip_address);
    CREATE NONCLUSTERED INDEX idx_failed_login_attempted ON failed_login_attempts(attempted_at);
    
    PRINT 'failed_login_attempts tablosu olusturuldu';
END
ELSE
BEGIN
    PRINT 'failed_login_attempts tablosu zaten mevcut';
END
GO

PRINT '';
PRINT '============================================================';
PRINT 'Failed Login Tracking migration tamamlandi!';
PRINT '============================================================';
GO

