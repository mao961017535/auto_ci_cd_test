from django.db import models


class ReviewBaseModels(models.Model):
    """
    需要进行权限验证和审查的基类
    """
    created_at = models.CharField(max_length=20, null=True)
    created_by = models.ForeignKey('User', models.PROTECT, related_name='created', null=True)
    deleted_at = models.CharField(max_length=20, null=True)
    deleted_by = models.ForeignKey('User', models.PROTECT, related_name='deleted', null=True)

    class Meta:
        abstract = True
