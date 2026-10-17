<?php
require __DIR__ . '/includes/auth.php';
require __DIR__ . '/includes/db.php';
requireLogin();

$q = trim($_GET['q'] ?? '');

if ($q !== '') {
    $stmt = getDb()->prepare(
        'SELECT * FROM karya WHERE judul LIKE ? OR seniman LIKE ? ORDER BY created_at DESC'
    );
    $like = '%' . str_replace(['%', '_'], ['\%', '\_'], $q) . '%';
    $stmt->execute([$like, $like]);
    $karyaList = $stmt->fetchAll();
} else {
    $karyaList = getDb()->query('SELECT * FROM karya ORDER BY created_at DESC')->fetchAll();
}

$pageTitle = 'Daftar Karya — Admin Galeria';
require __DIR__ . '/includes/header.php';
?>

<div class="page-head">
    <h1>Daftar Karya</h1>
    <a class="btn" href="create.php">+ Tambah Karya</a>
</div>

<?php if (!empty($_GET['deleted'])): ?>
    <p class="alert alert-success">Karya berhasil dihapus.</p>
<?php endif; ?>
<?php if (!empty($_GET['saved'])): ?>
    <p class="alert alert-success">Karya berhasil disimpan.</p>
<?php endif; ?>

<form method="get" class="search-form">
    <input type="search" name="q" value="<?= htmlspecialchars($q) ?>" placeholder="Cari judul atau seniman…">
    <button type="submit" class="btn">Cari</button>
    <?php if ($q !== ''): ?>
        <a href="index.php" class="btn-reset">Reset</a>
    <?php endif; ?>
</form>

<?php if ($q !== ''): ?>
    <p class="search-summary">
        Menampilkan <?= count($karyaList) ?> hasil untuk "<?= htmlspecialchars($q) ?>".
    </p>
<?php endif; ?>

<?php if (!$karyaList): ?>
    <div class="empty-state">
        <?php if ($q !== ''): ?>
            Tidak ada karya yang cocok dengan pencarian.
        <?php else: ?>
            Belum ada data karya. <a href="create.php">Tambah karya pertama</a>.
        <?php endif; ?>
    </div>
<?php else: ?>
    <div class="karya-grid">
        <?php foreach ($karyaList as $karya): ?>
            <div class="karya-card">
                <div class="thumb-wrap">
                    <?php if ($karya['gambar']): ?>
                        <img src="../uploads/karya/<?= htmlspecialchars($karya['gambar']) ?>" alt="">
                    <?php else: ?>
                        <div class="thumb-empty">Tanpa gambar</div>
                    <?php endif; ?>
                </div>
                <div class="card-body">
                    <div class="card-title"><?= htmlspecialchars($karya['judul']) ?></div>
                    <div class="card-meta">
                        <?= htmlspecialchars($karya['seniman']) ?><?= $karya['tahun'] ? ' • ' . htmlspecialchars($karya['tahun']) : '' ?>
                    </div>
                </div>
                <div class="card-actions">
                    <a href="edit.php?id=<?= $karya['id'] ?>" class="btn btn-sm btn-outline">Ubah</a>
                    <form method="post" action="delete.php" onsubmit="return confirm('Hapus karya ini?');">
                        <input type="hidden" name="id" value="<?= $karya['id'] ?>">
                        <input type="hidden" name="csrf_token" value="<?= csrfToken() ?>">
                        <button type="submit" class="btn btn-sm btn-danger">Hapus</button>
                    </form>
                </div>
            </div>
        <?php endforeach; ?>
    </div>
<?php endif; ?>

<?php require __DIR__ . '/includes/footer.php'; ?>
