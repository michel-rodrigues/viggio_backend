from django.contrib import admin
from django.contrib.auth import get_user_model


User = get_user_model()


class UserAdmin(admin.ModelAdmin):

    search_fields = ['email']

    def save_model(self, request, obj, form, change):
        if change:
            orig_obj = User.objects.get(pk=obj.pk)
            if not obj.password == orig_obj.password:
                if request.user.has_perm('accounts.change_password'):
                    obj.set_password(obj.password)
                else:
                    raise Exception(f'{request.user.email} não tem permissão para alterar senhas.')
        obj.save()


admin.site.register(User, UserAdmin)
