from django.db import models
from stores.models import Store
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

# Create your models here.
class Coupon(models.Model):
    coupon_id = models.AutoField(primary_key=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE)
    coupon_name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    qr_code_image = models.ImageField(upload_to='qr_img/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.qr_code_image:
            qr_img=qrcode.make(self.code)
            qr_img_bytes=BytesIO()
            qr_img.save(qr_img_bytes, format='PNG')

            self.qr_code_image.save(f'{self.code}.png', ContentFile(qr_img_bytes.getvalue()), save=False)

            super().save(*args, **kwargs)