from django.db import models
from stores.models import Store
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile
from storages.backends.s3boto3 import S3Boto3Storage

# Create your models here.
class MediaS3Storage(S3Boto3Storage):
    location = "qr_img"        
    file_overwrite = False    # 같은 이름 덮어쓰기 방지

class Coupon(models.Model):
    coupon_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    coupon_name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    qr_code_image = models.ImageField(upload_to='', null=True, blank=True, storage=MediaS3Storage())

    def save(self, *args, **kwargs):
        if not self.qr_code_image:
            img = qrcode.make(self.code)
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            self.qr_code_image.save(f"{self.code}.png", ContentFile(buf.getvalue()), save=False)
        super().save(*args, **kwargs)