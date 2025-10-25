from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Tell SimpleJWT that our login identifier is the `email` field
    username_field = "email"
