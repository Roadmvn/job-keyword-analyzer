-- ===================================
-- INITIALISATION BASE DE DONNÉES
-- Job Keywords Analyzer
-- ===================================

-- Utiliser la base de données
USE job_analyzer;

-- ===================================
-- TABLE DES OFFRES D'EMPLOI
-- ===================================
CREATE TABLE IF NOT EXISTS job_offers (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    description TEXT NOT NULL,
    requirements TEXT,
    salary_min DECIMAL(10, 2),
    salary_max DECIMAL(10, 2),
    contract_type ENUM('CDI', 'CDD', 'FREELANCE', 'STAGE', 'APPRENTISSAGE', 'OTHER') DEFAULT 'OTHER',
    experience_level ENUM('JUNIOR', 'INTERMEDIATE', 'SENIOR', 'EXPERT', 'ANY') DEFAULT 'ANY',
    remote_work BOOLEAN DEFAULT FALSE,
    source VARCHAR(100) NOT NULL, -- indeed, linkedin, etc.
    source_url VARCHAR(500),
    source_id VARCHAR(255),
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Index pour les recherches fréquentes
    INDEX idx_company (company),
    INDEX idx_location (location),
    INDEX idx_source (source),
    INDEX idx_scraped_at (scraped_at),
    INDEX idx_contract_type (contract_type),
    INDEX idx_experience_level (experience_level),
    
    -- Éviter les doublons
    UNIQUE KEY unique_source_offer (source, source_id)
);

-- ===================================
-- TABLE DES MOTS-CLÉS EXTRAITS
-- ===================================
CREATE TABLE IF NOT EXISTS keywords (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    keyword VARCHAR(100) NOT NULL,
    category ENUM('LANGUAGE', 'FRAMEWORK', 'TOOL', 'SKILL', 'DOMAIN', 'OTHER') DEFAULT 'OTHER',
    confidence DECIMAL(3, 2) DEFAULT 0.00,
    frequency INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Index pour les recherches
    INDEX idx_keyword (keyword),
    INDEX idx_category (category),
    INDEX idx_frequency (frequency DESC),
    
    -- Éviter les doublons
    UNIQUE KEY unique_keyword (keyword)
);

-- ===================================
-- TABLE DE LIAISON OFFRES <-> MOTS-CLÉS
-- ===================================
CREATE TABLE IF NOT EXISTS job_offer_keywords (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_offer_id BIGINT NOT NULL,
    keyword_id BIGINT NOT NULL,
    relevance_score DECIMAL(3, 2) DEFAULT 0.00,
    extraction_method ENUM('NLP', 'REGEX', 'MANUAL') DEFAULT 'NLP',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Clés étrangères
    FOREIGN KEY (job_offer_id) REFERENCES job_offers(id) ON DELETE CASCADE,
    FOREIGN KEY (keyword_id) REFERENCES keywords(id) ON DELETE CASCADE,
    
    -- Index pour les jointures
    INDEX idx_job_offer (job_offer_id),
    INDEX idx_keyword (keyword_id),
    INDEX idx_relevance (relevance_score DESC),
    
    -- Éviter les doublons
    UNIQUE KEY unique_job_keyword (job_offer_id, keyword_id)
);

-- ===================================
-- TABLE DES TÂCHES DE SCRAPING
-- ===================================
CREATE TABLE IF NOT EXISTS scraping_jobs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL, -- ID Redis/RQ
    source VARCHAR(100) NOT NULL,
    search_query VARCHAR(255),
    location VARCHAR(255),
    max_pages INT DEFAULT 1,
    status ENUM('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED') DEFAULT 'PENDING',
    progress INT DEFAULT 0, -- Pourcentage de completion
    total_offers_found INT DEFAULT 0,
    offers_processed INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Index
    INDEX idx_job_id (job_id),
    INDEX idx_status (status),
    INDEX idx_source (source),
    INDEX idx_created_at (created_at DESC),
    
    UNIQUE KEY unique_job_id (job_id)
);

-- ===================================
-- TABLE DES STATISTIQUES QUOTIDIENNES
-- ===================================
CREATE TABLE IF NOT EXISTS daily_stats (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    total_offers INT DEFAULT 0,
    new_offers INT DEFAULT 0,
    unique_companies INT DEFAULT 0,
    unique_keywords INT DEFAULT 0,
    avg_salary DECIMAL(10, 2),
    top_keyword VARCHAR(100),
    top_company VARCHAR(255),
    top_location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_date (date)
);

-- ===================================
-- VUES UTILES
-- ===================================

-- Vue des offres avec leurs mots-clés principaux
CREATE OR REPLACE VIEW job_offers_with_keywords AS
SELECT 
    jo.id,
    jo.title,
    jo.company,
    jo.location,
    jo.contract_type,
    jo.experience_level,
    jo.salary_min,
    jo.salary_max,
    jo.scraped_at,
    GROUP_CONCAT(
        CONCAT(k.keyword, '(', jok.relevance_score, ')')
        ORDER BY jok.relevance_score DESC
        SEPARATOR ', '
    ) as top_keywords
FROM job_offers jo
LEFT JOIN job_offer_keywords jok ON jo.id = jok.job_offer_id
LEFT JOIN keywords k ON jok.keyword_id = k.id
GROUP BY jo.id;

-- Vue des mots-clés les plus populaires
CREATE OR REPLACE VIEW popular_keywords AS
SELECT 
    k.keyword,
    k.category,
    COUNT(jok.job_offer_id) as usage_count,
    AVG(jok.relevance_score) as avg_relevance,
    k.frequency
FROM keywords k
LEFT JOIN job_offer_keywords jok ON k.id = jok.keyword_id
GROUP BY k.id
ORDER BY usage_count DESC, avg_relevance DESC;

-- ===================================
-- DONNÉES D'EXEMPLE POUR LES TESTS
-- ===================================
INSERT IGNORE INTO keywords (keyword, category, frequency) VALUES
('Python', 'LANGUAGE', 1),
('JavaScript', 'LANGUAGE', 1),
('React', 'FRAMEWORK', 1),
('Django', 'FRAMEWORK', 1),
('FastAPI', 'FRAMEWORK', 1),
('Docker', 'TOOL', 1),
('Git', 'TOOL', 1),
('SQL', 'LANGUAGE', 1),
('Machine Learning', 'DOMAIN', 1),
('DevOps', 'DOMAIN', 1);

-- ===================================
-- PROCÉDURES STOCKÉES UTILES
-- ===================================

DELIMITER //

-- Procédure pour mettre à jour les statistiques quotidiennes
CREATE PROCEDURE UpdateDailyStats(IN target_date DATE)
BEGIN
    INSERT INTO daily_stats (
        date, 
        total_offers, 
        new_offers, 
        unique_companies, 
        unique_keywords,
        avg_salary
    ) VALUES (
        target_date,
        (SELECT COUNT(*) FROM job_offers WHERE DATE(scraped_at) <= target_date),
        (SELECT COUNT(*) FROM job_offers WHERE DATE(scraped_at) = target_date),
        (SELECT COUNT(DISTINCT company) FROM job_offers WHERE DATE(scraped_at) <= target_date),
        (SELECT COUNT(*) FROM keywords),
        (SELECT AVG((salary_min + salary_max) / 2) FROM job_offers WHERE salary_min IS NOT NULL AND salary_max IS NOT NULL AND DATE(scraped_at) = target_date)
    ) ON DUPLICATE KEY UPDATE
        total_offers = VALUES(total_offers),
        new_offers = VALUES(new_offers),
        unique_companies = VALUES(unique_companies),
        unique_keywords = VALUES(unique_keywords),
        avg_salary = VALUES(avg_salary),
        updated_at = CURRENT_TIMESTAMP;
END //

DELIMITER ;

-- ===================================
-- ÉVÉNEMENTS AUTOMATIQUES
-- ===================================

-- Nettoyer les anciennes tâches de scraping (plus de 30 jours)
CREATE EVENT IF NOT EXISTS cleanup_old_scraping_jobs
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
DELETE FROM scraping_jobs 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY)
AND status IN ('COMPLETED', 'FAILED', 'CANCELLED');

-- Mettre à jour les statistiques quotidiennes chaque nuit
CREATE EVENT IF NOT EXISTS update_daily_stats
ON SCHEDULE EVERY 1 DAY
STARTS (CURRENT_DATE + INTERVAL 1 DAY + INTERVAL 1 HOUR)
DO
CALL UpdateDailyStats(CURRENT_DATE - INTERVAL 1 DAY); 