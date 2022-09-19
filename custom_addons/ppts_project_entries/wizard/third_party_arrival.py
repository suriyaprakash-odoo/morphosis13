from odoo import fields, models, api, _
from datetime import timedelta, datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class ThirdPartyPlan(models.TransientModel):
    _name = 'third.party.arrival'

    project_id = fields.Many2one("project.entries", string="Project")
    arrival_date =fields.Date("Arrival Date")
    note = fields.Text("Help Note")
    exist = fields.Boolean("Already Exist?")
    action = fields.Selection([('delete' , 'Delete previous request and create new request'),('update' , 'Update date of the previous request')], string="Action")
    transport_id = fields.Char(string="Existing Request")
    planned_date = fields.Date("Previous Planned Date")

    expected_delivery_start_time = fields.Float('Time Duration')
    expected_delivery_end_time = fields.Float('Time Duration')

    def create_transport_request(self):
        picking_id = self.env["stock.picking"].search([('project_entry_id', '=', self.project_id.id)], limit=1)

        if self.project_id.no_of_container > 0:
            container_type = 'specified'
        else:
            container_type = 'not_specified'

        logistics_id = self.env['logistics.management'].create({
            # 'partner_id': self.partner_id.id,
            'company_id': self.project_id.company_id.id,
            'pickup_partner_id': self.project_id.pickup_location_id.id,
            'vendor_ref': self.project_id.partner_ref,
            'pickup_street': self.project_id.pickup_location_id.street,
            'pickup_street2': self.project_id.pickup_location_id.street2,
            'pickup_zip': self.project_id.pickup_location_id.zip,
            'pickup_city': self.project_id.pickup_location_id.city,
            'pickup_state_id': self.project_id.pickup_location_id.state_id.id,
            'pickup_countries_id': self.project_id.pickup_location_id.country_id.id,
            'gross_weight': picking_id.gross_weight,
            'logistics_for': 'purchase',
            'origin': self.project_id.id,
            'delivery_partner_id': self.project_id.company_id.partner_id.id,
            'delivery_street': self.project_id.company_id.partner_id.street,
            'delivery_street2': self.project_id.company_id.partner_id.street2,
            'delivery_zip': self.project_id.company_id.partner_id.zip,
            'delivery_city': self.project_id.company_id.partner_id.city,
            'delivery_state_id': self.project_id.company_id.partner_id.state_id.id,
            'delivery_countries_id': self.project_id.company_id.partner_id.country_id.id,
            'pickup_date_type': 'specific',
            'pickup_date': self.project_id.estimated_collection_date,
            'expected_delivery': self.arrival_date,
            'expected_delivery_start_time': self.expected_delivery_start_time,
            'expected_delivery_end_time': self.expected_delivery_end_time,
            'container_count': container_type,
            'no_of_container': self.project_id.no_of_container,
            'status': 'approved',
            'is_3rd_party': True
        })

        seq_date = None
        if logistics_id.create_date:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(logistics_id.create_date))
        logistics_id.name = logistics_id.origin.name + '/' + self.env['ir.sequence'].next_by_code('logistics.management', sequence_date=seq_date) or '/'

        start_date = datetime.strptime(str(logistics_id.expected_delivery)+" 00:00:00", '%Y-%m-%d %H:%M:%S')
        duration = 1
        if logistics_id.expected_delivery_start_time and logistics_id.expected_delivery_end_time:

            stime = logistics_id.expected_delivery_start_time

            hours = int(stime)
            minutes = (stime*60) % 60
            # seconds = (stime*3600) % 60

            start_time = "%d:%02d" % (hours, minutes)

            start_date = str(logistics_id.expected_delivery)+ " "+start_time
            start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M')

            etime = logistics_id.expected_delivery_end_time

            hours = int(etime)
            minutes = (etime*60) % 60
            # seconds = (etime*3600) % 60

            end_time = "%d:%02d" % (hours, minutes)

            end_date = str(logistics_id.expected_delivery)+ " "+end_time
            end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M')
            
            FMT = '%Y-%m-%d %H:%M'
            tdelta = end_date - start_date

            duration = abs(tdelta.total_seconds()/3600)


        x = datetime.strptime(str(start_date), '%Y-%m-%d %H:%M:%S')
        stop_date = x + timedelta(hours=duration)

        calender_obj = self.env['calendar.event'].create({
                'name' : logistics_id.name,
                'start' : start_date,
                'stop' : stop_date,
                'duration' : duration,
                'state' : 'draft',
                'logistics_id' : logistics_id.id,
                'logistics_partner_id' : logistics_id.partner_id.id,
                'logistics_pickup_partner_id' : logistics_id.pickup_partner_id.id,
                'logistics_delivery_partner_id' : logistics_id.delivery_partner_id.id,
                'pickup_state_id' : logistics_id.pickup_state_id.id,
                'delivery_state_id' : logistics_id.delivery_state_id.id,
                'gross_weight' : logistics_id.gross_weight,
                'pickup_date_type' : logistics_id.pickup_date_type,
                'pickup_date' : logistics_id.pickup_date,
                'pickup_earliest_date' : logistics_id.pickup_earliest_date,
                'pickup_latest_date' : logistics_id.pickup_latest_date,
                'expected_delivery' : logistics_id.expected_delivery,
                'logistics_calendar' : True
            })

    def plan_arrival(self):
        # if not self.exist and self.project_id.transport_request_count:
        #     transports = self.env["logistics.management"].search([('origin','=',self.project_id.id)],limit=1)
        #     for tr in transports:
        #         if tr.expected_delivery == self.arrival_date:
        #             raise UserError('Transport Request is already created for this date')
        if self.exist:
            if self.action:
                if self.action == 'delete':
                    transport = self.env["logistics.management"].search([('origin','=',self.project_id.id)])
                    if transport:
                        transport.unlink()
                    self.create_transport_request()
                else:
                    transport = self.env["logistics.management"].search([('origin','=',self.project_id.id)])
                    if transport:
                        transport.expected_delivery = self.arrival_date
            else:
                raise UserError('Please select any action to continue!')

        else:
            self.create_transport_request()



