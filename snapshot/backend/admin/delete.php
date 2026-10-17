<?php
require __DIR__ . '/includes/auth.php';
require __DIR__ . '/includes/db.php';
requireLogin();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Method not allowed');
}

checkCsrf();

$id = (int) ($_POST['id'] ?? 0);

$stmt = getDb()->prepare('SELECT gambar FROM karya WHERE id = ?');
$stmt->execute([$id]);
$karya = $stmt->fetch();

if ($karya) {
    getDb()->prepare('DELETE FROM karya WHERE id = ?')->execute([$id]);

    if ($karya['gambar']) {
        $file = __DIR__ . '/../uploads/karya/' . $karya['gambar'];
        if (is_file($file)) {
            unlink($file);
        }
    }
}

header('Location: index.php?deleted=1');
exit;
