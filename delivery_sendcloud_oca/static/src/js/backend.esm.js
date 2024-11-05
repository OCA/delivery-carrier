/** @odoo-module **/
/* global sendcloud */
import {Component, onWillStart} from "@odoo/owl";
import {_lt} from "@web/core/l10n/translation";
import {loadJS} from "@web/core/assets";
import {registry} from "@web/core/registry";
import {standardFieldProps} from "@web/views/fields/standard_field_props";
import {useInputField} from "@web/views/fields/input_field_hook";
import {useService} from "@web/core/utils/hooks";
import {WarningDialog} from "@web/core/errors/error_dialogs";

export class ServicePointSelectorField extends Component {
    setup() {
        useInputField({getValue: () => this.props.value || ""});
        this.dialog = useService("dialog");
        onWillStart(() =>
            loadJS("/delivery_sendcloud_oca/static/src/lib/sendcloud/api.min.js")
        );
    }

    async onClearClick() {
        this.props.update("");
    }

    async _onServicePointError(errors) {
        var irrelevantErrors = ["Closed"];
        var relevantErrors = _.difference(errors, irrelevantErrors);

        if (relevantErrors.length) {
            this.dialog.add(WarningDialog, {
                title: this.env._t("Failure in opening Service Point Selector"),
                message: relevantErrors.join("\n"),
            });
        }
    }

    async _onServicePointSelected(servicePoint) {
        this.props.update(JSON.stringify(servicePoint));
    }

    async onInputClick() {
        var value = this.props.record.data.sendcloud_sp_details;
        if (!value) {
            return "";
        }

        var parsedValue = JSON.parse(value);
        sendcloud.servicePoints.open(
            {
                apiKey: parsedValue.api_key,
                country: parsedValue.country,
                postalCode: parsedValue.postalcode,
                language: parsedValue.language,
                carriers: [parsedValue.carrier],
            },
            this._onServicePointSelected.bind(this),
            this._onServicePointError.bind(this)
        );
    }

    get sp_name() {
        try {
            return JSON.parse(this.props.value).name;
        } catch {
            return "";
        }
    }

    get street() {
        try {
            return JSON.parse(this.props.value).street;
        } catch {
            return "";
        }
    }

    get house_number() {
        try {
            return JSON.parse(this.props.value).house_number;
        } catch {
            return "";
        }
    }

    get postal_code() {
        try {
            return JSON.parse(this.props.value).postal_code;
        } catch {
            return "";
        }
    }

    get city() {
        try {
            return JSON.parse(this.props.value).city;
        } catch {
            return "";
        }
    }
}
ServicePointSelectorField.template = "delivery_sendcloud_oca.ServicePointField";
ServicePointSelectorField.props = standardFieldProps;
export const servicePointSelectorField = {
    component: ServicePointSelectorField,
    supportedTypes: ["text"],
    displayName: _lt("Service Point Selector"),
};

registry
    .category("fields")
    .add("sendcloud_service_point_selector", servicePointSelectorField);
