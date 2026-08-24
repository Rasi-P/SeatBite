from rest_framework import serializers
from .models import Screen, Seat, Venue


class VenueSerializer(serializers.ModelSerializer):
    screen_count = serializers.SerializerMethodField()

    class Meta:
        model = Venue
        fields = "__all__"

    def get_screen_count(self, obj):
        return obj.screens.filter(is_deleted=False).count()


class ScreenSerializer(serializers.ModelSerializer):
    venue_name = serializers.CharField(source="venue.name", read_only=True)
    seat_count = serializers.IntegerField(source="seats.count", read_only=True)

    class Meta:
        model = Screen
        fields = "__all__"
        read_only_fields = ["is_deleted", "deleted_at", "deleted_by"]
        validators = []

    def validate_total_rows(self, value):
        if not 1 <= value <= 26:
            raise serializers.ValidationError("Rows must be between 1 and 26.")
        return value

    def validate_total_columns(self, value):
        if not 1 <= value <= 50:
            raise serializers.ValidationError("Seats per row must be between 1 and 50.")
        return value

    def validate(self, attrs):
        venue = attrs.get("venue", self.instance.venue if self.instance else None)
        screen_number = attrs.get(
            "screen_number", self.instance.screen_number if self.instance else None
        )
        if venue and screen_number:
            duplicate = Screen.objects.filter(
                venue=venue,
                screen_number=screen_number,
                is_deleted=False,
            )
            if self.instance:
                duplicate = duplicate.exclude(pk=self.instance.pk)
            if duplicate.exists():
                raise serializers.ValidationError(
                    {"screen_number": "This screen number is already active at the venue."}
                )
        if self.instance:
            immutable_changes = {
                field: "This field cannot be changed after seats and QR codes are generated."
                for field in ("venue", "total_rows", "total_columns")
                if field in attrs and attrs[field] != getattr(self.instance, field)
            }
            if immutable_changes:
                raise serializers.ValidationError(immutable_changes)
        return attrs


class SeatSerializer(serializers.ModelSerializer):
    screen_name = serializers.CharField(source="screen.name", read_only=True)
    venue_name = serializers.CharField(source="screen.venue.name", read_only=True)

    class Meta:
        model = Seat
        fields = "__all__"
        read_only_fields = ["qr_token"]


class SeatPublicSerializer(serializers.ModelSerializer):
    venue_id = serializers.IntegerField(source="screen.venue_id")
    screen = serializers.CharField(source="screen.name")
    screen_number = serializers.IntegerField(source="screen.screen_number")
    venue = serializers.CharField(source="screen.venue.name")
    venue_code = serializers.CharField(source="screen.venue.code")

    class Meta:
        model = Seat
        fields = ["venue_id", "venue", "venue_code", "screen", "screen_number", "row_label", "seat_number", "seat_code"]
