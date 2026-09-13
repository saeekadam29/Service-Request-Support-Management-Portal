from django.contrib.auth.models import User
from rest_framework import serializers

from tickets.models import Ticket, Category, Comment, TicketHistory


class UserMiniSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source='profile.role', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'role']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class CommentSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'ticket', 'author', 'body', 'created_at']
        read_only_fields = ['author', 'created_at']


class TicketHistorySerializer(serializers.ModelSerializer):
    actor = UserMiniSerializer(read_only=True)

    class Meta:
        model = TicketHistory
        fields = ['id', 'action', 'actor', 'timestamp']


class TicketSerializer(serializers.ModelSerializer):
    """
    Used for list/create/update. Nested read-only representations for
    customer/agent/category keep responses informative without extra requests,
    while write operations use the plain FK id fields below.
    """
    customer_detail = UserMiniSerializer(source='customer', read_only=True)
    assigned_agent_detail = UserMiniSerializer(source='assigned_agent', read_only=True)
    category_detail = CategorySerializer(source='category', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'title', 'description', 'category', 'category_detail',
            'priority', 'status', 'customer', 'customer_detail',
            'assigned_agent', 'assigned_agent_detail', 'resolution_notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['customer', 'created_at', 'updated_at']

    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long.")
        return value


class TicketDetailSerializer(TicketSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    history = TicketHistorySerializer(many=True, read_only=True)

    class Meta(TicketSerializer.Meta):
        fields = TicketSerializer.Meta.fields + ['comments', 'history']
