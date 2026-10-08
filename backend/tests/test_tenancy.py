import pytest
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.accounts.models import User
from apps.households.models import Household, HouseholdMembership
from apps.households.selectors import tenant_queryset
from apps.households.services import require_household_permission, resolve_active_membership


@pytest.mark.django_db
def test_user_cannot_resolve_a_household_without_an_active_membership():
    member = User.objects.create_user("member@example.com", "password")
    outsider = User.objects.create_user("outsider@example.com", "password")
    home = Household.objects.create(name="Hogar A")
    HouseholdMembership.objects.create(user=member, household=home)

    assert resolve_active_membership(member, home.id).household_id == home.id
    with pytest.raises(NotFound):
        resolve_active_membership(outsider, home.id)


@pytest.mark.django_db
def test_tenant_queryset_excludes_another_household_even_for_a_multi_household_user():
    user = User.objects.create_user("multi@example.com", "password")
    first_home = Household.objects.create(name="Hogar Uno")
    second_home = Household.objects.create(name="Hogar Dos")
    first_membership = HouseholdMembership.objects.create(user=user, household=first_home)
    HouseholdMembership.objects.create(user=user, household=second_home)

    visible = tenant_queryset(HouseholdMembership.objects.all(), first_membership)
    assert list(visible.values_list("household_id", flat=True)) == [first_home.id]


@pytest.mark.django_db
def test_limited_entry_member_cannot_manage_members():
    user = User.objects.create_user("limited@example.com", "password")
    membership = HouseholdMembership.objects.create(
        user=user,
        household=Household.objects.create(name="Hogar B"),
        role=HouseholdMembership.Role.LIMITED_ENTRY,
    )
    with pytest.raises(PermissionDenied):
        require_household_permission(membership, "member.manage")
