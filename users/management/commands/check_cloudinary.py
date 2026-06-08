import io

from django.core.management.base import BaseCommand

from users.media_utils import cloudinary_config_error, cloudinary_configured, upload_image


class Command(BaseCommand):
    help = 'Verify Cloudinary credentials and test a small upload'

    def handle(self, *args, **options):
        if not cloudinary_configured():
            self.stderr.write(self.style.ERROR(cloudinary_config_error()))
            return

        self.stdout.write('Cloudinary credentials loaded.')

        # Minimal valid 1x1 PNG
        png = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
            b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
            b'\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01'
            b'\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        try:
            url = upload_image(
                io.BytesIO(png),
                folder='joblink/healthcheck',
                public_id='connectivity_test',
            )
        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(f'Upload failed: {exc}'),
            )
            return

        self.stdout.write(self.style.SUCCESS('Upload OK'))
        self.stdout.write(url)
