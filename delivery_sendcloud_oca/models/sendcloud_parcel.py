# Copyright 2024 Onestein (<https://www.onestein.nl>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl)

import base64

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class SendcloudParcel(models.Model):
    _name = "sendcloud.parcel"
    _inherit = ["sendcloud.mixin", "mail.thread", "mail.activity.mixin"]
    _description = "Sendcloud Parcel"

    @api.model
    def _selection_parcel_statuses(self):
        statuses = self.env["sendcloud.parcel.status"].search([])
        return [(status.sendcloud_code, status.message) for status in statuses]

    partner_name = fields.Char()
    address = fields.Char()
    address_2 = fields.Char(help="An apartment or floor number.")
    house_number = fields.Char()
    street = fields.Char()
    city = fields.Char()
    postal_code = fields.Char()
    company_name = fields.Char()
    country_iso_2 = fields.Char()
    email = fields.Char()
    telephone = fields.Char()
    name = fields.Char(required=True)
    sendcloud_code = fields.Integer(required=True)
    label = fields.Binary(related="attachment_id.datas", string="File Content")
    tracking_url = fields.Char()
    tracking_number = fields.Char()
    label_printer_url = fields.Char()
    return_portal_url = fields.Char()
    external_reference = fields.Char(
        help="A field to use as a reference for your order."
    )
    insured_value = fields.Float(help="Insured Value is in Euro currency.")
    total_insured_value = fields.Float(help="Total Insured Value is in Euro currency.")
    weight = fields.Float(help="Weight unit of measure is KG.")
    is_return = fields.Boolean(readonly=True)
    collo_count = fields.Integer(
        help="A number indicating the number of collos within a shipment. "
        "For non-multi-collo shipments, this value will always be 1."
    )
    collo_nr = fields.Integer(
        help="A number indicating the collo number within a shipment. For a "
        "non-multi-collo shipment, this value will always be 0. In a multi-collo"
        " shipment with 3 collos, this number will range from 0 to 2."
    )
    colli_uuid = fields.Char()
    colli_tracking_number = fields.Char(
        help="Multi-collo only. This is a tracking number assigned by the carrier to"
        " identify the entire multi-collo shipment."
    )
    external_shipment_id = fields.Char()
    external_order_id = fields.Char()
    shipping_method = fields.Integer()
    shipment_uuid = fields.Char()
    to_post_number = fields.Text()
    parcel_item_ids = fields.One2many("sendcloud.parcel.item", "parcel_id")
    documents = fields.Text(
        string="Documents Data",
        help="An array of documents. A parcel can contain multiple documents, for "
        "instance labels and a customs form. This field returns an array of all"
        " the available documents for this parcel.",
    )
    note = fields.Text()
    type = fields.Char(
        help="Returns either ‘parcel’ or ‘letter’ by which you can determine the type"
        " of your shipment."
    )
    to_state = fields.Char()
    order_number = fields.Char()
    customs_invoice_nr = fields.Char()
    shipment = fields.Char(string="Cached Shipment")
    shipment_id = fields.Many2one("delivery.carrier", compute="_compute_shipment_id")
    reference = fields.Char()
    to_service_point = fields.Char(
        help="The id of service point to which the shipment is going to be shipped."
    )
    sendcloud_customs_shipment_type = fields.Selection(
        selection="_get_sendcloud_customs_shipment_type"
    )
    picking_id = fields.Many2one("stock.picking")
    package_id = fields.Many2one("stock.quant.package")
    sendcloud_status = fields.Selection(
        selection=lambda self: self._selection_parcel_statuses(), readonly=True
    )
    carrier = fields.Char()
    company_id = fields.Many2one(
        "res.company",
        required=True,
        compute="_compute_company_id",
        store=True,
        readonly=False,
    )
    brand_id = fields.Many2one(
        "sendcloud.brand", compute="_compute_brand_id", store=True, readonly=False
    )
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        ondelete="cascade",
    )
    document_ids = fields.One2many(
        "sendcloud.parcel.document",
        "parcel_id",
        string="Documents",
    )
    label_print_status = fields.Selection(
        [
            ("generated", "Generated"),
            ("printed", "Printed"),
        ],
        default="generated",
    )

    def action_parcel_documents(self):
        self.mapped("document_ids").unlink()
        skip_get_parcel_document = self.env.context.get("skip_get_parcel_document")
        for parcel in self:
            doc_vals = []
            for document_data in safe_eval(parcel.documents or "[]"):
                doc_vals.append(
                    {
                        "name": document_data["type"],
                        "size": document_data["size"],
                        "link": document_data.get("link"),
                        "parcel_id": parcel.id,
                    }
                )
            parcel.document_ids = self.env["sendcloud.parcel.document"].create(doc_vals)
            if not skip_get_parcel_document:
                parcel.document_ids._generate_parcel_document()

    @api.depends("shipment")
    def _compute_shipment_id(self):
        for parcel in self:
            shipment_data = safe_eval(parcel.shipment or "{}")
            shipment_code = shipment_data.get("id")
            domain = parcel._get_shipment_domain_by_code(shipment_code)
            parcel.shipment_id = self.env["delivery.carrier"].search(domain, limit=1)

    def _get_shipment_domain_by_code(self, shipment_code):
        self.ensure_one()
        return [
            ("company_id", "=", self.company_id.id),
            ("sendcloud_code", "=", shipment_code),
        ]

    @api.depends("picking_id.company_id")
    def _compute_company_id(self):
        for parcel in self:
            parcel.company_id = parcel.picking_id.company_id or parcel.company_id

    @api.depends("company_id")
    def _compute_brand_id(self):
        for parcel in self:
            brands = parcel.company_id.sendcloud_brand_ids
            # TODO only brands with domain?
            parcel.brand_id = fields.first(brands)

    @api.model
    def _prepare_sendcloud_parcel_from_response(self, parcel):
        res = {
            "name": parcel.get("id"),
            "sendcloud_code": parcel.get("id"),
            "carrier": parcel.get("carrier", {}).get("code") or parcel.get("carrier"),
        }
        if parcel.get("status", {}).get("id"):
            res["sendcloud_status"] = str(parcel.get("status", {}).get("id"))
        if parcel.get("tracking_number"):
            res["tracking_number"] = parcel.get("tracking_number")
        if parcel.get("tracking_url"):
            res["tracking_url"] = parcel.get("tracking_url")
        if parcel.get("label", {}).get("label_printer"):
            res["label_printer_url"] = parcel.get("label", {}).get("label_printer")
        if parcel.get("external_reference"):
            res["external_reference"] = parcel.get("external_reference", "")
        if parcel.get("collo_count"):
            res["collo_count"] = parcel.get("collo_count")
        if parcel.get("collo_nr"):
            res["collo_nr"] = parcel.get("collo_nr")
        if parcel.get("colli_uuid"):
            res["colli_uuid"] = parcel.get("colli_uuid")
        if parcel.get("colli_tracking_number"):
            res["colli_tracking_number"] = parcel.get("colli_tracking_number")
        customs_shipment_type = parcel.get("customs_shipment_type")
        res["sendcloud_customs_shipment_type"] = (
            str(customs_shipment_type) if customs_shipment_type else False
        )
        res["to_service_point"] = parcel.get("to_service_point")
        res["reference"] = parcel.get("reference")
        res["shipment"] = parcel.get("shipment")
        res["customs_invoice_nr"] = parcel.get("customs_invoice_nr")
        res["order_number"] = parcel.get("order_number")
        res["to_state"] = parcel.get("to_state")
        res["type"] = parcel.get("type")
        res["note"] = parcel.get("note")
        res["documents"] = parcel.get("documents")
        res["to_post_number"] = parcel.get("to_post_number")
        res["shipment_uuid"] = parcel.get("shipment_uuid")
        res["shipping_method"] = parcel.get("shipping_method")
        res["external_order_id"] = parcel.get("external_order_id")
        res["external_shipment_id"] = parcel.get("external_shipment_id")
        res["is_return"] = parcel.get("is_return")
        res["weight"] = parcel.get("weight")
        res["total_insured_value"] = parcel.get("total_insured_value")
        res["insured_value"] = parcel.get("insured_value")
        res["return_portal_url"] = parcel.get("return_portal_url")
        res["partner_name"] = parcel.get("name")
        res["address"] = parcel.get("address")
        if parcel.get("address_2"):
            res["address_2"] = parcel.get("address_2")
        if parcel.get("address_divided"):
            res["house_number"] = parcel["address_divided"].get(
                "house_number"
            ) or parcel.get("house_number")
            res["street"] = parcel["address_divided"].get("street") or parcel.get(
                "street"
            )
        else:
            res["house_number"] = parcel.get("house_number")
            res["street"] = parcel.get("street")
        res["city"] = parcel.get("city")
        res["postal_code"] = parcel.get("postal_code")
        res["company_name"] = parcel.get("company_name")
        res["country_iso_2"] = parcel.get("country", {}).get("iso_2")
        res["email"] = parcel.get("email")
        res["telephone"] = parcel.get("telephone")
        if isinstance(parcel.get("parcel_items"), list):
            res["parcel_item_ids"] = [(5, False, False)] + [
                (0, False, self._prepare_sendcloud_parcel_item_from_response(values))
                for values in parcel.get("parcel_items")
            ]
        return res

    def action_get_parcel_label(self):
        self.ensure_one()
        if not self.label_printer_url:
            raise UserError(_("Label not available: no label printer url provided."))
        self._generate_parcel_labels()

    def _generate_parcel_labels(self):
        for parcel in self.filtered(lambda p: p.label_printer_url):
            integration = parcel.company_id.sendcloud_default_integration_id
            label = integration.get_parcel_label(parcel.label_printer_url)
            filename = parcel._generate_parcel_label_filename()
            attachment_id = self.env["ir.attachment"].create(
                {
                    "name": filename,
                    "res_id": parcel.id,
                    "res_model": parcel._name,
                    "datas": base64.b64encode(label),
                    "description": parcel.name,
                }
            )
            parcel.attachment_id = attachment_id

    def _generate_parcel_label_filename(self):
        self.ensure_one()
        if not self.name.lower().endswith(".pdf"):
            return self.name + ".pdf"
        return self.name

    def action_get_return_portal_url(self):
        for parcel in self:
            code = parcel.sendcloud_code
            integration = parcel.company_id.sendcloud_default_integration_id
            response = integration.get_return_portal_url(code)
            if response.get("url") is None:
                parcel.return_portal_url = "None"
            else:
                parcel.return_portal_url = response.get("url")

    @api.model
    def sendcloud_create_update_parcels(self, parcels_data, company_id):
        # All records
        all_records = self.search([("company_id", "=", company_id)])

        # Existing records
        existing_records = all_records.filtered(
            lambda c: c.sendcloud_code in [record["id"] for record in parcels_data]
        )

        # Existing records map (internal code -> existing record)
        existing_records_map = {}
        for existing in existing_records:
            if existing.sendcloud_code not in existing_records_map:
                existing_records_map[existing.sendcloud_code] = self.env[
                    "sendcloud.parcel"
                ]
            existing_records_map[existing.sendcloud_code] |= existing

        # Created records
        vals_list = []
        for record in parcels_data:
            vals = self._prepare_sendcloud_parcel_from_response(record)
            vals["company_id"] = company_id
            if record["id"] in existing_records_map:
                existing_records_map[record["id"]].write(vals)
            else:
                vals_list += [vals]
        new_records = self.create(vals_list)
        new_records.action_get_return_portal_url()

        return existing_records + new_records

    @api.model
    def sendcloud_sync_parcels(self):
        for company in self.env["res.company"].search([]):
            integration = company.sendcloud_default_integration_id
            if integration:
                parcels = integration.get_parcels()
                self.sendcloud_create_update_parcels(parcels, company.id)

    def button_sync_parcel(self):
        self.ensure_one()
        integration = self.company_id.sendcloud_default_integration_id
        if integration:
            parcel = integration.get_parcel(self.sendcloud_code)
            parcels_vals = self.env[
                "sendcloud.parcel"
            ]._prepare_sendcloud_parcel_from_response(parcel)
            self.write(parcels_vals)

    def unlink(self):
        if not self.env.context.get("skip_cancel_parcel"):
            for parcel in self:
                integration = parcel.company_id.sendcloud_default_integration_id
                if integration:
                    res = integration.cancel_parcel(parcel.sendcloud_code)
                    if res.get("error"):
                        if res["error"]["code"] == 404:
                            continue  # ignore "Not Found" error
                        raise UserError(
                            _("Sendcloud: %s") % res["error"].get("message")
                        )
        return super().unlink()

    def action_create_return_parcel(self):
        self.ensure_one()
        [action] = self.env.ref(
            "delivery_sendcloud_oca.action_sendcloud_create_return_parcel_wizard"
        ).read()
        action["context"] = (
            f'{{"default_brand_id": "{self.brand_id.id}", '
            f'"default_parcel_id": "{self.id}"}}'
        )
        return action

    @api.model
    def _prepare_sendcloud_parcel_item_from_response(self, data):
        return {
            "description": data.get("description"),
            "quantity": data.get("quantity"),
            "weight": data.get("weight"),
            "value": data.get("value"),
            "hs_code": data.get("hs_code"),
            "origin_country": data.get("origin_country"),
            "product_id": data.get("product_id"),
            "properties": data.get("properties"),
            "sku": data.get("sku"),
            "return_reason": data.get("return_reason"),
            "return_message": data.get("return_message"),
        }


class SendcloudParcelDocument(models.Model):
    _name = "sendcloud.parcel.document"
    _description = "Sendcloud Parcel Document"

    name = fields.Char(required=True)
    size = fields.Char()
    link = fields.Char()
    parcel_id = fields.Many2one("sendcloud.parcel")
    attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        ondelete="cascade",
    )
    attachment = fields.Binary(related="attachment_id.datas", string="File Content")

    def action_get_parcel_document(self):
        self.ensure_one()
        if not self.link:
            raise UserError(_("Document not available: no link provided."))
        self._generate_parcel_document()

    def _generate_parcel_document(self):
        for document in self.filtered(lambda p: p.link):
            integration = document.parcel_id.company_id.sendcloud_default_integration_id
            content = integration.get_parcel_document(document.link)
            filename = document.generate_parcel_document_filename()
            attachment_id = self.env["ir.attachment"].create(
                {
                    "name": filename,
                    "res_id": document.id,
                    "res_model": document._name,
                    "datas": base64.b64encode(content),
                    "description": document.name,
                }
            )
            document.attachment_id = attachment_id

    def generate_parcel_document_filename(self):
        self.ensure_one()
        if not self.name.lower().endswith(".pdf"):
            return self.name + ".pdf"
        return self.name
