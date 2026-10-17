<?php
require __DIR__ . '/includes/auth.php';
require __DIR__ . '/includes/db.php';
require __DIR__ . '/includes/upload.php';
requireLogin();

$id = (int) ($_GET['id'] ?? $_POST['id'] ?? 0);

$stmt = getDb()->prepare('SELECT * FROM karya WHERE id = ?');
$stmt->execute([$id]);
$karya = $stmt->fetch();

if (!$karya) {
    http_response_code(404);
    exit('Karya tidak ditemukan.');
}

$error = '';

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
            $gambar = $upload['filename'] ?? $karya['gambar'];
            $lebar = $upload['width'] ?? $karya['lebar'];
            $tinggi = $upload['height'] ?? $karya['tinggi'];

            if ($upload && $karya['gambar']) {
                $old = __DIR__ . '/../uploads/karya/' . $karya['gambar'];
                if (is_file($old)) {
                    unlink($old);
                }
            }

            $stmt = getDb()->prepare(
                'UPDATE karya SET judul = ?, seniman = ?, tahun = ?, deskripsi = ?, gambar = ?, lebar = ?, tinggi = ? WHERE id = ?'
            );
            $stmt->execute([$judul, $seniman, $tahun, $deskripsi, $gambar, $lebar, $tinggi, $id]);

            header('Location: index.php?saved=1');
            exit;
        } catch (RuntimeException $e) {
            $error = $e->getMessage();
        }
    }

    $karya = array_merge($karya, compact('judul', 'seniman', 'tahun', 'deskripsi'));
}

$pageTitle = 'Ubah Karya — Admin Galeria';
require __DIR__ . '/includes/header.php';
?>

<h1>Ubah Karya</h1>

<?php if ($error): ?>
    <p class="alert"><?= htmlspecialchars($error) ?></p>
<?php endif; ?>

<form method="post" enctype="multipart/form-data">
    <input type="hidden" name="csrf_token" value="<?= csrfToken() ?>">
    <input type="hidden" name="id" value="<?= $karya['id'] ?>">

    <div class="form-layout">
        <div class="form-card">
            <h2>Detail Karya</h2>

            <label>Judul Karya
                <input type="text" name="judul" value="<?= htmlspecialchars($karya['judul']) ?>" required>
            </label>

            <div class="field-row">
                <label>Seniman
                    <input type="text" name="seniman" value="<?= htmlspecialchars($karya['seniman']) ?>" required>
                </label>

                <label>Tahun
                    <input type="text" name="tahun" value="<?= htmlspecialchars($karya['tahun'] ?? '') ?>">
                </label>
            </div>

            <label>Deskripsi
                <textarea name="deskripsi" rows="6"><?= htmlspecialchars($karya['deskripsi'] ?? '') ?></textarea>
            </label>
        </div>

        <div class="form-card">
            <h2>Gambar</h2>

            <?php if ($karya['gambar']): ?>
                <img class="thumb-preview" src="../uploads/karya/<?= htmlspecialchars($karya['gambar']) ?>" alt="">
            <?php endif; ?>

            <div class="file-drop">
                <input type="file" id="gambar-input" name="gambar" accept="image/jpeg,image/png,image/webp">
                <label for="gambar-input" class="btn btn-sm btn-outline">Ganti Gambar</label>
                <span class="file-name">Kosongkan jika tidak diubah</span>
            </div>
        </div>
    </div>

    <button type="submit" class="btn">Simpan Perubahan</button>
</form>

<script src="assets/upload-compress.js?v=<?= filemtime(__DIR__ . '/assets/upload-compress.js') ?>"></script>
<?php require __DIR__ . '/includes/footer.php'; ?>
