from django.urls import reverse


def jwt_obtain_pair_url():
    return reverse("token_obtain_pair")


def jwt_refresh_url():
    return reverse("token_refresh")


def jwt_verify_url():
    return reverse("token_verify")
