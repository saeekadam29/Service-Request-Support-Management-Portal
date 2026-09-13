from django.contrib import admin

from .models import Category, Ticket, Comment, TicketHistory


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('author', 'created_at')


class TicketHistoryInline(admin.TabularInline):
    model = TicketHistory
    extra = 0
    readonly_fields = ('actor', 'action', 'timestamp')
    can_delete = False


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'priority', 'status', 'customer', 'assigned_agent', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('title', 'description', 'id')
    autocomplete_fields = ('customer', 'assigned_agent')
    inlines = [CommentInline, TicketHistoryInline]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'created_at')
    search_fields = ('body',)


@admin.register(TicketHistory)
class TicketHistoryAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'actor', 'action', 'timestamp')
    list_filter = ('timestamp',)
