<?php
require __DIR__ . '/../admin/includes/db.php';

header('Content-Type: application/json; charset=utf-8');

$rows = getDb()
    ->query('SELECT id, judul, seniman, tahun, deskripsi, gambar, lebar, tinggi FROM karya ORDER BY id ASC')
    ->fetchAll();

echo json_encode($rows, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
