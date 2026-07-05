CREATE DATABASE IF NOT EXISTS webscraper;

USE webscraper;

CREATE TABLE scraped_data(

    id INT AUTO_INCREMENT PRIMARY KEY,

    website_url VARCHAR(500) NOT NULL,

    title VARCHAR(500),

    description TEXT,

    total_links INT DEFAULT 0,

    total_images INT DEFAULT 0,

    status VARCHAR(30),

    http_status INT,

    scraped_time DATETIME DEFAULT CURRENT_TIMESTAMP

);