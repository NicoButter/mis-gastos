from django.conf import settings
from rest_framework import serializers


class HouseholdSelectionInput(serializers.Serializer):
    householdId = serializers.UUIDField()


class HouseholdInput(serializers.Serializer):
    name = serializers.CharField(max_length=120)
    termsVersion = serializers.CharField(max_length=32, required=False)

    def validate(self, attrs):
        active_version = settings.GASTIO_TERMS_VERSION or None
        accepted_version = attrs.get("termsVersion")
        if active_version and accepted_version != active_version:
            raise serializers.ValidationError(
                {"termsVersion": "Debés aceptar la versión vigente de los términos."}
            )
        if not active_version and accepted_version:
            raise serializers.ValidationError(
                {"termsVersion": "No hay una versión vigente de términos para aceptar."}
            )
        return attrs


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
    termsVersion = serializers.CharField(allow_null=True)
