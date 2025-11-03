-- Audit Log Tablosu Oluşturma Script'i
-- SQL Server için

-- Audit Log Action Enum değerleri için constraint
IF NOT EXISTS (SELECT * FROM sys.check_constraints WHERE name = 'CHK_audit_log_action')
BEGIN
    ALTER TABLE audit_logs ADD CONSTRAINT CHK_audit_log_action CHECK (
        action IN (
            'login', 'logout', 'login_failed', 'password_change',
            'mutabakat_create', 'mutabakat_update', 'mutabakat_delete', 'mutabakat_send',
            'mutabakat_approve', 'mutabakat_reject', 'mutabakat_cancel', 'mutabakat_view', 'mutabakat_download_pdf',
            'user_create', 'user_update', 'user_delete', 'user_activate', 'user_deactivate',
            'bayi_create', 'bayi_update', 'bayi_delete', 'bayi_import',
            'company_create', 'company_update', 'company_delete', 'company_settings_update',
            'kvkk_consent_given', 'kvkk_consent_withdrawn', 'kvkk_data_export', 'kvkk_data_delete',
            'system_backup', 'system_restore', 'database_migration',
            'report_generate', 'report_export',
            'api_access', 'api_error',
            'unauthorized_access', 'suspicious_activity'
        )
    );
END;
GO

-- Audit Log Tablosu
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'audit_logs')
BEGIN
    CREATE TABLE audit_logs (
        id INT IDENTITY(1,1) PRIMARY KEY,
        
        -- İşlem Bilgileri
        action VARCHAR(100) NOT NULL,
        action_description NVARCHAR(MAX),
        status VARCHAR(20) DEFAULT 'success' NOT NULL,
        
        -- Kullanıcı Bilgileri
        user_id INT NULL,
        username VARCHAR(100),
        user_role VARCHAR(50),
        
        -- Şirket Bilgileri
        company_id INT NULL,
        company_name NVARCHAR(255),
        
        -- İlişkili Kayıt Bilgileri
        target_model VARCHAR(100),
        target_id INT,
        target_identifier NVARCHAR(255),
        
        -- Değişiklik Bilgileri (JSON formatında)
        old_values NVARCHAR(MAX),
        new_values NVARCHAR(MAX),
        
        -- IP ve Konum Bilgileri
        ip_address VARCHAR(50),
        user_agent VARCHAR(500),
        isp NVARCHAR(255),
        city NVARCHAR(255),
        country NVARCHAR(255),
        
        -- HTTP Request Bilgileri
        http_method VARCHAR(10),
        endpoint VARCHAR(500),
        request_data NVARCHAR(MAX),
        response_status INT,
        
        -- Hata Bilgileri
        error_message NVARCHAR(MAX),
        error_traceback NVARCHAR(MAX),
        
        -- Zaman Bilgileri
        created_at DATETIME2 DEFAULT GETDATE() NOT NULL,
        duration_ms INT,
        
        -- Foreign Keys
        CONSTRAINT FK_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
        CONSTRAINT FK_audit_logs_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
    );
    
    PRINT '✅ audit_logs tablosu oluşturuldu';
END
ELSE
BEGIN
    PRINT '⚠️  audit_logs tablosu zaten mevcut';
END;
GO

-- Index'ler (Performans için)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_audit_logs_action')
BEGIN
    CREATE INDEX IX_audit_logs_action ON audit_logs(action);
    PRINT '✅ IX_audit_logs_action index oluşturuldu';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_audit_logs_user_id')
BEGIN
    CREATE INDEX IX_audit_logs_user_id ON audit_logs(user_id);
    PRINT '✅ IX_audit_logs_user_id index oluşturuldu';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_audit_logs_company_id')
BEGIN
    CREATE INDEX IX_audit_logs_company_id ON audit_logs(company_id);
    PRINT '✅ IX_audit_logs_company_id index oluşturuldu';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_audit_logs_created_at')
BEGIN
    CREATE INDEX IX_audit_logs_created_at ON audit_logs(created_at DESC);
    PRINT '✅ IX_audit_logs_created_at index oluşturuldu';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_audit_logs_username')
BEGIN
    CREATE INDEX IX_audit_logs_username ON audit_logs(username);
    PRINT '✅ IX_audit_logs_username index oluşturuldu';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_audit_logs_ip_address')
BEGIN
    CREATE INDEX IX_audit_logs_ip_address ON audit_logs(ip_address);
    PRINT '✅ IX_audit_logs_ip_address index oluşturuldu';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_audit_logs_status')
BEGIN
    CREATE INDEX IX_audit_logs_status ON audit_logs(status);
    PRINT '✅ IX_audit_logs_status index oluşturuldu';
END;

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_audit_logs_target_id')
BEGIN
    CREATE INDEX IX_audit_logs_target_id ON audit_logs(target_id);
    PRINT '✅ IX_audit_logs_target_id index oluşturuldu';
END;
GO

PRINT '🎉 Audit Log sistemi başarıyla kuruldu!';
GO

-- Tablo bilgilerini göster
SELECT 
    COUNT(*) as 'Toplam Kayıt',
    (SELECT COUNT(*) FROM audit_logs WHERE status = 'success') as 'Başarılı',
    (SELECT COUNT(*) FROM audit_logs WHERE status = 'failed') as 'Başarısız',
    (SELECT COUNT(*) FROM audit_logs WHERE status = 'error') as 'Hatalı'
FROM audit_logs;
GO

