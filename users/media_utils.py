from django.conf import settings


def cloudinary_configured():
    storage = getattr(settings, 'CLOUDINARY_STORAGE', {})
    return bool(
        storage.get('CLOUD_NAME')
        and storage.get('API_KEY')
        and storage.get('API_SECRET')
    )


def cloudinary_config_error():
    storage = getattr(settings, 'CLOUDINARY_STORAGE', {})
    name = (storage.get('CLOUD_NAME') or '').strip()
    key = (storage.get('API_KEY') or '').strip()
    secret = (storage.get('API_SECRET') or '').strip()
    if not name or not key:
        return (
            'Photo upload is not configured. Add CLOUDINARY_CLOUD_NAME and '
            'CLOUDINARY_API_KEY to joblink-backend/.env, then restart Django.'
        )
    if not secret:
        return (
            'Cloudinary API secret is missing. Open your Cloudinary dashboard '
            '(Settings -> API Keys), copy the API Secret into '
            'CLOUDINARY_API_SECRET in joblink-backend/.env, then restart Django.'
        )
    return 'Photo upload is not configured.'


def upload_image(file, *, folder, public_id=None, transformation=None):
    """Upload a file to Cloudinary and return the secure URL."""
    if not cloudinary_configured():
        raise ValueError(cloudinary_config_error())

    import cloudinary.uploader

    options = {'folder': folder}
    if public_id:
        options['public_id'] = public_id
        options['overwrite'] = True
    if transformation:
        options['transformation'] = transformation

    result = cloudinary.uploader.upload(file, **options)
    return result['secure_url']
