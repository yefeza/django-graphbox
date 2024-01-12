# models
from django_graphbox.models import LoginCaptcha

# http response
from django.http import HttpResponse

# Create your views here.


def captcha_image(request):
    id = request.GET.get("id")
    # get captcha
    try:
        from captcha.image import ImageCaptcha

        captcha = LoginCaptcha.objects.get(captcha_id=id)
        if captcha.active and not captcha.image_generated:
            captcha.image_generated = True
            captcha.save()
            # return image
            image = ImageCaptcha(width=280, height=90)
            image_io = image.generate(captcha.captcha_value)
            return HttpResponse(image_io, content_type="image/png")
        else:
            return HttpResponse("Captcha no válido", status=400)
    except Exception as e:
        return HttpResponse("Captcha no válido", status=400)
