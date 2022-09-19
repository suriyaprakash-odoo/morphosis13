# -*- coding: utf-8 -*-

import json

from odoo.http import Controller, route, request
import logging
_logger = logging.getLogger(__name__)


class ReportController(Controller):
    @route([
        '/zebra/report/<converter>/<reportname>',
        '/zebra/report/<converter>/<reportname>/<docids>',
    ], type='json')
    def report_routes_cusrome(self, reportname, docids=None, **data):
        context = dict(request.env.context)
        lang_id = 'fr_FR'
        
        
        if docids:
            docids = [int(i) for i in docids.split(',')]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            data['context'] = json.loads(data['context'])
            if data.get('lang_id', ""):
#                 del data['context']['lang']
                lang_id = data.get('lang_id', "")
            context.update(data['context'])
            
        if data.get('lang_id', ""):
            lang_id = data.get('lang_id', "")
            
        _logger.info("@ Context and data :%s%s",str(context),str(data))

        data = []
        if reportname == 'label_zebra_printer.report_donor_barcode_label':
            for donor_container in request.env['project.container'].with_context(lang=lang_id).browse(docids):
                _logger.info("@ DONOR CONTAINER ID {} ***".donor_container)
                _logger.info("@ DONOR CONTAINER ID {} ***".donor_container.main_product_id.name)
                _logger.info("@ DONOR CONTAINER ID {} ***".donor_container.sub_product_id.name)

                data.append({
                        'project_name' : donor_container.project_id.name,
                        'gross_weight' : donor_container.gross_weight,
                        'tare_weight' : donor_container.extra_tare if donor_container.extra_tare != 0.00 else donor_container.container_type_id.tare_weight,
                        'product' : donor_container.main_product_id.name,
                        'sub_product' : donor_container.sub_product_id.name,
                        'description' : donor_container.description
                    })
                _logger.info("@ DATA:%s",data)
                print(data)
        elif reportname == 'stock.report_location_barcode':
            for location in request.env['stock.location'].with_context(lang=lang_id).browse(docids):
                data.append({
                    'name': location.name,
                    'barcode': location.barcode,
                })
        elif reportname == 'product.report_productlabel':
            for product in request.env['product.product'].with_context(lang=lang_id).browse(docids):
                ratp = False
                if product.ref_ratp:
                    ratp = str(product.ref_ratp) + ' / ' + str(product.name)
                else:
                    ratp = product.name
                if ratp:
                    data.append({
                        'name': '[' + str(product.default_code)+']' + ' '+product.name,
                        'product_name': product.name,
                        'barcode': product.default_code,
                        'weight': str(product.weight),
                        'location_name': product.get_label_location(product=True),
                        'ref_ratp': ratp,
                        'uom': product.uom_id.name,
                        'from_ratp':'yes',
                        'reportname':reportname,
                    })
                else:
                    data.append({
                        'name': product.name,
                        'barcode': product.default_code,
                        'default_code': product.default_code,
                        'weight': str(product.weight),
                        'location_name': product.get_label_location(product=True),
                        'from_ratp':'no',
                        'reportname':reportname,
                    })    
                
        elif reportname == 'custom_product.ratp_report_productlabel':
            for product in request.env['product.template'].with_context(lang=lang_id).browse(docids):
                if product.ref_ratp:
                    ratp = str(product.ref_ratp) + ' / ' + str(product.name)
                else:
                    ratp = product.name
                data.append({
                    'name': '[' + str(product.default_code)+']' + ' '+product.name,
                    'product_name': product.name,
                    'barcode': product.default_code,
                    'weight': str(product.weight),
                    'location_name': product.get_label_location(product=False),
                    'ref_ratp': ratp,
                    'uom': product.uom_id.name,
                    'from_ratp':'yes',
                    'reportname':reportname,
                })
        else:
            for product in request.env['product.template'].with_context(lang=lang_id).browse(docids):
                data.append({
                    'name': product.name,
                    'barcode': product.default_code,
                    'default_code': product.default_code,
                    'weight': str(product.weight),
                    'location_name': product.get_label_location(product=False),
                    'from_ratp':'no',
                    'reportname':reportname,
                })     
        print(data) 
        return {'data': data}
