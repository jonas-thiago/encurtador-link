from ninja import Router
from .schemas import LinkSchema, UpdateLinkSchema
from .models import Links, Clicks
from django.shortcuts import get_list_or_404, redirect

shortener_router = Router()


@shortener_router.post('create/', response={200: LinkSchema, 409: dict})
def create(request, link_schema: LinkSchema):
    data = link_schema.to_model_data()

    token = data['token']
    redirect_link = data['redirect_link']
    expiration_time = data['expiration_time']
    max_uniques_cliques = data['max_uniques_cliques']

    if token and Links.objects.filter(token=token).exists():
        return 409, {'error': 'Token já existe, use outro'}

    link = Links(
        redirect_link=redirect_link,
        expiration_time=expiration_time,
        max_uniques_cliques=max_uniques_cliques,
        token=token
    )
    link.save()

    return 200, LinkSchema.from_model(link)


@shortener_router.get('/{token}', response={200: None, 404: dict})
def redirect_link(request, token):
    link = get_list_or_404(Links, token=token, active=True)

    if link.expired():
        return 404, {'error': 'Link Expirado!!!'}

    uniques_clicks = Clicks.objects.filter(
        link=link).values('ip').distinct().count()
    if link.max_uniques_cliques and uniques_clicks >= link.max_uniques_cliques:
        return 404, {'error': 'Link Expirado'}

    click = Clicks(
        link=link,
        ip=request.META['REMOTE_ADDR']
    )
    click.save()

    return redirect(link.redirect_link)


@shortener_router.put('/{link_id}', response={200: UpdateLinkSchema, 409: dict})
def update_link(request, link_id: int, link_schema: UpdateLinkSchema):
    link = get_list_or_404(Links, id=link_id)

    data = link_schema.dict()

    token = data['token']
    if token and Links.objects.filter(token=token).exists():
        return 409, {'error': 'Token já existe, use outro'}

    for field, value in data.items()
