FROM php:8.2-apache

RUN apt-get update \
    && apt-get install -y --no-install-recommends libjpeg62-turbo-dev libpng-dev libwebp-dev \
    && rm -rf /var/lib/apt/lists/* \
    && docker-php-ext-configure gd --with-jpeg --with-webp \
    && docker-php-ext-install pdo pdo_mysql mysqli gd \
    && a2enmod rewrite expires headers \
    && echo "ServerName localhost" >> /etc/apache2/apache2.conf

RUN { \
        echo "upload_max_filesize = 15M"; \
        echo "post_max_size = 16M"; \
        echo "display_errors = Off"; \
        echo "log_errors = On"; \
        echo "expose_php = Off"; \
    } > /usr/local/etc/php/conf.d/uploads.ini

# Aset statis (gambar karya, library JS) tidak pernah berubah isinya
# setelah dibuat — nama filenya acak per unggahan — jadi aman di-cache
# lama di browser pengunjung, mengurangi request berulang saat mereka
# berpindah ruangan di galeri 3D.
RUN { \
        echo "<IfModule mod_expires.c>"; \
        echo "  ExpiresActive On"; \
        echo "  <FilesMatch \"\\.(jpg|jpeg|png|webp|gif|ico|svg)\$\">"; \
        echo "    ExpiresDefault \"access plus 30 days\""; \
        echo "  </FilesMatch>"; \
        echo "  <FilesMatch \"\\.(js|css)\$\">"; \
        echo "    ExpiresDefault \"access plus 7 days\""; \
        echo "  </FilesMatch>"; \
        echo "</IfModule>"; \
        echo "<IfModule mod_headers.c>"; \
        echo "  <FilesMatch \"\\.(jpg|jpeg|png|webp|gif|ico|svg|js|css)\$\">"; \
        echo "    Header set Cache-Control \"public, max-age=2592000\""; \
        echo "  </FilesMatch>"; \
        echo "</IfModule>"; \
    } > /etc/apache2/conf-available/static-cache.conf \
    && a2enconf static-cache

# Bawaan mod_deflate tidak mengompresi application/json, padahal itu
# tipe respons api/karya.php — ditambahkan supaya ikut terkompresi gzip.
RUN echo "AddOutputFilterByType DEFLATE application/json" > /etc/apache2/conf-available/deflate-json.conf \
    && a2enconf deflate-json
