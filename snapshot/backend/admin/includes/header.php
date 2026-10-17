<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($pageTitle ?? 'Admin Galeria') ?></title>
    <link rel="icon" type="image/svg+xml" href="../favicon.svg">
    <link rel="stylesheet" href="assets/style.css?v=<?= filemtime(__DIR__ . '/../assets/style.css') ?>">
</head>
<body>
<?php if (!empty($_SESSION['admin_id'])): $current = basename($_SERVER['SCRIPT_NAME']); ?>
    <header class="topbar">
        <div class="brand">GALERIA <span>Admin</span></div>
        <nav>
            <a href="index.php" class="<?= $current === 'index.php' ? 'active' : '' ?>">Daftar Karya</a>
            <a href="create.php" class="<?= $current === 'create.php' ? 'active' : '' ?>">Tambah Karya</a>
            <a href="stats.php" class="<?= $current === 'stats.php' ? 'active' : '' ?>">Statistik</a>
            <a href="logout.php">Keluar (<?= htmlspecialchars($_SESSION['admin_username'] ?? '') ?>)</a>
        </nav>
    </header>
<?php endif; ?>
<main class="container">
