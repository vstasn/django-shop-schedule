from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Shop, Daysoff
from itertools import groupby
from timeline.utils import timetostring

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "password")

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class ShopSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Shop
        fields = ("id", "title", "owner")

    def create(self, validated_data):
        shop = super(ShopSerializer, self).create(validated_data)
        shop.save()
        return shop

    def is_working(self, instance):
        return instance.is_working()

    def schedule(self, instance):
        def prepare_data(row):
            return {
                "from_time": timetostring(row["from_time"]),
                "to_time": timetostring(row["to_time"]),
            }

        entries = instance.timeline_entries.all().values(
            "from_time", "to_time", "day_of_week"
        )
        # group rows by day_of_week
        result = {
            k: list(each)
            for k, each in groupby(entries, key=lambda x: x["day_of_week"])
        }
        # update format
        return {day: list(map(prepare_data, row)) for day, row in result.items()}


class SchedulerBreaksSerialized(serializers.Serializer):
    from_time = serializers.TimeField(format="hh:mm", required=True)
    to_time = serializers.TimeField(format="hh:mm", required=True)


class ScheduleSerialized(serializers.Serializer):
    from_time = serializers.TimeField(format="hh:mm", required=True)
    to_time = serializers.TimeField(format="hh:mm", required=True)
    breaks = serializers.ListField(child=SchedulerBreaksSerialized(), required=False)


class ShopUpdateSerialized(serializers.ModelSerializer):
    day_of_week = serializers.IntegerField(required=True)
    is_working_day = serializers.BooleanField(required=True)
    working_schedule = ScheduleSerialized(required=False)

    class Meta:
        model = Shop
        fields = ("id", "day_of_week", "is_working_day", "working_schedule")

    def update_schedule(self, instance, validated_data):
        day_of_week = validated_data.get("day_of_week")
        is_working_day = validated_data.get("is_working_day", True)
        schedule = validated_data.get("working_schedule", {})
        return instance.update_schedule(day_of_week, is_working_day, schedule)

    def validate(self, attrs):
        if attrs["is_working_day"] and "working_schedule" not in attrs:
            raise serializers.ValidationError(
                "working_schedule can't be empty if is_working_day is True"
            )

        return super().validate(attrs)


class ShopCloseSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = Daysoff
        fields = ("id", "from_date", "to_date", "shop")

    def validate(self, attrs):
        """
        Check that from_date is before to_date.
        """
        if "from_date" in attrs and "to_date" in attrs:
            if attrs["from_date"] > attrs["to_date"]:
                raise serializers.ValidationError("finish must occur after start")
        return super().validate(attrs)
