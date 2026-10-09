from rest_framework import serializers


class HouseholdSelectionInput(serializers.Serializer):
    householdId = serializers.UUIDField()


class HouseholdInput(serializers.Serializer):
    name = serializers.CharField(max_length=120)


class MembershipOutput(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    role = serializers.CharField()


class SelectionOutput(serializers.Serializer):
    activeHousehold = MembershipOutput()


class UserOutput(serializers.Serializer):
    id = serializers.UUIDField()
    email = serializers.EmailField()
    displayName = serializers.CharField()
    avatarUrl = serializers.URLField(allow_null=True)


class SessionOutput(serializers.Serializer):
    user = UserOutput()
    households = MembershipOutput(many=True)
    activeHousehold = MembershipOutput(allow_null=True)


class CsrfOutput(serializers.Serializer):
    csrfToken = serializers.CharField()


class AuthConfigurationOutput(serializers.Serializer):
    googleLoginEnabled = serializers.BooleanField()
