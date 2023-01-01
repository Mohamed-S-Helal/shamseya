# -*- coding: utf-8 -*-
from odoo import http


# class Testmodule(http.Controller):
#     @http.route('/testmodule/testmodule', auth='public')
#     def index(self, **kw):
#         return "Hello, world"
#
#     @http.route('/testmodule/testmodule/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('testmodule.listing', {
#             'root': '/testmodule/testmodule',
#             'objects': http.request.env['testmodule.testmodule'].search([]),
#         })
#
#     @http.route('/testmodule/testmodule/objects/<model("testmodule.testmodule"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('testmodule.object', {
#             'object': obj
#         })
