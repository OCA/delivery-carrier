import {ListRenderer} from "@web/views/list/list_renderer";
import {SendcloudOnboarding} from "@delivery_sendcloud_oca/components/onboarding/onboarding.esm";
import {listView} from "@web/views/list/list_view";
import {registry} from "@web/core/registry";

export class SendcloudListRenderer extends ListRenderer {
    static template = "delivery_sendcloud_oca.SendcloudListRenderer";
    static components = {
        ...ListRenderer.components,
        SendcloudOnboarding,
    };
}

registry.category("views").add("sendcloud_list", {
    ...listView,
    Renderer: SendcloudListRenderer,
});
