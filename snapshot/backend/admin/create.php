<?php
require __DIR__ . '/includes/auth.php';
require __DIR__ . '/includes/db.php';
require __DIR__ . '/includes/upload.php';
requireLogin();

$error = '';
$judul = $seniman = $tahun = $deskripsi = '';

if (postExceededSizeLimit()) {
    $error = 'File yang diunggah terlalu besar (maksimal ' . ini_get('upload_max_filesize') . ').';
} elseif ($_SERVER['REQUEST_METHOD'] === 'POST') {
    checkCsrf();

    $judul = trim($_POST['judul'] ?? '');
    $seniman = trim($_POST['seniman'] ?? '');
    $tahun = trim($_POST['tahun'] ?? '');
    $deskripsi = trim($_POST['deskripsi'] ?? '');

    if ($judul === '' || $seniman === '') {
        $error = 'Judul dan seniman wajib diisi.';
    } else {
        try {
            $upload = handleKaryaUpload($_FILES['gambar'] ?? []);
            $gambar = $upload['filename'] ?? null;
            $lebar = $upload['width'] ?? null;
            $tinggi = $upload['height'] ?? null;

            $stmt = getDb()->prepare(
                'INSERT INTO karya (judul, seniman, tahun, deskripsi, gambar, lebar, tinggi) VALUES (?, ?, ?, ?, ?, ?, ?)'
            );
            $stmt->execute([$judul, $seniman, $tahun, $deskripsi, $gambar, $lebar, $tinggi]);

            header('Location: index.php?saved=1');
            exit;
        } catch (RuntimeException $e) {
            $error = $e->getMessage();
        }
    }
}

$pageTitle = 'Tambah Karya — Admin Galeria';
require __DIR__ . '/includes/header.php';
?>

<h1>Tambah Karya</h1>

<?php if ($error): ?>
    <p class="alert"><?= htmlspecialchars($error) ?></p>
<?php endif; ?>

<form method="post" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="<?= csrfToken() ?>">

    <div class="form-layout">
        <div class="form-card">
            <h2>Detail Karya</h2>

            <label>Judul Karya
                <input type="text" name="judul" value="<?= htmlspecialchars($judul) ?>" required>
            </label>

            <div class="field-row">
                <label>Seniman
                    <input type="text" name="seniman" value="<?= htmlspecialchars($seniman) ?>" required>
                </label>

                <label>Tahun
                    <input type="text" name="tahun" value="<?= htmlspecialchars($tahun) ?>" placeholder="mis. 1889 atau 1907–1908">
                </label>
            </div>

            <label>Deskripsi
                <textarea name="deskripsi" rows="6"><?= htmlspecialchars($deskripsi) ?></textarea>
            </label>
        </div>

        <div class="form-card">
            <h2>Gambar</h2>

            <div class="file-drop">
                <input type="file" id="gambar-input" name="gambar" accept="image/jpeg,image/png,image/webp">
                <label for="gambar-input" class="btn btn-sm btn-outline">Pilih Gambar</label>
                <span class="file-name">JPG/PNG/WEBP, otomatis dikompres</span>
            </div>
        </div>
    </div>

    <button type="submit" class="btn">Simpan</button>
</form>

<script src="assets/upload-compress.js?v=<?= filemtime(__DIR__ . '/assets/upload-compress.js') ?>"></script>
<?php require __DIR__ . '/includes/footer.php'; ?>
