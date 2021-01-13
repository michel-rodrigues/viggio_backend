from rest_framework_simplejwt.tokens import RefreshToken


def get_new_tokens(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)
