-- SMS Verification Logs Tablosu Oluşturma Script
-- Yasal delil için SMS gönderim kayıtları

IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[sms_verification_logs]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[sms_verification_logs] (
        [id] INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        
        -- Mutabakat Bilgisi
        [mutabakat_id] INT NOT NULL,
        [approval_token] NVARCHAR(100) NOT NULL,
        
        -- SMS Bilgileri
        [phone] NVARCHAR(20) NOT NULL,
        [receiver_name] NVARCHAR(255) NULL,
        [sms_message] NTEXT NULL,
        
        -- ISP Bilgileri (Yasal Delil)
        [ip_address] NVARCHAR(50) NULL,
        [isp] NVARCHAR(255) NULL,
        [city] NVARCHAR(255) NULL,
        [country] NVARCHAR(255) NULL,
        [organization] NVARCHAR(255) NULL,
        [user_agent] NVARCHAR(500) NULL,
        
        -- SMS Gönderim Durumu
        [sent_at] DATETIME NOT NULL DEFAULT GETDATE(),
        [sms_provider] NVARCHAR(50) NOT NULL DEFAULT 'goldsms',
        [sms_status] NVARCHAR(50) NOT NULL DEFAULT 'sent',
        [sms_provider_id] NVARCHAR(255) NULL,
        [error_message] NTEXT NULL,
        
        -- Token Kullanım Bilgisi
        [token_used] BIT NOT NULL DEFAULT 0,
        [token_used_at] DATETIME NULL,
        
        -- Foreign Key
        CONSTRAINT [FK_sms_verification_logs_mutabakats] 
            FOREIGN KEY ([mutabakat_id]) 
            REFERENCES [dbo].[mutabakats]([id]) 
            ON DELETE CASCADE,
            
        -- Indexes
        INDEX [IX_sms_verification_logs_mutabakat_id] ([mutabakat_id]),
        INDEX [IX_sms_verification_logs_approval_token] ([approval_token]),
        INDEX [IX_sms_verification_logs_phone] ([phone]),
        INDEX [IX_sms_verification_logs_sent_at] ([sent_at]),
        INDEX [IX_sms_verification_logs_token_used] ([token_used]),
        INDEX [IX_sms_verification_logs_ip_address] ([ip_address])
    );
    
    PRINT 'sms_verification_logs tablosu başarıyla oluşturuldu.';
END
ELSE
BEGIN
    PRINT 'sms_verification_logs tablosu zaten mevcut.';
END;
GO

