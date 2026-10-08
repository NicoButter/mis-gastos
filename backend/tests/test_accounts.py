import pytest

from apps.accounts.models import User


@pytest.mark.django_db
def test_email_is_the_unique_login_identifier():
    user = User.objects.create_user("PERSONA@EXAMPLE.COM", "safe-password")
    assert user.email == "PERSONA@example.com"
    assert User.USERNAME_FIELD == "email"
    assert user.check_password("safe-password")
