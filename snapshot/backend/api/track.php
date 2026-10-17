<?php
require __DIR__ . '/../admin/includes/db.php';

header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false]);
    exit;
}

// IP disimpan dalam bentuk hash, bukan mentah — cukup untuk menghitung
// perkiraan pengunjung unik tanpa menyimpan alamat IP asli.
$ip = $_SERVER['REMOTE_ADDR'] ?? '';
$ipHash = $ip !== '' ? hash('sha256', $ip) : null;
$userAgent = substr($_SERVER['HTTP_USER_AGENT'] ?? '', 0, 255);

$stmt = getDb()->prepare('INSERT INTO kunjungan (ip_hash, user_agent) VALUES (?, ?)');
$stmt->execute([$ipHash, $userAgent]);

echo json_encode(['ok' => true]);
