<?php

// 1400px sudah lebih dari cukup untuk ukuran lukisan di galeri 3D
// (dipasang pada bingkai sekitar 2-3 meter) maupun panel info — dipatok
// lebih rendah dari sebelumnya (1920px) supaya tekstur tidak boros
// memori GPU saat koleksi bertambah banyak.
const KARYA_MAX_DIMENSION = 1400;
const KARYA_WEBP_QUALITY = 82;

/**
 * Handles an uploaded karya image: validates it, downsizes/recompresses it
 * with GD so stored files stay small regardless of the original, and saves
 * it as WebP (~25-35% lebih kecil dari JPEG pada kualitas visual yang
 * setara — didukung semua browser modern). Returns
 * ['filename' => ..., 'width' => ..., 'height' => ...] (dimensi akhir
 * setelah resize, disimpan ke DB supaya galeri 3D tidak perlu memuat ulang
 * tiap gambar hanya untuk tahu rasio aspeknya), atau null jika tidak ada
 * file yang diunggah. Throws RuntimeException on invalid input.
 */
function handleKaryaUpload(array $file): ?array
{
    if (!isset($file['error']) || $file['error'] === UPLOAD_ERR_NO_FILE) {
        return null;
    }

    if ($file['error'] !== UPLOAD_ERR_OK) {
        throw new RuntimeException('Gagal mengunggah gambar (kemungkinan ukuran file melebihi batas).');
    }

    $allowed = ['image/jpeg', 'image/png', 'image/webp'];
    $mime = mime_content_type($file['tmp_name']);
    if (!in_array($mime, $allowed, true)) {
        throw new RuntimeException('Format gambar harus JPG, PNG, atau WEBP.');
    }

    $image = loadImageForUpload($file['tmp_name'], $mime);

    $filename = bin2hex(random_bytes(16)) . '.webp';
    $destination = __DIR__ . '/../../uploads/karya/' . $filename;

    if (!imagewebp($image, $destination, KARYA_WEBP_QUALITY)) {
        imagedestroy($image);
        throw new RuntimeException('Gagal menyimpan gambar.');
    }

    $width = imagesx($image);
    $height = imagesy($image);
    imagedestroy($image);

    return ['filename' => $filename, 'width' => $width, 'height' => $height];
}

/**
 * Loads an uploaded image, applies EXIF rotation (JPEG only), flattens
 * transparency onto white, and downsizes it so its longest side is at
 * most KARYA_MAX_DIMENSION — keeping stored files small no matter how
 * large the original upload was.
 */
function loadImageForUpload(string $tmpPath, string $mime): \GdImage
{
    switch ($mime) {
        case 'image/jpeg':
            $image = @imagecreatefromjpeg($tmpPath);
            break;
        case 'image/png':
            $image = @imagecreatefrompng($tmpPath);
            break;
        case 'image/webp':
            $image = @imagecreatefromwebp($tmpPath);
            break;
        default:
            $image = false;
    }

    if (!$image) {
        throw new RuntimeException('Gagal membaca gambar. File mungkin rusak.');
    }

    if ($mime === 'image/jpeg') {
        $image = applyExifRotation($image, $tmpPath);
    }

    $width = imagesx($image);
    $height = imagesy($image);
    $longest = max($width, $height);
    $scale = $longest > KARYA_MAX_DIMENSION ? KARYA_MAX_DIMENSION / $longest : 1;
    $targetWidth = max(1, (int) round($width * $scale));
    $targetHeight = max(1, (int) round($height * $scale));

    // Selalu digambar ulang di atas kanvas putih (bukan hanya saat resize)
    // supaya transparansi PNG/WEBP tidak berubah jadi hitam saat disimpan
    // sebagai JPEG.
    $canvas = imagecreatetruecolor($targetWidth, $targetHeight);
    imagefill($canvas, 0, 0, imagecolorallocate($canvas, 255, 255, 255));
    imagecopyresampled($canvas, $image, 0, 0, 0, 0, $targetWidth, $targetHeight, $width, $height);
    imagedestroy($image);

    return $canvas;
}

function applyExifRotation(\GdImage $image, string $tmpPath): \GdImage
{
    if (!function_exists('exif_read_data')) {
        return $image;
    }

    $exif = @exif_read_data($tmpPath);
    $orientation = $exif['Orientation'] ?? 1;

    switch ($orientation) {
        case 3:
            return imagerotate($image, 180, 0);
        case 6:
            return imagerotate($image, -90, 0);
        case 8:
            return imagerotate($image, 90, 0);
        default:
            return $image;
    }
}
