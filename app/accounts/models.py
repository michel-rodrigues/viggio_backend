from django.contrib.auth.models import AbstractUser


class User(AbstractUser):

    class Meta:
        permissions = (
            ('change_password', 'Can change user password.'),
        )

    def save(self, *args, **kwargs):
        self.username = self.email
        super().save(*args, **kwargs)

    @property
    def is_talent(self):
        return 'talent' if hasattr(self, 'talent') else 'customer'
