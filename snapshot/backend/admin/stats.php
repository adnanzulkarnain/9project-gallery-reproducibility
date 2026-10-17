<?php
require __DIR__ . '/includes/auth.php';
require __DIR__ . '/includes/db.php';
requireLogin();

$db = getDb();

$total = (int) $db->query('SELECT COUNT(*) FROM kunjungan')->fetchColumn();
$today = (int) $db->query('SELECT COUNT(*) FROM kunjungan WHERE DATE(dikunjungi_pada) = CURDATE()')->fetchColumn();
$uniqueVisitors = (int) $db->query('SELECT COUNT(DISTINCT ip_hash) FROM kunjungan WHERE ip_hash IS NOT NULL')->fetchColumn();

$daily = $db->query('
    SELECT DATE(dikunjungi_pada) AS tanggal, COUNT(*) AS jumlah
    FROM kunjungan
    WHERE dikunjungi_pada >= (CURDATE() - INTERVAL 13 DAY)
    GROUP BY DATE(dikunjungi_pada)
')->fetchAll(PDO::FETCH_KEY_PAIR);

// Lengkapi 14 hari terakhir dengan 0 untuk hari tanpa kunjungan,
// supaya grafiknya tidak bolong.
$series = [];
for ($i = 13; $i >= 0; $i--) {
    $date = date('Y-m-d', strtotime("-{$i} day"));
    $series[$date] = (int) ($daily[$date] ?? 0);
}
$maxCount = max(1, max($series));

$pageTitle = 'Statistik — Admin Galeria';
require __DIR__ . '/includes/header.php';
?>

<div class="page-head">
    <h1>Statistik Kunjungan</h1>
</div>

<div class="stats-cards">
    <div class="stat-card">
        <div class="stat-value"><?= number_format($total, 0, ',', '.') ?></div>
        <div class="stat-label">Total Kunjungan</div>
    </div>
    <div class="stat-card">
        <div class="stat-value"><?= number_format($today, 0, ',', '.') ?></div>
        <div class="stat-label">Kunjungan Hari Ini</div>
    </div>
    <div class="stat-card">
        <div class="stat-value"><?= number_format($uniqueVisitors, 0, ',', '.') ?></div>
        <div class="stat-label">Pengunjung Unik</div>
    </div>
</div>

<h2 class="section-title">14 Hari Terakhir</h2>

<?php if ($total === 0): ?>
    <div class="empty-state">Belum ada data kunjungan. Statistik akan muncul setelah museum 3D dibuka pengunjung.</div>
<?php else: ?>
    <div class="bar-chart">
        <?php foreach ($series as $date => $count): ?>
            <div class="bar-col">
                <div class="bar-value"><?= $count ?></div>
                <div class="bar" style="height: <?= max(4, round($count / $maxCount * 100)) ?>%"></div>
                <div class="bar-label"><?= date('d/m', strtotime($date)) ?></div>
            </div>
        <?php endforeach; ?>
    </div>
<?php endif; ?>

<?php require __DIR__ . '/includes/footer.php'; ?>
