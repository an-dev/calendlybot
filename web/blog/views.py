from django.template.response import TemplateResponse
from django.views import generic
from django.views.decorators.http import require_http_methods

from web.blog.models import Post


# class PostList(generic.ListView):
#     queryset = Post.objects.filter(status=1).order_by('-created_on')
#     template_name = 'blog/index.html'


@require_http_methods(["GET"])
def PostListView(request):
    posts = Post.objects.filter(status=1).order_by('-created_on')
    return TemplateResponse(request, 'blog/index.html', {'post_list': posts, 'blog_nav': True})


# class PostDetailView(generic.DetailView):
#     model = Post
#     template_name = 'blog/post.html'


@require_http_methods(["GET"])
def PostDetailView(request, slug):
    post = Post.objects.get(slug=slug)
    return TemplateResponse(request, 'blog/post.html', {'post': post, 'blog_nav': True})
