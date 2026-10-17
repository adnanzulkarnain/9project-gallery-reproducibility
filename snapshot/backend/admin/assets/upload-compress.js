(function () {
    var MAX_DIM = 1920;
    var QUALITY = 0.85;
    var SKIP_BELOW_BYTES = 1.5 * 1024 * 1024;

    var input = document.querySelector('input[type="file"][name="gambar"]');
    if (!input) return;

    var hint = input.parentElement ? input.parentElement.querySelector('.file-name') : null;
    var defaultHintText = hint ? hint.textContent : '';
    if (!hint) {
        hint = document.createElement('span');
        hint.className = 'upload-hint';
        input.insertAdjacentElement('afterend', hint);
    }

    input.addEventListener('change', function () {
        var file = input.files[0];
        if (!file || !/^image\//.test(file.type)) {
            hint.textContent = defaultHintText;
            return;
        }

        hint.textContent = file.name;

        var img = new Image();
        var url = URL.createObjectURL(file);

        img.onload = function () {
            URL.revokeObjectURL(url);

            var w = img.naturalWidth, h = img.naturalHeight;
            var scale = Math.min(1, MAX_DIM / Math.max(w, h));

            if (scale === 1 && file.size <= SKIP_BELOW_BYTES) {
                return; // sudah cukup kecil, tidak perlu dikompres ulang
            }

            var cw = Math.round(w * scale), ch = Math.round(h * scale);
            var canvas = document.createElement('canvas');
            canvas.width = cw;
            canvas.height = ch;
            var ctx = canvas.getContext('2d');
            ctx.fillStyle = '#fff';
            ctx.fillRect(0, 0, cw, ch);
            ctx.drawImage(img, 0, 0, cw, ch);

            canvas.toBlob(function (blob) {
                if (!blob) return;
                var compressed = new File(
                    [blob],
                    file.name.replace(/\.[^.]+$/, '') + '.jpg',
                    { type: 'image/jpeg' }
                );
                var dt = new DataTransfer();
                dt.items.add(compressed);
                input.files = dt.files;

                var beforeMb = (file.size / 1024 / 1024).toFixed(1);
                var afterMb = (compressed.size / 1024 / 1024).toFixed(1);
                hint.textContent = file.name + ' — dikompres otomatis: ' + beforeMb + ' MB → ' + afterMb + ' MB';
            }, 'image/jpeg', QUALITY);
        };
        img.onerror = function () { URL.revokeObjectURL(url); };
        img.src = url;
    });
})();
