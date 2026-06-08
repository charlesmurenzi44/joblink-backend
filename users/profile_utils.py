from rest_framework.exceptions import PermissionDenied

PROFILE_PHOTO_REQUIRED_MSG = (
    'A profile photo is required. Upload one in Profile before continuing.'
)


def user_has_profile_photo(user) -> bool:
    photo = getattr(user, 'profile_photo', None) or ''
    return bool(str(photo).strip())


def ensure_profile_photo(user) -> None:
    if not user_has_profile_photo(user):
        raise PermissionDenied(PROFILE_PHOTO_REQUIRED_MSG)
