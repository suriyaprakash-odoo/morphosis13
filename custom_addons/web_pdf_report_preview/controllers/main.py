# -*- coding: utf-8 -*-



from odoo import http, tools
from odoo.addons.web.controllers.main import serialize_exception, ReportController

class WebPdfReports(ReportController):

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token, context=None):
        result = super(WebPdfReports, self).report_download(data, token, context)
        result.headers['Content-Disposition'] = result.headers['Content-Disposition'].replace('attachment', 'inline')
        return result




