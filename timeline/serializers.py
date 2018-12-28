from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Shop, Daysoff
from itertools import groupby
from timeline.schedule import from_str_to_time

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password')

    def create(self, validated_data):
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class ShopSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = Shop
        fields = ('id', 'title', 'owner', )

    def create(self, validated_data):
        shop = super(ShopSerializer, self).create(validated_data)
        shop.save()
        return shop

    def is_working(self, instance):
        return instance.is_working()

    def schedule(self, instance):
        result = {}
        entries = instance.timeline_entries.all().values()
        d = {k: list(each) for k, each in groupby(entries, key=lambda x: x['day_of_week'])}

        for day_of_week, rows in d.items():
            working_hours = []
            for row in rows:
                working_hours.append({
                    'from_time': row['from_time'],
                    'to_time': row['to_time'],
                })
            result[day_of_week] = working_hours

        return result


class ShopUpdateSerialized(serializers.ModelSerializer):
    day_of_week = serializers.IntegerField(required=True)
    from_time = serializers.CharField(required=True)
    to_time = serializers.CharField(required=True)
    breaks = serializers.JSONField(required=False,)

    class Meta:
        model = Shop
        fields = ('id', 'day_of_week', 'from_time', 'to_time', 'breaks')

    def update_schedule(self, instance, validated_data):
        day_of_week = validated_data.get('day_of_week')
        from_time = from_str_to_time(validated_data.get('from_time'))
        to_time = from_str_to_time(validated_data.get('to_time'))
        breaks = validated_data.get('breaks', {})
        return instance.update_schedule(day_of_week, from_time, to_time, breaks)


class ShopCloseSerializer(serializers.ModelSerializer):
    shop = serializers.PrimaryKeyRelatedField(many=False, read_only=True)

    class Meta:
        model = Daysoff
        fields = ('id', 'from_date', 'to_date', 'shop')

    def validate(self, data):
        """
        Check that start is before finish.
        """
        if 'from_date' in data and 'to_date' in data:
            if data['from_date'] > data['to_date']:
                raise serializers.ValidationError("finish must occur after start")
        return data
