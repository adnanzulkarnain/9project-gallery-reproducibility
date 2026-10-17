<?php

// Di Docker, kredensial DB disuntikkan sebagai environment variable lewat
// docker-compose.yml. Di hosting biasa (mis. cPanel) tidak ada mekanisme
// itu, jadi sebagai fallback file .env di root proyek dibaca langsung.
function loadEnvFile(): void
{
    static $loaded = false;
    if ($loaded) {
        return;
    }
    $loaded = true;

    $envPath = __DIR__ . '/../../../.env';
    if (!is_readable($envPath)) {
        return;
    }

    foreach (file($envPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#') || !str_contains($line, '=')) {
            continue;
        }
        [$key, $value] = explode('=', $line, 2);
        $key = trim($key);
        $value = trim($value);
        if (getenv($key) === false) {
            putenv("{$key}={$value}");
        }
    }
}

function getDb(): PDO
{
    static $pdo = null;

    if ($pdo === null) {
        loadEnvFile();

        $host = getenv('DB_HOST') ?: 'localhost';
        $name = getenv('DB_NAME') ?: 'galeri';
        $user = getenv('DB_USER') ?: 'galeri_user';
        $pass = getenv('DB_PASSWORD') ?: '';

        $dsn = "mysql:host={$host};dbname={$name};charset=utf8mb4";
        $pdo = new PDO($dsn, $user, $pass, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
    }

    return $pdo;
}
