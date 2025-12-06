from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html


class XRPVideosAdminSite(AdminSite):
    site_header = format_html(
        '<span style="font-weight: bold; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
        '-webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 24px;">xrpvideos Admin</span>'
    )
    site_title = "xrpvideos Admin Portal"
    index_title = "Welcome to xrpvideos Administration"
    
    def each_context(self, request):
        context = super().each_context(request)
        context['site_header'] = self.site_header
        return context


# Override the default admin site
admin.site.site_header = "xrpvideos Administration"
admin.site.site_title = "xrpvideos Admin Portal"
admin.site.index_title = "Platform Management Dashboard"
