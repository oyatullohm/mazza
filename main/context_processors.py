from django.urls import get_resolver

def url_patterns(request):
    resolver = get_resolver()
    urls = [str(pattern) for pattern in resolver.url_patterns]
    return {
        'all_urls': urls
    }